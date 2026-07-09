import os
# pyrefly: ignore [missing-import]
import streamlit as st
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import config
from chatbot import data_loader
from chatbot.retriever import retrieve_context
from chatbot.responder import offline_response
from chatbot.intents import route_intent

try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    from langchain_classic.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Page configuration for a premium, wide dashboard look
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state=config.INITIAL_SIDEBAR_STATE
)

# Custom CSS to apply a high-end light premium theme
st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)

# ----------------- DATA PREPARATION -----------------
@st.cache_data
def load_datasets_cached():
    """Load and aggregate datasets with Streamlit caching support"""
    return data_loader.load_all_datasets()

customers, products, transactions, support, campaigns, delivered = load_datasets_cached()

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
    
    # Clickable questions grouped in expanders for premium look
    with st.expander("🔍 General Business RAG", expanded=True):
        q1 = st.button("👥 Target segments for retention?")
        q2 = st.button("📦 Products running out of stock?")
        q3 = st.button("📊 ROI of marketing campaigns?")
        q4 = st.button("🛠️ Performance of customer support?")
        
    with st.expander("📈 Revenue Aggregation (Intent 1)"):
        q5 = st.button("💰 What was revenue in March?")
        q6 = st.button("👔 Total sales for Electronics in 2024?")
        q7 = st.button("💵 How much did we make in 2023?")
        q8 = st.button("👚 What is the revenue for clothing?")
        q9 = st.button("⚽ Sales in Dec 2024 for sports?")
        
    with st.expander("👤 Customer Risk Prediction (Intent 2)"):
        q10 = st.button("🛡️ Is customer CUST00123 at risk?")
        q11 = st.button("⚡ Is CUST04427 churn-linked?")
        q12 = st.button("📉 Churn probability for CUST00001")
        q13 = st.button("🔑 Risk rating for CUST00010?")
        q14 = st.button("🛑 Will customer CUST00250 stop purchasing?")
        
    with st.expander("🏷️ Product Details Lookup (Intent 3)"):
        q15 = st.button("🎧 Tell me about Wireless Earbuds")
        q16 = st.button("⭐ What's the rating for PROD003?")
        q17 = st.button("📦 Get details for PROD015")
        q18 = st.button("🕒 Stock of Smart Watch?")
        q19 = st.button("🔥 Price and margin of Air Fryer")
        

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
elif q5:
    clicked_query = "What was revenue in March?"
elif q6:
    clicked_query = "Total sales for Electronics in 2024?"
elif q7:
    clicked_query = "How much did we make in 2023?"
elif q8:
    clicked_query = "What is the revenue for clothing?"
elif q9:
    clicked_query = "What was the sales figure in December 2024 for sports?"
elif q10:
    clicked_query = "Is customer CUST00123 at risk?"
elif q11:
    clicked_query = "Is CUST04427 churn-linked?"
elif q12:
    clicked_query = "Check churn probability for CUST00001"
elif q13:
    clicked_query = "What is the risk rating for CUST00010?"
elif q14:
    clicked_query = "Will customer CUST00250 stop purchasing?"
elif q15:
    clicked_query = "Tell me about Wireless Earbuds"
elif q16:
    clicked_query = "What's the rating for PROD003?"
elif q17:
    clicked_query = "Get details for PROD015"
elif q18:
    clicked_query = "How many units of Smart Watch do we have left in stock?"
elif q19:
    clicked_query = "Check price and margin of Air Fryer"

# Text Input box
user_query = st.chat_input("Type your question here...")

active_query = clicked_query or user_query

if active_query:
    # Append user question to state
    st.session_state.messages.append({"role": "user", "content": active_query})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(active_query)
        
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
