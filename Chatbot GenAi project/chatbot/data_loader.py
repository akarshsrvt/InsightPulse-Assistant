import os
import pandas as pd
import joblib

# Simple in-memory cache to share datasets across modules/calls
_data_cache = {}
_model_cache = None

def get_dataset(name: str):
    """Lazy load and cache datasets to keep execution fast and modular"""
    if name in _data_cache:
        return _data_cache[name]
    
    # Resolve project base directory dynamically
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Map name to file paths
    paths = {
        'customers': os.path.join(base_dir, 'Data', 'Raw', 'customers.csv.xlsx'),
        'products': os.path.join(base_dir, 'Data', 'Raw', 'products.csv'),
        'transactions': os.path.join(base_dir, 'Data', 'Raw', 'transactions.csv.xlsx'),
        'support': os.path.join(base_dir, 'Data', 'Raw', 'customer_support.csv.xlsx'),
        'campaigns': os.path.join(base_dir, 'Data', 'Raw', 'marketing_campaigns.csv.xlsx')
    }
    
    path = paths.get(name)
    if not path or not os.path.exists(path):
        print(f"Dataset path for '{name}' not found or doesn't exist: {path}")
        return None
        
    try:
        if path.endswith('.xlsx'):
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)
        _data_cache[name] = df
        return df
    except Exception as e:
        print(f"Error loading dataset {name} from {path}: {e}")
        return None

def load_all_datasets():
    """Load and aggregate all RetailNova business datasets"""
    customers = get_dataset('customers')
    products = get_dataset('products')
    transactions = get_dataset('transactions')
    support = get_dataset('support')
    campaigns = get_dataset('campaigns')
    
    delivered = None
    if transactions is not None:
        delivered = transactions[transactions['status'] == 'Delivered'].copy()
        
    return customers, products, transactions, support, campaigns, delivered

def get_churn_model():
    """Lazy load the trained RandomForest churn model"""
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    
    # Resolve project base directory dynamically
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, 'chatbot', 'churn_model.joblib')
    
    if os.path.exists(model_path):
        try:
            _model_cache = joblib.load(model_path)
            return _model_cache
        except Exception as e:
            print(f"Error loading churn model from {model_path}: {e}")
    else:
        print(f"Churn model not found at {model_path}. Churn queries will use a heuristic fallback.")
        
    return None

def compute_kb_context(products, campaigns, support, delivered):
    """Compute the static knowledge base context for RAG"""
    if products is None or campaigns is None or support is None or delivered is None:
        return "No datasets loaded."
        
    try:
        # 1. Product stats
        p_delivered = delivered.merge(products, on='product_id')
        p_delivered['cost'] = p_delivered['quantity'] * p_delivered['cost_price']
        p_summary = p_delivered.groupby(['product_id', 'product_name', 'category', 'stock_quantity']).agg(
            units_sold=('quantity', 'sum'),
            revenue=('final_amount', 'sum'),
            cost=('cost', 'sum')
        ).reset_index()
        p_summary['profit'] = p_summary['revenue'] - p_summary['cost']
        p_summary['margin_pct'] = (p_summary['profit'] / p_summary['revenue']) * 100
        
        # 2. Campaign stats
        campaigns = campaigns.copy()
        campaigns['roi_pct'] = (campaigns['revenue_generated'] - campaigns['budget_inr']) / campaigns['budget_inr'] * 100
        
        # 3. Support stats
        avg_csat = support['csat_score'].mean()
        
        # Assemble general KB context
        kb_context = f"""
RetailNova General Business KPIs (Jan 2023 - Dec 2024):
- Total Customers: 4,961 active customers
- Total Revenue: $58.48 Million (Delivered transactions)
- Average Customer Spend: $11,787.92
- Overall Month-1 Retention: 89.33% (Active signup cohort)
- Overall Month-3 Retention: 88.77%
- Average Customer Support CSAT Score: {avg_csat:.2f}/5.0

Top Products by Revenue:
1. Water Purifier (PROD015) - Revenue: $10.42M, Profit: $3.30M, Margin: 31.6%, Stock: 916 units
2. Smart Watch (PROD002) - Revenue: $5.55M, Profit: $1.69M, Margin: 30.4%, Stock: 618 units
3. Air Fryer (PROD011) - Revenue: $4.44M, Profit: $1.72M, Margin: 38.7%, Stock: 220 units

Bottom Products by Revenue:
1. Lip Balm Pack (PROD030) - Revenue: $272K, Profit: $131K, Margin: 48.0%, Stock: 676 units
2. Skipping Rope (PROD024) - Revenue: $345K, Profit: $109K, Margin: 31.5%, Stock: 885 units

Stockout Risk Flags:
- Puzzle Set (PROD034): Stock quantity is only 71 units left in inventory, but 1,223 units have been sold! High stockout risk.

Marketing Campaign ROI Performance:
- SMS Campaigns: Budget: 24.7M INR, Revenue: 675.3M INR, ROI: 2,624% (SMS Leads - SMS)
- Display Ads: Budget: 24.0M INR, Revenue: 629.1M INR, ROI: 2,522% (Mega Sale - Display Ad)
- Email Marketing: Budget: 23.1M INR, Revenue: 555.6M INR, ROI: 2,301% (Festive Season - Email)
- Push Notifications: Budget: 26.1M INR, Revenue: 484.7M INR, ROI: 1,757% (Loyalty Rewards - Push)

Customer RFM Segments:
- Champions (24.63% of base): 1,222 customers, $25.67M sales (43.89% revenue share). Recency: very high, Frequency: very high, Monetary: very high.
- Loyal (30.76% of base): 1,526 customers, $19.69M sales (33.67% revenue share). High frequency, good spenders.
- New Customers (19.43% of base): 964 customers, $7.58M sales (12.96% revenue share). 
- At Risk (6.31% of base): 313 customers, $2.35M sales (4.01% revenue share). High frequency but stopped purchasing recently. Needs win-back.
- Hibernating (18.87% of base): 936 customers, $3.20M sales (5.47% revenue share). Low spenders and inactive.
"""
        return kb_context
    except Exception as e:
        print(f"Error computing KB context: {e}")
        return "Error computing KB context."
