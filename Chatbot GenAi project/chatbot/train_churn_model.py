import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import os

def train_model():
    print("Loading datasets...")
    customers_path = 'Data/Raw/customers.csv.xlsx'
    transactions_path = 'Data/Raw/transactions.csv.xlsx'
    
    customers = pd.read_excel(customers_path)
    transactions = pd.read_excel(transactions_path)
    
    print("Preprocessing data...")
    # Calculate recency: days since last transaction
    transactions['order_date'] = pd.to_datetime(transactions['order_date'])
    ref_date = transactions['order_date'].max()
    
    last_purchase = transactions.groupby('customer_id')['order_date'].max().reset_index()
    last_purchase['recency'] = (ref_date - last_purchase['order_date']).dt.days
    
    # Merge recency into customers
    df = pd.merge(customers, last_purchase[['customer_id', 'recency']], on='customer_id', how='left')
    # Fill missing recency (no transactions) with a high value (e.g., 730 days)
    df['recency'] = df['recency'].fillna(730)
    
    # Define target label: 1 if customer segment is 'Dormant' (churned/at risk), else 0
    df['churn'] = (df['segment'] == 'Dormant').astype(int)
    
    # Encode categorical columns
    le_gender = LabelEncoder()
    df['gender_encoded'] = le_gender.fit_transform(df['gender'].astype(str))
    
    le_region = LabelEncoder()
    df['region_encoded'] = le_region.fit_transform(df['region'].astype(str))
    
    # Select features
    feature_cols = ['age', 'gender_encoded', 'region_encoded', 'total_orders', 'lifetime_value', 'recency']
    X = df[feature_cols]
    y = df['churn']
    
    print("Training RandomForestClassifier...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    train_acc = model.score(X_train_scaled, y_train)
    test_acc = model.score(X_test_scaled, y_test)
    print(f"Model trained successfully! Train accuracy: {train_acc:.4f}, Test accuracy: {test_acc:.4f}")
    
    # Save the artifacts
    model_data = {
        'model': model,
        'scaler': scaler,
        'le_gender': le_gender,
        'le_region': le_region,
        'features': feature_cols
    }
    
    os.makedirs('chatbot', exist_ok=True)
    joblib.dump(model_data, 'chatbot/churn_model.joblib')
    print("Saved model artifacts to chatbot/churn_model.joblib")

if __name__ == '__main__':
    train_model()
