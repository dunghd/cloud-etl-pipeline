# Sample test data generator script
import pandas as pd
import os
from datetime import datetime, timedelta
import random

def generate_sample_sales_data(num_rows=10000):
    """Generate sample sales data for testing"""
    
    # Generate date range
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)]
    
    # Generate sample data
    data = {
        'transaction_id': [f'TXN{i:06d}' for i in range(num_rows)],
        'customer_id': [f'CUST{random.randint(1, 1000):04d}' for _ in range(num_rows)],
        'product_id': [f'PROD{random.randint(1, 100):03d}' for _ in range(num_rows)],
        'sales_amount': [round(random.uniform(10, 1000), 2) for _ in range(num_rows)],
        'quantity': [random.randint(1, 10) for _ in range(num_rows)],
        'discount': [round(random.uniform(0, 0.3), 2) for _ in range(num_rows)],
        'tax': [round(random.uniform(0, 0.1), 2) for _ in range(num_rows)],
        'transaction_date': dates,
        'store_id': [f'STORE{random.randint(1, 20):02d}' for _ in range(num_rows)]
    }
    
    df = pd.DataFrame(data)
    
    # Add some duplicates and nulls for testing data cleaning
    # Add 5% duplicates
    num_duplicates = int(num_rows * 0.05)
    duplicate_rows = df.sample(n=num_duplicates)
    df = pd.concat([df, duplicate_rows], ignore_index=True)
    
    # Add 2% nulls
    for col in ['discount', 'tax']:
        null_indices = random.sample(range(len(df)), int(len(df) * 0.02))
        df.loc[null_indices, col] = None
    
    return df

def save_sample_data():
    """Generate and save sample data in multiple formats"""
    
    # Create data directory
    os.makedirs('data/raw/sample_data', exist_ok=True)
    
    # Generate data
    print("Generating sample sales data...")
    df = generate_sample_sales_data(10000)
    
    # Save in different formats
    print("Saving as Parquet...")
    df.to_parquet('data/raw/sample_data/sales_data.parquet', index=False)
    
    print("Saving as CSV...")
    df.to_csv('data/raw/sample_data/sales_data.csv', index=False)
    
    print("Saving as JSON...")
    df.to_json('data/raw/sample_data/sales_data.json', orient='records', lines=True)
    
    print(f"\nSample data generated successfully!")
    print(f"Total rows: {len(df)}")
    print(f"\nData saved to:")
    print("  - data/raw/sample_data/sales_data.parquet")
    print("  - data/raw/sample_data/sales_data.csv")
    print("  - data/raw/sample_data/sales_data.json")
    print("\nSample data preview:")
    print(df.head())

if __name__ == '__main__':
    save_sample_data()
