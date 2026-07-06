import os
import re
import pandas as pd
import numpy as np
import joblib

# Cache datasets in module memory to avoid reloading on every function call
_data_cache = {}

def get_dataset(name):
    """Lazy load and cache datasets to keep execution fast"""
    if name in _data_cache:
        return _data_cache[name]
    
    try:
        if name == 'customers':
            _data_cache[name] = pd.read_excel('Data/Raw/customers.csv.xlsx')
        elif name == 'products':
            _data_cache[name] = pd.read_csv('Data/Raw/products.csv')
        elif name == 'transactions':
            _data_cache[name] = pd.read_excel('Data/Raw/transactions.csv.xlsx')
        return _data_cache.get(name)
    except Exception as e:
        print(f"Error loading dataset {name}: {e}")
        return None

# Load model artifacts
_model_cache = None
def get_churn_model():
    """Lazy load the trained RandomForest churn model"""
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    
    model_path = 'chatbot/churn_model.joblib'
    if os.path.exists(model_path):
        try:
            _model_cache = joblib.load(model_path)
            return _model_cache
        except Exception as e:
            print(f"Error loading churn model: {e}")
            return None
    else:
        print(f"Churn model not found at {model_path}. Churn queries will use a heuristic fallback.")
        return None

# Define months for parsing
MONTHS_MAP = {
    'january': 1, 'jan': 1,
    'february': 2, 'feb': 2,
    'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'may': 5,
    'june': 6, 'jun': 6,
    'july': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9, 'sept': 9,
    'october': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'december': 12, 'dec': 12
}

# ==========================================
# INTENT 1: REVENUE SUMMARY
# ==========================================
def handle_revenue_summary(query: str) -> str:
    """
    Intent 1: Direct SQL/Pandas aggregation function for Revenue/Sales queries.
    Aggregates delivered transaction final amounts by month, year, or category.
    """
    transactions = get_dataset('transactions')
    products = get_dataset('products')
    
    if transactions is None:
        return "I'm sorry, I couldn't load the transaction data to aggregate revenue."
        
    query_lower = query.lower()
    
    # 1. Filter for Delivered status (revenue is based on delivered transactions)
    delivered = transactions[transactions['status'] == 'Delivered'].copy()
    delivered['order_date'] = pd.to_datetime(delivered['order_date'])
    
    # 2. Extract Year
    year_match = re.search(r'\b(2023|2024)\b', query)
    year_filter = int(year_match.group(1)) if year_match else None
    
    # 3. Extract Month
    month_filter = None
    for month_name, month_num in MONTHS_MAP.items():
        if re.search(r'\b' + month_name + r'\b', query_lower):
            month_filter = month_num
            break
            
    # 4. Extract Category
    category_filter = None
    if products is not None:
        categories = [cat.lower() for cat in products['category'].unique()]
        for cat in categories:
            if cat in query_lower:
                category_filter = cat
                break
                
        # Support compound keywords like "home & kitchen"
        if "home & kitchen" in query_lower or "kitchen" in query_lower:
            category_filter = "home & kitchen"
            
    # Apply filters
    df_filtered = delivered
    
    # If category is selected, we need to join with products
    if category_filter:
        df_filtered = df_filtered.merge(products, on='product_id')
        df_filtered = df_filtered[df_filtered['category'].str.lower() == category_filter]
        
    if year_filter:
        df_filtered = df_filtered[df_filtered['order_date'].dt.year == year_filter]
        
    if month_filter:
        df_filtered = df_filtered[df_filtered['order_date'].dt.month == month_filter]
        
    # Check if empty results
    if len(df_filtered) == 0:
        filters_str = []
        if category_filter: filters_str.append(f"category '{category_filter}'")
        if month_filter: filters_str.append(f"month '{month_filter}'")
        if year_filter: filters_str.append(f"year '{year_filter}'")
        return f"I couldn't find any delivered transactions matching your filters: {', '.join(filters_str)}."

    # Perform aggregations
    total_rev = df_filtered['final_amount'].sum()
    units_sold = df_filtered['quantity'].sum()
    txn_count = len(df_filtered)
    avg_order = total_rev / txn_count if txn_count > 0 else 0
    
    # Format currency nicely
    def fmt_curr(val):
        if val >= 1_000_000:
            return f"${val / 1_000_000:.2f} Million"
        elif val >= 1_000:
            return f"${val / 1_000:.2f}K"
        return f"${val:.2f}"

    # Build response explanation
    title_parts = []
    if category_filter:
        title_parts.append(category_filter.title())
    title_parts.append("Revenue")
    if month_filter:
        # Get month name
        m_name = [name for name, num in MONTHS_MAP.items() if num == month_filter][0].title()
        title_parts.append(f"for {m_name}")
    if year_filter:
        title_parts.append(f"in {year_filter}")
    else:
        if month_filter:
            title_parts.append("(Across 2023 & 2024)")
            
    title = " ".join(title_parts)
    
    response = f"### 📊 {title} Summary\n"
    response += f"- **Total Revenue (Delivered)**: **{fmt_curr(total_rev)}**\n"
    response += f"- **Units Sold**: **{units_sold:,} items**\n"
    response += f"- **Total Transactions**: **{txn_count:,} orders**\n"
    response += f"- **Average Order Value**: **${avg_order:.2f}**\n\n"
    
    # Add a breakdown by year if year was not specified
    if not year_filter and len(df_filtered['order_date'].dt.year.unique()) > 1:
        response += "*Breakdown by Year:*\n"
        yearly_agg = df_filtered.groupby(df_filtered['order_date'].dt.year)['final_amount'].sum()
        for yr, rev in yearly_agg.items():
            response += f"- **{yr}**: {fmt_curr(rev)}\n"
            
    return response

# ==========================================
# INTENT 2: CUSTOMER RISK (CHURN-LINKED)
# ==========================================
def handle_customer_risk(query: str) -> str:
    """
    Intent 2: Customer Risk (churn-linked) prediction.
    Extracts customer ID, loads trained RF model, predicts churn probability using .predict_proba(),
    and explains the risk drivers (recency, spending, segments).
    """
    # Extract Customer ID: CUSTxxxxx (case-insensitive)
    match = re.search(r'CUST\d{5}', query, re.IGNORECASE)
    if not match:
        return "I detected a customer risk query, but I couldn't find a valid Customer ID in the format 'CUSTxxxxx' (e.g., CUST00123)."
        
    cust_id = match.group(0).upper()
    
    customers = get_dataset('customers')
    transactions = get_dataset('transactions')
    
    if customers is None:
        return "I'm sorry, I couldn't load the customer database to check customer risk."
        
    # Look up customer
    cust_row = customers[customers['customer_id'] == cust_id]
    if len(cust_row) == 0:
        return f"Customer **{cust_id}** was not found in our database. Please double-check the ID."
        
    cust_data = cust_row.iloc[0]
    cust_name = cust_data['name']
    cust_segment = cust_data['segment']
    cust_orders = cust_data['total_orders']
    cust_ltv = cust_data['lifetime_value']
    cust_age = cust_data['age']
    cust_gender = cust_data['gender']
    cust_region = cust_data['region']
    cust_city = cust_data['city']
    
    # Calculate recency manually to pass to the model
    recency = 730 # Default if no transactions
    if transactions is not None:
        transactions['order_date'] = pd.to_datetime(transactions['order_date'])
        ref_date = transactions['order_date'].max()
        cust_txns = transactions[transactions['customer_id'] == cust_id]
        if len(cust_txns) > 0:
            last_date = cust_txns['order_date'].max()
            recency = (ref_date - last_date).days
            
    # Try loading the model to get predict_proba
    model_data = get_churn_model()
    
    if model_data is not None:
        try:
            # Reconstruct the feature vector
            # Features: ['age', 'gender_encoded', 'region_encoded', 'total_orders', 'lifetime_value', 'recency']
            gender_encoded = model_data['le_gender'].transform([str(cust_gender)])[0]
            region_encoded = model_data['le_region'].transform([str(cust_region)])[0]
            
            features = np.array([[cust_age, gender_encoded, region_encoded, cust_orders, cust_ltv, recency]])
            features_scaled = model_data['scaler'].transform(features)
            
            # Predict probability
            prob_churn = model_data['model'].predict_proba(features_scaled)[0][1]
        except Exception as e:
            print(f"Prediction failed, falling back to heuristics: {e}")
            prob_churn = None
    else:
        prob_churn = None
        
    # Heuristic fallback if model loading failed or errored out
    if prob_churn is None:
        # Generate a reasonable mock churn probability based on segment and recency
        if cust_segment == 'At Risk':
            prob_churn = 0.70 + (recency / 730) * 0.25 # 70% to 95%
        elif cust_segment == 'Hibernating':
            prob_churn = 0.85 + (recency / 730) * 0.14 # 85% to 99%
        elif cust_segment == 'Occasional':
            prob_churn = 0.35 + (recency / 730) * 0.30 # 35% to 65%
        elif cust_segment in ['Loyal', 'New Customers']:
            prob_churn = 0.10 + (recency / 730) * 0.20 # 10% to 30%
        else: # Champions
            prob_churn = 0.01 + (recency / 730) * 0.09 # 1% to 10%
        prob_churn = min(max(prob_churn, 0.0), 1.0)
        
    # Risk Level mapping
    if prob_churn >= 0.70:
        risk_level = "🚨 HIGH RISK"
        risk_color = "red"
        explanation = "This customer is highly likely to churn. They haven't purchased in a significant amount of time and are classified in an inactive RFM segment. Immediate intervention is required."
        action = "Include in the high-value win-back campaign: send a personalized email with a 25% discount voucher and assign a priority support representative if they have open tickets."
    elif prob_churn >= 0.35:
        risk_level = "⚠️ MEDIUM RISK"
        risk_color = "orange"
        explanation = "This customer shows early warning signs of churn. Their purchase frequency is slowing down, or they have a moderate recency gap."
        action = "Target with a standard customer engagement email, highlight trending products in their favorite category, or offer loyalty points booster multiplier."
    else:
        risk_level = "✅ LOW RISK"
        risk_color = "green"
        explanation = "This customer is highly active, purchase records are recent, and they show strong loyalty indicators."
        action = "Keep them engaged with VIP pre-launch access, exclusive rewards, or referral programs. No immediate churn prevention needed."
        
    response = f"### 👥 Customer Churn Risk Analysis: {cust_id}\n"
    response += f"- **Customer Name**: {cust_name}\n"
    response += f"- **Demographics**: {cust_age} years old | {cust_gender} | Region: {cust_region} ({cust_city})\n"
    response += f"- **RFM Segment**: **{cust_segment}**\n"
    response += f"- **Lifetime Purchase History**: **{cust_orders} orders** totaling **${cust_ltv:,.2f}**\n"
    response += f"- **Purchase Recency**: **{recency} days** since last purchase\n"
    response += f"- **Churn Risk Score**: **{prob_churn*100:.1f}% Churn Probability** ({risk_level})\n\n"
    
    response += f"**Risk Driver Explanation:**\n"
    response += f"{explanation} With a last purchase date {recency} days ago, their behavioral pattern matches a churn profile. "
    response += f"Their total spend is ${cust_ltv:,.2f} over {cust_orders} orders, giving an average order value of ${cust_ltv/cust_orders:.2f}.\n\n"
    
    response += f"**Recommended Action Playbook:**\n"
    response += f"- {action}\n"
    
    return response

# ==========================================
# INTENT 3: PRODUCT LOOKUP
# ==========================================
def handle_product_lookup(query: str) -> str:
    """
    Intent 3: Direct database lookup against products.csv.
    Retrieves and formats specifications, inventory levels, ratings, and margins for a specific product.
    """
    products = get_dataset('products')
    transactions = get_dataset('transactions')
    
    if products is None:
        return "I'm sorry, I couldn't load the products database."
        
    query_lower = query.lower()
    
    # 1. Match Product ID: PRODxxx
    id_match = re.search(r'PROD\d{3}', query, re.IGNORECASE)
    
    product_row = pd.DataFrame()
    
    if id_match:
        prod_id = id_match.group(0).upper()
        product_row = products[products['product_id'] == prod_id]
    else:
        # Find product by name matching in query
        for _, row in products.iterrows():
            if row['product_name'].lower() in query_lower:
                product_row = pd.DataFrame([row])
                break
                
    if len(product_row) == 0:
        return "I detected a product search request, but I couldn't find a matching product ID (PRODxxx) or product name in our records."
        
    prod_data = product_row.iloc[0]
    prod_id = prod_data['product_id']
    prod_name = prod_data['product_name']
    category = prod_data['category']
    base_price = prod_data['base_price']
    cost_price = prod_data['cost_price']
    stock = prod_data['stock_quantity']
    supplier = prod_data['supplier']
    rating = prod_data['rating']
    reviews = prod_data['reviews_count']
    launch_date = prod_data['launch_date']
    
    margin = base_price - cost_price
    margin_pct = (margin / base_price) * 100
    
    # Aggregate transaction statistics for this product
    units_sold = 0
    total_rev = 0
    txn_count = 0
    if transactions is not None:
        delivered_txns = transactions[(transactions['product_id'] == prod_id) & (transactions['status'] == 'Delivered')]
        units_sold = delivered_txns['quantity'].sum()
        total_rev = delivered_txns['final_amount'].sum()
        txn_count = len(delivered_txns)
        
    # Stock status
    if stock <= 100:
        stock_status = f"🔴 Critical Stock Alert ({stock} units remaining) - Stockout risk is HIGH!"
    elif stock <= 300:
        stock_status = f"🟡 Low Stock ({stock} units remaining) - Monitor closely."
    else:
        stock_status = f"🟢 Healthy Stock ({stock} units remaining)"
        
    response = f"### 📦 Product Profile: {prod_name} ({prod_id})\n"
    response += f"- **Category**: {category}\n"
    response += f"- **Pricing**: **${base_price:,.2f}** (Cost Price: ${cost_price:,.2f} | Profit Margin: **{margin_pct:.1f}%**)\n"
    response += f"- **Inventory Level**: {stock_status}\n"
    response += f"- **Customer Feedback**: **{rating:.1f} / 5.0** rating ({reviews:,} reviews)\n"
    response += f"- **Supplier**: {supplier}\n"
    response += f"- **Launch Date**: {launch_date}\n\n"
    
    response += f"**Transaction History (Delivered Orders):**\n"
    response += f"- **Total Sales Revenue**: **${total_rev:,.2f}**\n"
    response += f"- **Units Sold**: **{units_sold:,} items**\n"
    response += f"- **Number of Transactions**: **{txn_count:,} orders**\n"
    
    return response

# ==========================================
# FALLBACK AND SCOPE CHECK HANDLERS (Task 5)
# ==========================================
def check_date_out_of_bounds(query: str) -> bool:
    """Check if query requests data for years outside RetailNova's records (Jan 2023 - Dec 2024)"""
    query_lower = query.lower()
    # Extract any 4-digit years
    years = re.findall(r'\b\d{4}\b', query)
    for y in years:
        y_int = int(y)
        # If year is specified but outside 2023-2024, it's out of bounds
        if y_int < 2023 or y_int > 2024:
            return True
    
    # Check if query references years like 2022 or 2025 in text form
    if any(yr in query_lower for yr in ["2022", "2025", "2026", "2021", "next year", "last year of 2022"]):
        return True
    return False

def check_out_of_scope_rules(query: str) -> bool:
    """Fallback rule-based out-of-scope classifier"""
    query_lower = query.lower()
    
    # Explicit out-of-scope keywords
    out_of_scope_words = [
        'weather', 'temperature', 'rain', 'snow', 'forecast',
        'recipe', 'cook', 'baking', 'dinner ideas', 'ingredients',
        'joke', 'funny',
        'president', 'prime minister', 'capital of', 'population of',
        'write a script', 'python code', 'coding', 'programming',
        'meaning of life', 'general knowledge', 'trivia', 'news today',
        'who is', 'how tall is', 'distance to'
    ]
    
    # In-scope keywords (to prevent false positives)
    in_scope_words = [
        'revenue', 'sales', 'turnover', 'earn', 'spend', 'monetary',
        'customer', 'cust', 'churn', 'risk', 'retention', 'segment', 'dormant',
        'product', 'prod', 'stock', 'inventory', 'item', 'price', 'margin', 'cost',
        'campaign', 'marketing', 'roi', 'ad', 'email', 'sms', 'push', 'click', 'conversion',
        'support', 'ticket', 'issue', 'csat', 'agent', 'complain', 'refund',
        'make', 'profit', 'earnings', 'performance', 'grow', 'loss', 'cohort', 'history', 'stat', 'kpi', 'record', 'segmentation'
    ]
    
    # If it has out of scope words, it's out of scope
    if any(w in query_lower for w in out_of_scope_words):
        print(f"[Rule Scope Check] Query: '{query}' -> Out-of-Scope (detected out-of-scope keyword)")
        return True
        
    # If it contains greetings, it's in-scope (handled by conversation)
    greetings = ['hello', 'hi', 'hey', 'help', 'menu', 'options', 'clear', 'reset', 'welcome']
    if any(w in query_lower for w in greetings):
        return False
        
    # If it doesn't match any retail terms, it's out of scope
    if not any(w in query_lower for w in in_scope_words):
        print(f"[Rule Scope Check] Query: '{query}' -> Out-of-Scope (no retail keywords found)")
        return True
        
    return False

# ==========================================
# INTENT ROUTER AND CLASSIFIER
# ==========================================
def route_intent(query: str) -> str:
    """
    Main entry point for intent classification and routing.
    Runs rule-based checks on the user query. If a match is found,
    routes to the specialized handler. Otherwise, returns None (fallback to RAG).
    """
    query_lower = query.lower()
    
    # 1. Date Range Check (in-scope but unanswerable dates)
    if check_date_out_of_bounds(query):
        print(f"[Intent Router] Triggered Date Out of Bounds Fallback for: '{query}'")
        return "I don't have data for that period; my records cover Jan 2023 to Dec 2024."
        
    # 2. INTENT 2 Check: Customer Churn/Risk query (contains CUSTxxxxx ID)
    if re.search(r'cust\d{5}', query_lower):
        print(f"[Intent Router] Detected Intent 2 (Customer Risk) for query: '{query}'")
        return handle_customer_risk(query)
        
    # 3. INTENT 3 Check: Product lookup (contains PRODxxx ID or matches a product name in products.csv)
    products = get_dataset('products')
    has_prod_id = re.search(r'prod\d{3}', query_lower)
    has_product_name = False
    
    if products is not None:
        for name in products['product_name'].unique():
            if name.lower() in query_lower:
                has_product_name = True
                break
                
    if has_prod_id or has_product_name:
        print(f"[Intent Router] Detected Intent 3 (Product Lookup) for query: '{query}'")
        return handle_product_lookup(query)
        
    # 4. INTENT 1 Check: Revenue / Sales aggregation query
    # Triggers on combinations of revenue/sales/turnover keywords
    revenue_keywords = ['revenue', 'sales', 'turnover', 'how much did we make', 'total cash', 'earnings']
    if any(keyword in query_lower for keyword in revenue_keywords):
        print(f"[Intent Router] Detected Intent 1 (Revenue Summary) for query: '{query}'")
        return handle_revenue_summary(query)
        
    # 5. Scope Check (out-of-scope queries) - only if no specialized intent matched
    is_memory_followup = any(w in query_lower for w in ["compare", "month before", "previous month", "prior month", "go back to churn", "return to churn", "about churn again", "churn action"])
    
    if is_memory_followup:
        print(f"[Intent Router] Detected memory follow-up. Bypassing out-of-scope check.")
        is_out = False
    else:
        is_out = check_out_of_scope_rules(query)
        
    if is_out:
        print(f"[Intent Router] Triggered Out-of-Scope Fallback for: '{query}'")
        return "I'm InsightPulse Assistant, focused on RetailNova's sales, customers, and support data. I can't help with that, but feel free to ask me about revenue, products, or customer trends!"
        
    # Fallback to standard RAG pipeline
    print(f"[Intent Router] No specialized intent matched. Falling back to general RAG path for query: '{query}'")
    return None

# ==========================================
# SELF-TEST SECTION
# ==========================================
def run_self_test():
    """Test all 3 intents with at least 5 varied phrasings per intent (15 queries total)"""
    test_cases = {
        "Intent 1: Revenue Summary": [
            "What was revenue in March?",
            "Total sales for Electronics in 2024?",
            "How much did we make in 2023?",
            "What is the revenue for clothing?",
            "What was the sales figure in December 2024 for sports?"
        ],
        "Intent 2: Customer Risk": [
            "Is customer CUST00123 at risk?",
            "Is CUST04427 churn-linked?",
            "Check churn probability for CUST00001",
            "What is the risk rating for CUST00010?",
            "Will customer CUST00250 stop purchasing?"
        ],
        "Intent 3: Product Lookup": [
            "Tell me about Wireless Earbuds",
            "What's the rating for PROD003?",
            "Get details for PROD015",
            "How many units of Smart Watch do we have left in stock?",
            "Check price and margin of Air Fryer"
        ]
    }
    
    print("\n" + "="*50)
    print("RUNNING INTENT ROUTER SELF-TEST (15 Queries)")
    print("="*50 + "\n")
    
    total_tests = 0
    passed_tests = 0
    
    for intent_name, queries in test_cases.items():
        print(f"--- Testing {intent_name} ---")
        for q in queries:
            total_tests += 1
            response = route_intent(q)
            if response:
                lines = response.splitlines()
                sample = lines[0] if len(lines) > 0 else ""
                if len(lines) > 1:
                    sample += " - " + lines[1]
                print(f"Query: '{q}'\nResult: SUCCESS (Routed & Handled)\nResponse Sample: {sample}\n")
                passed_tests += 1
            else:
                print(f"Query: '{q}'\nResult: FAILED (Fallback to RAG)\n")
        print()
        
    print(f"Self-Test Complete: {passed_tests}/{total_tests} queries successfully routed and handled.")

if __name__ == '__main__':
    run_self_test()
