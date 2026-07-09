# 🧠 Week 3 Stress Test Suite: 24-Query Routing & Fallback Validation

This document records the comprehensive 24-query stress test performed on the specialized, intent-routed architecture of the **InsightPulse Assistant**. 

### Summary of Results
- **Total Queries Tested**: 24
- **Successful Queries (Correct Route & Handling)**: 24
- **Failed Queries**: 0
- **Partial Successes**: 0
- **Final Pass Rate**: **100.0%**

---

## 📋 Comprehensive Test Registry

### 1. General RAG (In-Scope, Offline Fallback)
*Queries that do not match specialized intents and route to the general vector search or offline RAG responder.*

| # | Query | Expected Route | Actual Route | Status | Response Summary |
|---|---|---|---|---|---|
| 1 | *Which customer segments should we target for retention?* | General RAG | RAG (Offline Fallback) | **PASS** | Returned segmented breakdown for At-Risk, Champions, and Loyal segments. |
| 2 | *Which products are at risk of running out of stock?* | General RAG | RAG (Offline Fallback) | **PASS** | Identified Puzzle Set (PROD034) with 71 units left in inventory. |
| 3 | *What is the ROI of our marketing campaigns?* | General RAG | RAG (Offline Fallback) | **PASS** | Listed SMS (2,624%) and Display Ads (2,522%) as top ROI channels. |
| 4 | *What is the performance of customer support?* | General RAG | RAG (Offline Fallback) | **PASS** | Highlighted average CSAT score of 2.35/5.0 and open ticket volume. |
| 5 | *Summarize common customer support ticket issues* | General RAG | RAG (Offline Fallback) | **PASS** | Summarized delivery delays, damaged items, and payment issues. |

---

### 2. Intent 1: Revenue Summary (Pandas Aggregator)
*Deterministic financial questions requiring precise database calculations.*

| # | Query | Expected Route | Actual Route | Status | Response Summary |
|---|---|---|---|---|---|
| 6 | *What was revenue in March?* | Intent 1 | Intent 1 (Revenue Summary) | **PASS** | Aggregated delivered revenue: **$5.39 Million** (4,209 items across 2023 & 2024). |
| 7 | *Total sales for Electronics in 2024?* | Intent 1 | Intent 1 (Revenue Summary) | **PASS** | Delivered revenue: **$5.85 Million** (3,019 items, 1,569 orders). |
| 8 | *How much did we make in 2023?* | Intent 1 | Intent 1 (Revenue Summary) | **PASS** | Delivered revenue: **$29.59 Million** (24,153 units, 12,421 orders). |
| 9 | *What is the revenue for clothing?* | Intent 1 | Intent 1 (Revenue Summary) | **PASS** | Delivered revenue: **$7.32 Million** (5,952 units, 3,127 orders). |
| 10| *What was the sales figure in December 2024 for sports?* | Intent 1 | Intent 1 (Revenue Summary) | **PASS** | Delivered revenue: **$209.74K** (284 units, 134 orders). |

---

### 3. Intent 2: Customer Risk (Random Forest Classifier)
*Predicting attrition probability and displaying individual customer metrics.*

| # | Query | Expected Route | Actual Route | Status | Response Summary |
|---|---|---|---|---|---|
| 11| *Is customer CUST00123 at risk?* | Intent 2 | Intent 2 (Customer Risk) | **PASS** | Churn Risk: **Low (0.0%)** | Recency: 27 days | LTV: $14.2k | RFM: Regular |
| 12| *Is CUST04427 churn-linked?* | Intent 2 | Intent 2 (Customer Risk) | **PASS** | Churn Risk: **Low (0.0%)** | Recency: 1 day | LTV: $20.0k | RFM: Occasional |
| 13| *Check churn probability for CUST00001* | Intent 2 | Intent 2 (Customer Risk) | **PASS** | Churn Risk: **Low (32.0%)** | Recency: 60 days | LTV: $1.8k | RFM: Occasional |
| 14| *What is the risk rating for CUST00010?* | Intent 2 | Intent 2 (Customer Risk) | **PASS** | Churn Risk: **Medium (59.0%)** | Recency: 85 days | LTV: $76.0k | RFM: Regular |
| 15| *Will customer CUST00250 stop purchasing?* | Intent 2 | Intent 2 (Customer Risk) | **PASS** | Churn Risk: **High (100.0%)** | Recency: 25 days | LTV: $0.00 | RFM: Dormant |

---

### 4. Intent 3: Product Lookup (CSV Direct Query)
*Extracting product specifications, pricing, stock levels, and ratings.*

| # | Query | Expected Route | Actual Route | Status | Response Summary |
|---|---|---|---|---|---|
| 16| *Tell me about Wireless Earbuds* | Intent 3 | Intent 3 (Product Lookup) | **PASS** | Profile: PROD001 | Category: Electronics | Price: $1299 | Margin: 46.2% | Stock: 1,256 |
| 17| *What's the rating for PROD003?* | Intent 3 | Intent 3 (Product Lookup) | **PASS** | Profile: PROD003 (Bluetooth Speaker) | Rating: 3.6/5.0 | Stock: 221 |
| 18| *Get details for PROD015* | Intent 3 | Intent 3 (Product Lookup) | **PASS** | Profile: PROD015 (Water Purifier) | Price: $8999 | Margin: 37.4% | Rating: 4.7/5.0 |
| 19| *How many units of Smart Watch do we have left in stock?* | Intent 3 | Intent 3 (Product Lookup) | **PASS** | Profile: PROD002 (Smart Watch) | Stock: 605 units |
| 20| *Check price and margin of Air Fryer* | Intent 3 | Intent 3 (Product Lookup) | **PASS** | Profile: PROD011 (Air Fryer) | Price: $3999 | Margin: 44.3% |

---

### 5. Out-of-Scope Detection
*Blocking query requests unrelated to RetailNova's business parameters.*

| # | Query | Expected Route | Actual Route | Status | Response Summary |
|---|---|---|---|---|---|
| 21| *What's the weather today in New Delhi?* | Out of Scope | Out-of-Scope Fallback | **PASS** | "I'm InsightPulse Assistant, focused on RetailNova's sales, customers, and support data..." |
| 22| *What is a good recipe for baking chocolate chip cookies?* | Out of Scope | Out-of-Scope Fallback | **PASS** | "I'm InsightPulse Assistant, focused on RetailNova's sales, customers, and support data..." |

---

### 6. Date Out of Bounds Fallback
*Intercepting questions requesting data outside the supported 2023–2024 timeframe.*

| # | Query | Expected Route | Actual Route | Status | Response Summary |
|---|---|---|---|---|---|
| 23| *What was our sales revenue in the year 2022?* | Date Out of Bounds | Date Fallback | **PASS** | "I don't have data for that period; my records cover Jan 2023 to Dec 2024." |
| 24| *Total profit in January 2025?* | Date Out of Bounds | Date Fallback | **PASS** | "I don't have data for that period; my records cover Jan 2023 to Dec 2024." |

---

## 🔍 Failure Analysis & Modularity Review

While the overall pass rate was **100%** on our standardized test set, analyzing edge cases reveals important areas for improvement as the dataset grows:

1. **Failure Theme 1: Zero-Transaction Customers (AOV Division by Zero)**
   - *Query 15*: "Will customer CUST00250 stop purchasing?"
   - *Symptom*: Python threw a runtime warning: `RuntimeWarning: invalid value encountered in scalar divide`.
   - *Root Cause*: Customer CUST00250 is in the `'Dormant'` segment and has `0` transactions. The handler calculated Average Order Value (`cust_ltv / cust_orders`) which resulted in division by zero (`0.00 / 0`).
   - *Mitigation*: The code handled the exception and fell back gracefully (displaying average order value as `$0.00`), but we should enforce a strict zero-orders check inside the customer details formatter.

2. **Failure Theme 2: Product Name Collisions with General Vocabulary**
   - *Potential Issue*: If a customer asks "Is the support team wearing a jacket?", the keyword `"jacket"` triggers the Product Lookup parser rather than Support.
   - *Mitigation*: We placed regex queries (e.g., exact matches like `prod\d{3}`) at a higher priority than simple keyword checks, and we should explore semantic segment classifiers instead of keyword-only classification for generic words.

3. **Failure Theme 3: Multi-Category Financial Inquiries**
   - *Potential Issue*: "What was the revenue for electronics and clothing combined?"
   - *Symptom*: The regex handles single categories (`electronics` or `clothing`) but doesn't aggregate multiple categories in a single call.
   - *Root Cause*: The current Pandas aggregator extracts the *first* matching category found.
   - *Mitigation*: Week 4 will expand category extraction to support list-based filtering and multi-category aggregations.
