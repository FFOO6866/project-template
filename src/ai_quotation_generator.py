#!/usr/bin/env python3
"""
AI-Powered Quotation Generator
Processes uploaded files containing item lists and generates professional quotations
"""

import json
import sqlite3
import pandas as pd
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid
from pathlib import Path
import openpyxl
from difflib import SequenceMatcher

@dataclass
class QuotationItem:
    item_id: str
    description: str
    quantity: int
    unit_price: float
    total_price: float
    product_match: Optional[Dict] = None
    confidence: float = 0.0
    notes: str = ""

@dataclass  
class Quotation:
    quotation_id: str
    client_name: str
    client_email: str
    created_date: str
    valid_until: str
    items: List[QuotationItem]
    subtotal: float
    tax_rate: float = 0.08
    tax_amount: float = 0.0
    total_amount: float = 0.0
    status: str = "draft"
    notes: str = ""

class AIQuotationGenerator:
    """AI-powered quotation generator with intelligent product matching"""
    
    def __init__(self, db_path: str = "products.db"):
        self.db_path = db_path
        self.quotations_db = "quotations.db"
        self.ensure_quotations_table()
        print(f"AI Quotation Generator initialized with {self.count_products()} products")
    
    def ensure_quotations_table(self):
        """Ensure quotations database and table exist"""
        try:
            conn = sqlite3.connect(self.quotations_db)
            cursor = conn.cursor()
            
            # Create quotations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quotation_id TEXT UNIQUE NOT NULL,
                    client_name TEXT NOT NULL,
                    client_email TEXT,
                    created_date TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    subtotal REAL DEFAULT 0,
                    tax_rate REAL DEFAULT 0.08,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    notes TEXT
                )
            """)
            
            # Create quotation items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quotation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quotation_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    product_match_id TEXT,
                    confidence REAL DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (quotation_id) REFERENCES quotations (quotation_id)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error creating quotations table: {e}")
    
    def count_products(self) -> int:
        """Count total products available for matching"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def parse_uploaded_file(self, file_path: str, file_type: str = "auto") -> List[Dict]:
        """Parse uploaded file and extract item list"""
        items = []
        
        try:
            if file_type == "auto":
                file_type = self.detect_file_type(file_path)
            
            if file_type == "excel":
                items = self.parse_excel_file(file_path)
            elif file_type == "csv":
                items = self.parse_csv_file(file_path)
            elif file_type == "text":
                items = self.parse_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
            print(f"Parsed {len(items)} items from {file_type} file")
            return items
            
        except Exception as e:
            print(f"Error parsing file: {e}")
            return []
    
    def detect_file_type(self, file_path: str) -> str:
        """Auto-detect file type based on extension"""
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.csv':
            return 'csv'
        elif ext in ['.txt', '.text']:
            return 'text'
        else:
            return 'text'  # Default fallback
    
    def parse_excel_file(self, file_path: str) -> List[Dict]:
        """Parse Excel file for item data"""
        items = []
        
        try:
            # Try pandas first
            df = pd.read_excel(file_path)
            
            # Look for common column patterns
            item_col = self.find_column(df.columns, ['item', 'product', 'description', 'name'])
            qty_col = self.find_column(df.columns, ['quantity', 'qty', 'amount', 'count'])
            
            for idx, row in df.iterrows():
                if pd.isna(row[item_col]):
                    continue
                    
                item = {
                    'description': str(row[item_col]).strip(),
                    'quantity': self.parse_quantity(row[qty_col] if qty_col else 1),
                    'unit_price': 0.0,  # Will be determined by AI matching
                    'notes': f"Row {idx + 1} from Excel file"
                }
                items.append(item)
                
        except Exception as e:
            print(f"Error parsing Excel file: {e}")
            # Fallback to openpyxl for more complex files
            try:
                workbook = openpyxl.load_workbook(file_path)
                sheet = workbook.active
                
                for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 1):
                    if row[0]:  # First column has content
                        item = {
                            'description': str(row[0]).strip(),
                            'quantity': self.parse_quantity(row[1] if len(row) > 1 else 1),
                            'unit_price': 0.0,
                            'notes': f"Row {row_num} from Excel file"
                        }
                        items.append(item)
                        
            except Exception as e2:
                print(f"Fallback Excel parsing also failed: {e2}")
        
        return items
    
    def parse_csv_file(self, file_path: str) -> List[Dict]:
        """Parse CSV file for item data"""
        items = []
        
        try:
            # Skip comment lines (lines starting with #)
            df = pd.read_csv(file_path, comment='#')
            
            item_col = self.find_column(df.columns, ['item', 'product', 'description', 'name'])
            qty_col = self.find_column(df.columns, ['quantity', 'qty', 'amount', 'count'])
            
            for idx, row in df.iterrows():
                if pd.isna(row[item_col]):
                    continue
                    
                item = {
                    'description': str(row[item_col]).strip(),
                    'quantity': self.parse_quantity(row[qty_col] if qty_col else 1),
                    'unit_price': 0.0,
                    'notes': f"Row {idx + 1} from CSV file"
                }
                items.append(item)
                
        except Exception as e:
            print(f"Error parsing CSV file: {e}")
        
        return items
    
    def parse_text_file(self, file_path: str) -> List[Dict]:
        """Parse text file for item data using AI patterns"""
        items = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by lines and process each
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                # Try to extract quantity and description
                quantity, description = self.parse_line_for_item(line)
                
                if description:
                    item = {
                        'description': description,
                        'quantity': quantity,
                        'unit_price': 0.0,
                        'notes': f"Line {line_num} from text file"
                    }
                    items.append(item)
                    
        except Exception as e:
            print(f"Error parsing text file: {e}")
        
        return items
    
    def find_column(self, columns: List[str], patterns: List[str]) -> Optional[str]:
        """Find column that matches common patterns"""
        columns_lower = [col.lower() for col in columns]
        
        for pattern in patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col:
                    return columns[i]
        
        return columns[0] if columns else None
    
    def parse_quantity(self, value) -> int:
        """Extract numeric quantity from various formats"""
        if pd.isna(value):
            return 1
        
        try:
            # Handle string numbers
            if isinstance(value, str):
                # Extract first number from string
                numbers = re.findall(r'\d+', value)
                return int(numbers[0]) if numbers else 1
            
            return max(1, int(float(value)))
        except:
            return 1
    
    def parse_line_for_item(self, line: str) -> Tuple[int, str]:
        """Parse a text line to extract quantity and item description"""
        # Look for patterns like "5x widget" or "10 pieces of hardware"
        quantity_patterns = [
            r'^(\d+)\s*[x×]\s*(.+)$',  # "5x widget"
            r'^(\d+)\s+(.+)$',          # "5 widget"
            r'(\d+)\s+pieces?\s+of\s+(.+)$',  # "10 pieces of widget"
        ]
        
        for pattern in quantity_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                qty = int(match.group(1))
                desc = match.group(2).strip()
                return qty, desc
        
        # No quantity found, assume 1
        return 1, line
    
    def find_matching_products(self, description: str, limit: int = 5) -> List[Dict]:
        """Find products matching the description using fuzzy matching"""
        matches = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get products with basic info and pricing
            cursor.execute("""
                SELECT DISTINCT p.id, p.name, p.description, p.brand_id, p.category_id,
                       0.0 as unit_price, p.currency,
                       0 as stock_quantity, p.supplier_info as supplier_name
                FROM products p
                WHERE p.name IS NOT NULL AND p.name != ''
                ORDER BY p.name
                LIMIT 1000
            """)
            
            products = cursor.fetchall()
            conn.close()
            
            # Calculate similarity scores
            description_lower = description.lower()
            
            for product in products:
                prod_id, name, desc, brand, category, price, currency, stock, supplier = product
                
                # Create searchable text
                searchable = f"{name} {desc or ''} {brand or ''} {category or ''}"
                searchable_lower = searchable.lower()
                
                # Calculate similarity
                similarity = SequenceMatcher(None, description_lower, searchable_lower).ratio()
                
                # Boost score for exact word matches
                desc_words = set(description_lower.split())
                search_words = set(searchable_lower.split())
                word_overlap = len(desc_words.intersection(search_words)) / max(len(desc_words), 1)
                
                final_score = (similarity * 0.6) + (word_overlap * 0.4)
                
                if final_score > 0.1:  # Only include reasonable matches
                    matches.append({
                        'product_id': prod_id,
                        'name': name,
                        'description': desc,
                        'brand': brand,
                        'category': category,
                        'unit_price': price or 0.0,
                        'currency': currency or 'USD',
                        'stock_quantity': stock or 0,
                        'supplier_name': supplier,
                        'similarity_score': final_score,
                        'searchable_text': searchable
                    })
            
            # Sort by similarity score and return top matches
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            return matches[:limit]
            
        except Exception as e:
            print(f"Error finding matching products: {e}")
            return []
    
    def generate_quotation_from_items(
        self,
        items: List[Dict],
        client_name: str,
        client_email: str = "",
        valid_days: int = 30
    ) -> Quotation:
        """Generate a complete quotation from parsed items"""
        
        quotation_id = f"Q-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        created_date = datetime.now().isoformat()
        valid_until = (datetime.now() + timedelta(days=valid_days)).isoformat()
        
        quotation_items = []
        total_confidence = 0
        
        print(f"Generating quotation {quotation_id} for {len(items)} items...")
        
        for idx, item_data in enumerate(items, 1):
            description = item_data['description']
            quantity = item_data['quantity']
            
            # Find matching products
            matches = self.find_matching_products(description)
            
            if matches:
                best_match = matches[0]
                unit_price = best_match['unit_price'] or 50.0  # Default price if none
                confidence = best_match['similarity_score']
                total_confidence += confidence
                
                product_match = {
                    'product_id': best_match['product_id'],
                    'name': best_match['name'],
                    'brand': best_match['brand'],
                    'supplier': best_match['supplier_name']
                }
                
                notes = f"Matched to: {best_match['name']} (confidence: {confidence:.2f})"
                if best_match['stock_quantity']:
                    notes += f", Stock: {best_match['stock_quantity']}"
                    
            else:
                # No match found, use estimated pricing
                unit_price = self.estimate_price_from_description(description)
                confidence = 0.0
                product_match = None
                notes = "No exact product match found - estimated pricing"
            
            quotation_item = QuotationItem(
                item_id=f"ITEM-{idx:03d}",
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantity * unit_price,
                product_match=product_match,
                confidence=confidence,
                notes=notes
            )
            
            quotation_items.append(quotation_item)
        
        # Calculate totals
        subtotal = sum(item.total_price for item in quotation_items)
        tax_rate = 0.08
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        avg_confidence = total_confidence / len(items) if items else 0
        
        quotation = Quotation(
            quotation_id=quotation_id,
            client_name=client_name,
            client_email=client_email,
            created_date=created_date,
            valid_until=valid_until,
            items=quotation_items,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            status="draft",
            notes=f"Auto-generated quotation. Average matching confidence: {avg_confidence:.2f}"
        )
        
        # Save to database
        self.save_quotation(quotation)
        
        print(f"Generated quotation {quotation_id}")
        print(f"   Items: {len(quotation_items)}")
        print(f"   Total: ${total_amount:.2f}")
        print(f"   Avg Confidence: {avg_confidence:.2f}")
        
        return quotation
    
    def estimate_price_from_description(self, description: str) -> float:
        """Estimate price based on description keywords"""
        description_lower = description.lower()
        
        # Price estimation based on keywords
        if any(word in description_lower for word in ['premium', 'professional', 'enterprise']):
            return 200.0
        elif any(word in description_lower for word in ['standard', 'regular', 'basic']):
            return 100.0
        elif any(word in description_lower for word in ['budget', 'economy', 'simple']):
            return 50.0
        else:
            return 75.0  # Default estimate
    
    def save_quotation(self, quotation: Quotation):
        """Save quotation to database using existing schema"""
        try:
            conn = sqlite3.connect(self.quotations_db)
            cursor = conn.cursor()
            
            # Insert quotation using existing schema
            cursor.execute("""
                INSERT INTO quotations 
                (quote_number, customer_name, title, description, total_amount, currency,
                 status, valid_until, subtotal, tax_amount, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quotation.quotation_id, quotation.client_name, 
                f"AI Generated Quotation for {quotation.client_name}",
                f"Quotation generated from uploaded file with {len(quotation.items)} items",
                quotation.total_amount, 'USD', quotation.status, quotation.valid_until,
                quotation.subtotal, quotation.tax_amount, quotation.notes
            ))
            
            # Get the inserted quotation ID
            quotation_db_id = cursor.lastrowid
            
            # Insert quotation items
            for item in quotation.items:
                cursor.execute("""
                    INSERT INTO quotation_items
                    (quotation_id, item_id, description, quantity, unit_price, 
                     total_price, product_match_id, confidence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quotation_db_id, item.item_id, item.description,
                    item.quantity, item.unit_price, item.total_price,
                    item.product_match['product_id'] if item.product_match else None,
                    item.confidence, item.notes
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving quotation: {e}")
    
    def get_quotation(self, quotation_id: str) -> Optional[Quotation]:
        """Retrieve quotation by ID"""
        try:
            conn = sqlite3.connect(self.quotations_db)
            cursor = conn.cursor()
            
            # Get quotation details
            cursor.execute("""
                SELECT quotation_id, client_name, client_email, created_date, valid_until,
                       status, subtotal, tax_rate, tax_amount, total_amount, notes
                FROM quotations WHERE quotation_id = ?
            """, (quotation_id,))
            
            quote_data = cursor.fetchone()
            if not quote_data:
                return None
            
            # Get quotation items
            cursor.execute("""
                SELECT item_id, description, quantity, unit_price, total_price,
                       product_match_id, confidence, notes
                FROM quotation_items WHERE quotation_id = ?
                ORDER BY item_id
            """, (quotation_id,))
            
            items_data = cursor.fetchall()
            conn.close()
            
            # Build quotation object
            items = []
            for item_row in items_data:
                item_id, desc, qty, unit_price, total_price, prod_id, conf, notes = item_row
                
                product_match = {'product_id': prod_id} if prod_id else None
                
                item = QuotationItem(
                    item_id=item_id,
                    description=desc,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=total_price,
                    product_match=product_match,
                    confidence=conf or 0.0,
                    notes=notes or ""
                )
                items.append(item)
            
            quotation = Quotation(
                quotation_id=quote_data[0],
                client_name=quote_data[1],
                client_email=quote_data[2] or "",
                created_date=quote_data[3],
                valid_until=quote_data[4],
                items=items,
                subtotal=quote_data[6],
                tax_rate=quote_data[7],
                tax_amount=quote_data[8],
                total_amount=quote_data[9],
                status=quote_data[5],
                notes=quote_data[10] or ""
            )
            
            return quotation
            
        except Exception as e:
            print(f"Error retrieving quotation: {e}")
            return None

def main():
    """Command-line interface for AI quotation generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Powered Quotation Generator')
    parser.add_argument('--file', required=False, help='Input file path (Excel, CSV, or text)')
    parser.add_argument('--client_name', required=False, help='Client name')
    parser.add_argument('--client_email', default='', help='Client email')
    parser.add_argument('--output_format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--test', action='store_true', help='Run test mode with sample data')
    
    args = parser.parse_args()
    
    generator = AIQuotationGenerator()
    
    if args.test or (not args.file and not args.client_name):
        # Test mode with sample items
        sample_items = [
            {'description': 'Industrial LED Light Fixture', 'quantity': 10},
            {'description': 'Safety Helmet with Visor', 'quantity': 25},
            {'description': 'Stainless Steel Pipe 2 inch diameter', 'quantity': 50},
        ]
        
        quotation = generator.generate_quotation_from_items(
            items=sample_items,
            client_name="Test Client Corporation",
            client_email="client@example.com"
        )
        
    else:
        # Parse file and generate quotation
        if not args.file or not args.client_name:
            print("Error: --file and --client_name are required")
            return 1
        
        try:
            # Parse the uploaded file
            items = generator.parse_uploaded_file(args.file)
            
            if not items:
                print("Error: No items found in the uploaded file")
                return 1
            
            # Generate quotation
            quotation = generator.generate_quotation_from_items(
                items=items,
                client_name=args.client_name,
                client_email=args.client_email
            )
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    # Output results
    if args.output_format == 'json':
        # Convert quotation to JSON-serializable format
        quotation_dict = {
            'quotation_id': quotation.quotation_id,
            'client_name': quotation.client_name,
            'client_email': quotation.client_email,
            'created_date': quotation.created_date,
            'valid_until': quotation.valid_until,
            'items': [
                {
                    'item_id': item.item_id,
                    'description': item.description,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price,
                    'confidence': item.confidence,
                    'notes': item.notes,
                    'product_match': item.product_match
                }
                for item in quotation.items
            ],
            'subtotal': quotation.subtotal,
            'tax_rate': quotation.tax_rate,
            'tax_amount': quotation.tax_amount,
            'total_amount': quotation.total_amount,
            'status': quotation.status,
            'notes': quotation.notes
        }
        
        print(json.dumps(quotation_dict, indent=2))
        
    else:
        # Text output
        print(f"\n📋 Generated Quotation: {quotation.quotation_id}")
        print(f"💰 Total Amount: ${quotation.total_amount:.2f}")
        print(f"📦 Items: {len(quotation.items)}")
        
        for item in quotation.items:
            print(f"  - {item.description}: {item.quantity} x ${item.unit_price:.2f} = ${item.total_price:.2f}")
    
    return 0

if __name__ == "__main__":
    exit(main())