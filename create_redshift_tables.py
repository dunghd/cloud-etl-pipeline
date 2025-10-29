#!/usr/bin/env python3
"""
Script to create Redshift tables using Python
Run this script to set up your Redshift data warehouse schema
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Create all necessary tables in Redshift"""
    
    # Connection parameters from environment variables
    conn_params = {
        'host': os.getenv('REDSHIFT_HOST'),
        'port': os.getenv('REDSHIFT_PORT', '5439'),
        'database': os.getenv('REDSHIFT_DATABASE'),
        'user': os.getenv('REDSHIFT_USER'),
        'password': os.getenv('REDSHIFT_PASSWORD')
    }
    
    # Validate required parameters
    missing = [k for k, v in conn_params.items() if not v]
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        return False
    
    # SQL statements
    create_sales_fact_table = """
    CREATE TABLE IF NOT EXISTS sales_fact (
        transaction_id VARCHAR(20) NOT NULL,
        customer_id VARCHAR(20),
        product_id VARCHAR(20),
        sales_amount DECIMAL(10, 2),
        quantity INTEGER,
        discount DECIMAL(5, 2),
        tax DECIMAL(5, 2),
        transaction_date TIMESTAMP,
        store_id VARCHAR(20),
        processed_at TIMESTAMP,
        year INTEGER,
        month INTEGER,
        day INTEGER,
        hour INTEGER,
        PRIMARY KEY (transaction_id)
    )
    DISTSTYLE KEY
    DISTKEY (customer_id)
    SORTKEY (transaction_date, customer_id);
    """
    
    create_sales_summary_table = """
    CREATE TABLE IF NOT EXISTS sales_summary (
        summary_date DATE NOT NULL,
        store_id VARCHAR(20),
        total_sales DECIMAL(15, 2),
        total_quantity INTEGER,
        total_transactions INTEGER,
        avg_transaction_value DECIMAL(10, 2),
        PRIMARY KEY (summary_date, store_id)
    )
    DISTSTYLE ALL
    SORTKEY (summary_date);
    """
    
    create_dim_customer_table = """
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_id VARCHAR(20) NOT NULL,
        first_transaction_date TIMESTAMP,
        last_transaction_date TIMESTAMP,
        total_lifetime_value DECIMAL(15, 2),
        total_orders INTEGER,
        PRIMARY KEY (customer_id)
    )
    DISTSTYLE ALL
    SORTKEY (customer_id);
    """
    
    create_dim_product_table = """
    CREATE TABLE IF NOT EXISTS dim_product (
        product_id VARCHAR(20) NOT NULL,
        total_sales DECIMAL(15, 2),
        total_quantity_sold INTEGER,
        avg_price DECIMAL(10, 2),
        first_sale_date TIMESTAMP,
        last_sale_date TIMESTAMP,
        PRIMARY KEY (product_id)
    )
    DISTSTYLE ALL
    SORTKEY (product_id);
    """
    
    create_dim_store_table = """
    CREATE TABLE IF NOT EXISTS dim_store (
        store_id VARCHAR(20) NOT NULL,
        total_sales DECIMAL(15, 2),
        total_transactions INTEGER,
        avg_transaction_value DECIMAL(10, 2),
        PRIMARY KEY (store_id)
    )
    DISTSTYLE ALL
    SORTKEY (store_id);
    """
    
    verify_tables_query = """
    SELECT 
        table_schema,
        table_name,
        table_type
    FROM information_schema.tables
    WHERE table_schema = 'public'
        AND table_name IN ('sales_fact', 'sales_summary', 'dim_customer', 'dim_product', 'dim_store')
    ORDER BY table_name;
    """
    
    try:
        print("🔌 Connecting to Redshift...")
        print(f"   Host: {conn_params['host']}")
        print(f"   Database: {conn_params['database']}")
        print(f"   User: {conn_params['user']}")
        
        # Connect to Redshift
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        print("✅ Connected successfully!\n")
        
        # Create tables
        tables = [
            ('sales_fact', create_sales_fact_table),
            ('sales_summary', create_sales_summary_table),
            ('dim_customer', create_dim_customer_table),
            ('dim_product', create_dim_product_table),
            ('dim_store', create_dim_store_table)
        ]
        
        for table_name, create_sql in tables:
            print(f"📊 Creating table: {table_name}...")
            cursor.execute(create_sql)
            conn.commit()
            print(f"   ✅ Table {table_name} created successfully")
        
        print("\n🔍 Verifying tables...")
        cursor.execute(verify_tables_query)
        results = cursor.fetchall()
        
        if results:
            print("\n📋 Created tables:")
            print("-" * 60)
            print(f"{'Schema':<15} {'Table Name':<20} {'Type':<15}")
            print("-" * 60)
            for row in results:
                print(f"{row[0]:<15} {row[1]:<20} {row[2]:<15}")
            print("-" * 60)
        else:
            print("⚠️  No tables found")
        
        # Get table details
        print("\n📈 Table statistics:")
        for table_name, _ in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count} rows")
        
        cursor.close()
        conn.close()
        
        print("\n✅ All tables created successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your Redshift cluster is running")
        print("2. Verify security group allows your IP address")
        print("3. Confirm VPC and subnet settings")
        print("4. Check credentials in .env file")
        return False
        
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("🚀 Redshift Table Creation Script")
    print("="*60)
    print()
    
    success = create_tables()
    
    if success:
        print("\n" + "="*60)
        print("✨ Setup Complete! Your Redshift tables are ready.")
        print("="*60)
        print("\nNext steps:")
        print("1. Run: poetry run python my_pipeline.py")
        print("2. Check data: SELECT COUNT(*) FROM sales_fact;")
    else:
        print("\n" + "="*60)
        print("❌ Setup failed. Please fix the errors above.")
        print("="*60)
        exit(1)
