import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.data_loader import get_dataset, load_all_datasets, compute_kb_context

def retrieve_context(query: str) -> str:
    """Simple retriever that searches matching keywords in products, campaigns, and support issues"""
    context_chunks = []
    
    # Load required datasets
    customers, products, transactions, support, campaigns, delivered = load_all_datasets()
    
    # Compute KB Context
    kb_context = compute_kb_context(products, campaigns, support, delivered)
    
    # 1. Add static KPIs
    context_chunks.append("=== GENERAL BUSINESS KPIs ===\n" + kb_context.split("Top Products")[0].strip())
    
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
