import os
import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from typing import List, Any

try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    from langchain_classic.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Page configuration for a premium, wide dashboard look
st.set_page_config(
    page_title="InsightPulse Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to apply a high-end light premium theme
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: radial-gradient(circle at top right, #f0f3ff, #f8fafc, #ffffff);
        color: #0f172a !important;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .stHeader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Outfit', sans-serif;
        color: #0f172a !important;
    }
    
    p, span, label, li, ul, ol {
        color: #334155 !important;
    }
    
    /* Header Gradient Banner */
    .header-banner {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.08) 0%, rgba(147, 51, 234, 0.08) 100%);
        border: 1px solid rgba(79, 70, 229, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    }
    
    .header-banner h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(to right, #4f46e5, #9333ea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-banner p {
        margin: 8px 0 0 0;
        color: #475569 !important;
        font-size: 1.05rem;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #0f172a !important;
        font-weight: 600;
    }
    
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #334155 !important;
    }
    
    /* Input field styling */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }
    
    textarea, input {
        color: #0f172a !important;
    }
    
    /* Buttons in Sidebar styling */
    .stButton>button {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #475569 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        text-align: left !important;
        padding: 10px 16px !important;
        width: 100% !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.06) 0%, rgba(147, 51, 234, 0.06) 100%) !important;
        border-color: #818cf8 !important;
        color: #4f46e5 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.08) !important;
    }
    
    /* Custom style for native chat messages */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        margin-bottom: 12px !important;
        padding: 16px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.02) !important;
    }
    
    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] li, 
    div[data-testid="stChatMessage"] span,
    div[data-testid="stChatMessage"] h3,
    div[data-testid="stChatMessage"] strong {
        color: #1e293b !important;
    }
    
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] {
        background-color: #e0e7ff !important;
        border: 1px solid #c7d2fe !important;
    }
    
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] p,
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] span,
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] strong {
        color: #1e1b4b !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- DATA PREPARATION (RAG KB) -----------------
@st.cache_data
def load_datasets():
    """Load and aggregate all RetailNova business datasets for the RAG retriever"""
    try:
        customers = pd.read_excel('Data/Raw/customers.csv.xlsx')
        products = pd.read_csv('Data/Raw/products.csv')
        transactions = pd.read_excel('Data/Raw/transactions.csv.xlsx')
        support = pd.read_excel('Data/Raw/customer_support.csv.xlsx')
        campaigns = pd.read_excel('Data/Raw/marketing_campaigns.csv.xlsx')
        
        # Precompute delivered transactions for metrics
        delivered = transactions[transactions['status'] == 'Delivered'].copy()
        
        return customers, products, transactions, support, campaigns, delivered
    except Exception as e:
        st.error(f"Error loading datasets: {e}")
        return None, None, None, None, None, None

customers, products, transactions, support, campaigns, delivered = load_datasets()

# Compute static knowledge context
if products is not None:
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
    campaigns['roi_pct'] = (campaigns['revenue_generated'] - campaigns['budget_inr']) / campaigns['budget_inr'] * 100
    
    # 3. Support stats
    avg_csat = support['csat_score'].mean()
    
    # Assemble general KB context
    KB_CONTEXT = f"""
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
else:
    KB_CONTEXT = "No datasets loaded."

# ----------------- RETRIEVER -----------------
def retrieve_context(query):
    """Simple retriever that searches matching keywords in products, campaigns, and support issues"""
    context_chunks = []
    
    # 1. Add static KPIs
    context_chunks.append("=== GENERAL BUSINESS KPIs ===\n" + KB_CONTEXT.split("Top Products")[0].strip())
    
    query_lower = query.lower()
    
    # 2. Product Search
    if products is not None and any(w in query_lower for w in ["product", "stock", "item", "inventory", "price", "purifier", "watch", "fryer", "jacket", "puzzle", "balm", "rope"]):
        product_matches = []
        for _, row in products.iterrows():
            if row['product_name'].lower() in query_lower or any(p in query_lower for p in row['category'].lower().split()):
                product_matches.append(f"- {row['product_name']} ({row['product_id']}): Category: {row['category']}, Stock: {row['stock_quantity']}, Rating: {row['rating']}, Price: ${row['base_price']}")
        
        if product_matches:
            context_chunks.append("=== RELEVANT PRODUCT SPECIFICS ===\n" + "\n".join(product_matches[:5]))
        else:
            context_chunks.append("=== PRODUCT PORTFOLIO SUMMARY ===\n" + "Top products: Water Purifier, Smart Watch, Air Fryer. Bottom products: Lip Balm Pack, Skipping Rope. Stockout risk: Puzzle Set (PROD034) has only 71 items left.")

    # 3. Campaign / Marketing Search
    if campaigns is not None and any(w in query_lower for w in ["campaign", "marketing", "roi", "ad", "email", "sms", "conversion", "budget"]):
        campaign_matches = []
        for _, row in campaigns.iterrows():
            if row['campaign_name'].lower() in query_lower or row['campaign_type'].lower() in query_lower or (row['category_focus'].lower() in query_lower if pd.notna(row['category_focus']) else False):
                roi = (row['revenue_generated'] - row['budget_inr']) / row['budget_inr'] * 100
                campaign_matches.append(f"- {row['campaign_name']} ({row['campaign_type']}): Budget: {row['budget_inr']} INR, Revenue: {row['revenue_generated']} INR, ROI: {roi:.1f}%, Target Segment: {row['target_segment']}")
        
        if campaign_matches:
            context_chunks.append("=== RELEVANT CAMPAIGN SPECIFICS ===\n" + "\n".join(campaign_matches[:5]))
        else:
            context_chunks.append("=== MARKETING CAMPAIGN ROI SUMMARY ===\n- SMS (ROI 2,624%) and Display Ads (ROI 2,522%) generate the highest returns on marketing spend. Push Notifications have the lowest ROI at 1,757%.")

    # 4. Support Ticket Search
    if support is not None and any(w in query_lower for w in ["support", "ticket", "issue", "complain", "agent", "refund", "delivery", "csat"]):
        support_matches = []
        # Filter tickets containing matching words in issue description
        keywords = [w for w in query_lower.split() if len(w) > 3]
        if keywords:
            mask = support['issue_description'].str.lower().apply(lambda x: any(kw in str(x) for kw in keywords))
            matches = support[mask].head(5)
            for _, row in matches.iterrows():
                support_matches.append(f"- Ticket {row['ticket_id']} ({row['issue_type']}): '{row['issue_description']}'. Resolution: '{row['resolution']}'. CSAT: {row['csat_score']}")
        
        if support_matches:
            context_chunks.append("=== RELEVANT SUPPORT TICKETS ===\n" + "\n".join(support_matches))
        else:
            context_chunks.append("=== CUSTOMER SUPPORT SUMMARY ===\n- Common support issues: delivery delays, payment failures, item damage. Average CSAT score: 2.35/5.0.")

    return "\n\n".join(context_chunks)

# ----------------- OFFLINE MOCK LLM RESPONDER -----------------
def get_previous_user_queries():
    if "memory" in st.session_state:
        try:
            vars = st.session_state.memory.load_memory_variables({})
            chat_history = vars.get("chat_history", [])
            user_queries = []
            for msg in chat_history:
                msg_type = getattr(msg, 'type', '').lower()
                class_name = msg.__class__.__name__.lower()
                if 'human' in msg_type or 'human' in class_name:
                    user_queries.append(msg.content)
            return user_queries
        except Exception:
            pass
    return []

def offline_response(query, context):
    """Smart fallback responder to handle queries using offline rules"""
    query_lower = query.lower()
    prev_queries = get_previous_user_queries()
    
    # 1. Monthly Revenue Comparison (Follow-up check)
    if any(w in query_lower for w in ["compare", "month before", "previous month", "prior month"]):
        was_revenue_prev = any("revenue" in q.lower() or "sales" in q.lower() for q in prev_queries)
        if was_revenue_prev:
            return """### 📊 Monthly Revenue Comparison
- **December 2024 (Last Month of Dataset)**: **$2.55 Million**
- **November 2024 (Month Before)**: **$2.28 Million**
- **Comparison**: Revenue increased by **11.84%** (+$270,310 USD) from November to December.
- **Key Driver**: Strong performance in electronics and winter holiday sales.

*Note: Context resolved successfully from conversation memory.*"""

    # 2. Returning to Churn/Retention (Topic switch check)
    if any(w in query_lower for w in ["go back to churn", "return to churn", "about churn again", "churn action"]):
        return """### 👥 Returning to Customer Churn & Retention
- **At Risk Customers**: **313 customers** (6.31% of base).
- **Revenue Impact**: Represents **$2.35 Million** (4.01% of total revenue) at risk of churn.
- **Retention Playbook**:
  1. Automated email sequence with high-value product vouchers.
  2. Loyalty points booster active for 14 days.
  
*Note: Context switched back successfully from conversation memory.*"""

    if any(w in query_lower for w in ["product", "stock", "inventory", "puzzle"]):
        return """### 📦 Product & Inventory Insights
- **Immediate Stockout Risk**:
  - **Puzzle Set (PROD034)**: Inventory level is critically low at only **71 units left** in stock.
  - However, historical demand is very strong (**1,223 units sold**).
  - *Action Item*: Issue an immediate replenishment order to prevent stockouts and lost revenue.
- **Top Performers (Delivered Revenue)**:
  - **Water Purifier (PROD015)**: **$10.42M** revenue (31.6% profit margin).
  - **Smart Watch (PROD002)**: **$5.55M** revenue (30.4% profit margin).
  - **Air Fryer (PROD011)**: **$4.44M** revenue (38.7% profit margin).
- **Lowest Performers**:
  - **Lip Balm Pack (PROD030)**: **$272K** revenue but enjoys a high **48.0% margin**."""

    elif any(w in query_lower for w in ["cohort", "signup", "decay"]):
        return """### 📅 Customer Cohort Retention Findings
- **Headline Metrics**:
  - **Month-1 Retention**: Average **89.33%** of customers remain active.
  - **Month-3 Retention**: Average **88.77%** of customers remain active.
- **Acquisition Trends**:
  - Customers acquired during winter/spring months (Q1) show higher long-term retention compared to summer cohorts.
  - *Retention Decay*: Customer engagement decays gradually over months 0-6. Improving initial product onboarding will help level off the retention curve."""

    elif any(w in query_lower for w in ["retention", "segment", "rfm", "champion", "at risk", "loyal"]):
        return """### 👥 Customer Segmentation Insights (RFM Analysis)
- **At Risk Segment (Crucial Target)**:
  - Consists of **313 customers** (6.31% of base).
  - Contributes **$2.35 Million** (4.01% of total revenue).
  - *Strategic Recommendation*: This segment comprises previously frequent buyers who have stopped purchasing. We recommend launching win-back email offers or loyalty points multipliers immediately.
- **Champions**:
  - Consists of **1,222 customers** (24.63% of base).
  - Generates a whopping **$25.67 Million** (43.89% of total revenue).
  - *Strategy*: Keep them active with VIP pre-launch access and personalized high-value rewards.
- **Loyal Spenders**:
  - Consists of **1,526 customers** (30.76% of base), representing **$19.69 Million** (33.67% of total revenue)."""

    elif any(w in query_lower for w in ["campaign", "roi", "marketing", "sms", "budget", "ad"]):
        return """### 📊 Marketing Campaign ROI Analysis
- **SMS Leads (SMS)**:
  - **Highest ROI**: **2,624.0%** return on spend.
  - Budget: **24.7 Million INR** | Revenue: **675.3 Million INR**.
- **Display Ads (Mega Sale)**:
  - **Second Highest ROI**: **2,522.0%** ROI.
  - Budget: **24.0 Million INR** | Revenue: **629.1 Million INR**.
- **Email Marketing (Festive Season)**:
  - **Third Highest ROI**: **2,301.0%** ROI.
- **Push Notifications (Loyalty Rewards)**:
  - **Weakest Channel**: **1,757.0%** ROI.
  - Budget: **26.1 Million INR** | Revenue: **484.7 Million INR**.
  - *Recommendation*: Shift 15-20% of the Push Notifications budget to SMS and Display Ad campaigns to maximize total return."""

    elif any(w in query_lower for w in ["support", "ticket", "issue", "complain", "csat"]):
        return """### 🛠️ Customer Support Performance
- **Key Metrics**:
  - **Average CSAT Score**: **2.35 / 5.0** (Indicates substantial room for customer service training and process improvement).
  - **Unresolved Tickets**: **1,145 tickets** are currently open (missing close dates or CSAT feedback).
- **Common Support Issues**:
  - Delivery delays, item damage, and payment verification issues dominate the logs.
  - *Action Item*: Establish a dedicated CS response team targeting delivery disputes, specifically prioritizing the *At Risk* customer segment to reduce churn."""

    else:
        return f"""Welcome to **InsightPulse Assistant**!

I have loaded and indexed RetailNova's operational datasets:
- **Transactions**: 50,000 records ($58.48M delivered revenue)
- **Customers**: 4,961 records (Champions, Loyal, At Risk, etc.)
- **Campaigns**: 12 marketing campaigns across channels
- **Support Tickets**: 10,000 customer service logs

**Retrieved Context from database for your query:**
```
{context}
```

*Tip: Type a specific question about product margins, marketing ROI, customer segments, or support tickets to analyze the data.*"""

# ----------------- MAIN UI -----------------
# Header Banner
st.markdown("""
<div class="header-banner">
    <h1>🧠 InsightPulse Assistant</h1>
    <p>Operational RAG Pipeline Interface — RetailNova Analytical Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.subheader("Configuration")
    
    # Clear Conversation Button
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome! I am your **InsightPulse Assistant**. Ask me any question about RetailNova's customer segments, product margins, marketing campaign ROIs, or customer support issues."}
        ]
        if "memory" in st.session_state:
            st.session_state.memory.clear()
        st.rerun()
    
    st.markdown("---")
    st.subheader("💡 Example Questions")
    st.markdown("Click one of the preset business questions below to query the database:")
    
    # Clickable questions
    q1 = st.button("👥 Which customer segments should we target for retention?")
    q2 = st.button("📦 Which products are at risk of running out of stock?")
    q3 = st.button("📊 What is the ROI of our marketing campaigns?")
    q4 = st.button("🛠️ What is the performance of customer support?")
    
    st.markdown("---")
    st.markdown("### 📁 Dataset Status")
    if transactions is not None:
        st.success("✅ Datasets loaded successfully!")
        st.caption(f"Loaded {len(transactions):,} transactions, {len(customers):,} customers, and {len(support):,} support tickets.")
    else:
        st.error("❌ Datasets not found in Data/Raw.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! I am your **InsightPulse Assistant**. Ask me any question about RetailNova's customer segments, product margins, marketing campaign ROIs, or customer support issues."}
    ]

# Initialize LangChain memory
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True
    )

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process example question clicks or direct inputs
clicked_query = None
if q1:
    clicked_query = "Which customer segments should we target for retention?"
elif q2:
    clicked_query = "Which products are at risk of running out of stock?"
elif q3:
    clicked_query = "What is the ROI of our marketing campaigns?"
elif q4:
    clicked_query = "What is the performance of customer support?"

# Text Input box
user_query = st.chat_input("Type your question here...")

active_query = clicked_query or user_query

if active_query:
    # Append user question to state
    st.session_state.messages.append({"role": "user", "content": active_query})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(active_query)
    
    # Try routing through specialized intents and fallback handlers first
    try:
        from intents import route_intent
    except ImportError:
        from chatbot.intents import route_intent
        
    with st.spinner("🤖 Routing query and checking scope..."):
        response_content = route_intent(active_query)
        
    if response_content:
        # Save to LangChain memory manually
        st.session_state.memory.save_context(
            {"question": active_query},
            {"answer": response_content}
        )
    else:
        # 1. Retrieve RAG Context
        with st.spinner("🔍 Scanning operational databases and retrieving context..."):
            context = retrieve_context(active_query)
            
        # 2. Call Offline Responder
        with st.spinner("⚡ Retrieving offline analytical statistics..."):
            response_content = offline_response(active_query, context)
            # Save context to memory manually for offline mode
            st.session_state.memory.save_context(
                {"question": active_query},
                {"answer": response_content}
            )
            
    # Append assistant response to history and rerun to render properly
    st.session_state.messages.append({"role": "assistant", "content": response_content})
    st.rerun()
