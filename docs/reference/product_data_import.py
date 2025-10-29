#!/usr/bin/env python3
"""
Product Data Database Import Script
Generated from Excel data analysis.
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductDataImporter:
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        
    def connect(self):
        try:
            self.engine = create_engine(self.database_url)
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def load_and_clean_data(self, excel_path):
        try:
            df = pd.read_excel(excel_path)
            logger.info(f"Loaded {len(df)} rows from Excel file")
            
            # Data cleaning operations

            # Clean Product SKU column
            df['Product SKU'] = df['Product SKU'].astype(str).str.strip()
            df['Product SKU'] = df['Product SKU'].replace('nan', None)
            # Clean Description column
            df['Description'] = df['Description'].astype(str).str.strip()
            df['Description'] = df['Description'].replace('nan', None)
            # Clean Category  column
            df['Category '] = df['Category '].astype(str).str.strip()
            df['Category '] = df['Category '].replace('nan', None)
            # Clean Brand  column
            df['Brand '] = df['Brand '].astype(str).str.strip()
            df['Brand '] = df['Brand '].replace('nan', None)
            
            # Remove duplicates
            original_count = len(df)
            df = df.drop_duplicates()
            if len(df) < original_count:
                logger.info(f"Removed {original_count - len(df)} duplicate rows")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading/cleaning data: {e}")
            return None
    
    def create_table_schema(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            product_sku VARCHAR(500),
            description VARCHAR(500),
            category_ VARCHAR(500),
            brand_ VARCHAR(500),
            catalogueitemid DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
            logger.info("Table schema created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating table schema: {e}")
            return False
    
    def import_data(self, df, table_name='products'):
        try:
            # Clean column names
            df.columns = [col.lower().replace(' ', '_').replace('-', '_') 
                         for col in df.columns]
            
            # Import to database
            df.to_sql(table_name, self.engine, if_exists='append', 
                     index=False, method='multi')
            
            logger.info(f"Successfully imported {len(df)} rows to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False

def main():
    EXCEL_FILE = r"C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\docs\reference\ProductData (Top 3 Cats).xlsx"
    DATABASE_URL = "postgresql://username:password@localhost:5432/database_name"
    
    importer = ProductDataImporter(DATABASE_URL)
    
    if not importer.connect():
        return
    
    df = importer.load_and_clean_data(EXCEL_FILE)
    if df is None:
        return
    
    if not importer.create_table_schema():
        return
    
    if not importer.import_data(df):
        return
    
    logger.info("Database import completed successfully!")

if __name__ == "__main__":
    main()
