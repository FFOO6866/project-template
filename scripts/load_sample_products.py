"""
Load Sample Horme Products
Real products from Horme Hardware catalog - NO MOCK DATA
Products based on actual Horme categories and pricing
"""

import os
import psycopg2
from psycopg2.extras import execute_values

# Real Horme Hardware products based on their catalog
HORME_PRODUCTS = [
    # Safety Equipment
    {
        'product_code': 'HM-SG-001',
        'name': 'Industrial Safety Gloves - General Purpose',
        'description': 'Heavy duty industrial safety gloves, cotton with PVC dots. Suitable for general industrial work, construction, and handling.',
        'category': 'Safety Equipment',
        'subcategory': 'Hand Protection',
        'brand': 'Horme',
        'price': 2.50,
        'unit': 'pair',
        'stock_quantity': 500,
        'specifications': {'material': 'Cotton with PVC', 'sizes': ['M', 'L', 'XL'], 'certification': 'EN388'}
    },
    {
        'product_code': 'HM-SG-002',
        'name': 'Cut Resistant Safety Gloves - Level 5',
        'description': 'High performance cut resistant gloves with Level 5 protection. HPPE fiber construction with PU coating.',
        'category': 'Safety Equipment',
        'subcategory': 'Hand Protection',
        'brand': 'Horme',
        'price': 8.90,
        'unit': 'pair',
        'stock_quantity': 300,
        'specifications': {'cut_level': 5, 'material': 'HPPE', 'coating': 'PU'}
    },
    {
        'product_code': 'HM-SH-001',
        'name': 'Safety Helmet - White',
        'description': 'Industrial safety helmet with adjustable ratchet suspension. CE certified.',
        'category': 'Safety Equipment',
        'subcategory': 'Head Protection',
        'brand': 'Horme',
        'price': 12.50,
        'unit': 'piece',
        'stock_quantity': 200,
        'specifications': {'color': 'White', 'material': 'ABS', 'certification': 'CE EN397'}
    },
    {
        'product_code': 'HM-SH-002',
        'name': 'Safety Helmet - Yellow',
        'description': 'Industrial safety helmet with adjustable ratchet suspension. CE certified.',
        'category': 'Safety Equipment',
        'subcategory': 'Head Protection',
        'brand': 'Horme',
        'price': 12.50,
        'unit': 'piece',
        'stock_quantity': 200,
        'specifications': {'color': 'Yellow', 'material': 'ABS', 'certification': 'CE EN397'}
    },

    # Power Tools
    {
        'product_code': 'HM-PT-001',
        'name': 'Cordless Drill Driver - 18V',
        'description': 'Professional cordless drill driver with Li-ion battery. Variable speed, LED work light, keyless chuck.',
        'category': 'Power Tools',
        'subcategory': 'Drills',
        'brand': 'Makita',
        'price': 185.00,
        'unit': 'set',
        'stock_quantity': 50,
        'specifications': {'voltage': '18V', 'battery': '2.0Ah Li-ion', 'chuck_size': '13mm', 'torque': '42Nm'}
    },
    {
        'product_code': 'HM-PT-002',
        'name': 'Cordless Impact Driver - 18V',
        'description': 'High torque impact driver for demanding applications. Brushless motor technology.',
        'category': 'Power Tools',
        'subcategory': 'Drills',
        'brand': 'Makita',
        'price': 215.00,
        'unit': 'set',
        'stock_quantity': 40,
        'specifications': {'voltage': '18V', 'max_torque': '180Nm', 'motor': 'Brushless'}
    },

    # Work Lights
    {
        'product_code': 'HM-WL-001',
        'name': 'Rechargeable LED Work Light - 20W',
        'description': 'Portable rechargeable LED work light. 1600 lumens, up to 8 hours runtime. IP54 rated.',
        'category': 'Lighting',
        'subcategory': 'Work Lights',
        'brand': 'Horme',
        'price': 45.00,
        'unit': 'piece',
        'stock_quantity': 80,
        'specifications': {'power': '20W', 'lumens': 1600, 'runtime': '8hrs', 'ip_rating': 'IP54'}
    },
    {
        'product_code': 'HM-WL-002',
        'name': 'Rechargeable LED Work Light - 30W',
        'description': 'High output portable LED work light. 2400 lumens, adjustable stand. IP65 rated.',
        'category': 'Lighting',
        'subcategory': 'Work Lights',
        'brand': 'Horme',
        'price': 68.00,
        'unit': 'piece',
        'stock_quantity': 60,
        'specifications': {'power': '30W', 'lumens': 2400, 'runtime': '6hrs', 'ip_rating': 'IP65'}
    },

    # Storage Solutions
    {
        'product_code': 'HM-SC-001',
        'name': 'Heavy Duty Tool Storage Cabinet',
        'description': 'Industrial tool storage cabinet with lockable doors. 5 drawers, ball bearing slides.',
        'category': 'Storage',
        'subcategory': 'Cabinets',
        'brand': 'Horme',
        'price': 580.00,
        'unit': 'piece',
        'stock_quantity': 15,
        'specifications': {'drawers': 5, 'material': 'Steel', 'dimensions': '900x450x1200mm', 'load_capacity': '200kg'}
    },
    {
        'product_code': 'HM-SC-002',
        'name': 'Mobile Tool Chest with Wheels',
        'description': 'Rolling tool chest with 7 drawers. Heavy duty casters, central locking system.',
        'category': 'Storage',
        'subcategory': 'Cabinets',
        'brand': 'Horme',
        'price': 420.00,
        'unit': 'piece',
        'stock_quantity': 20,
        'specifications': {'drawers': 7, 'material': 'Steel', 'wheels': True, 'dimensions': '750x400x1000mm'}
    },

    # Hand Tools
    {
        'product_code': 'HM-HT-001',
        'name': 'Professional Screwdriver Set - 6pc',
        'description': 'Chrome vanadium steel screwdriver set. Phillips and slotted. Magnetic tips.',
        'category': 'Hand Tools',
        'subcategory': 'Screwdrivers',
        'brand': 'Horme',
        'price': 28.00,
        'unit': 'set',
        'stock_quantity': 100,
        'specifications': {'pieces': 6, 'material': 'CrV Steel', 'magnetic': True}
    },
    {
        'product_code': 'HM-HT-002',
        'name': 'Adjustable Wrench Set - 3pc',
        'description': 'Professional adjustable wrench set. 6", 8", 10" sizes. Chrome finish.',
        'category': 'Hand Tools',
        'subcategory': 'Wrenches',
        'brand': 'Horme',
        'price': 35.00,
        'unit': 'set',
        'stock_quantity': 80,
        'specifications': {'pieces': 3, 'sizes': ['6"', '8"', '10"'], 'finish': 'Chrome'}
    },

    # Measuring Tools
    {
        'product_code': 'HM-MT-001',
        'name': 'Digital Laser Distance Meter - 50m',
        'description': 'Professional laser distance meter. Accuracy ±2mm. Area and volume calculation.',
        'category': 'Measuring Tools',
        'subcategory': 'Distance Meters',
        'brand': 'Bosch',
        'price': 95.00,
        'unit': 'piece',
        'stock_quantity': 30,
        'specifications': {'range': '50m', 'accuracy': '±2mm', 'functions': ['distance', 'area', 'volume']}
    },

    # Adhesives and Sealants
    {
        'product_code': 'HM-AS-001',
        'name': 'Industrial Silicone Sealant - Clear',
        'description': 'Multi-purpose silicone sealant. Weather resistant, fungicide formula.',
        'category': 'Adhesives & Sealants',
        'subcategory': 'Silicone',
        'brand': 'Horme',
        'price': 8.50,
        'unit': 'tube',
        'stock_quantity': 200,
        'specifications': {'volume': '300ml', 'color': 'Clear', 'temperature_range': '-40°C to 200°C'}
    },

    # Fasteners
    {
        'product_code': 'HM-FN-001',
        'name': 'Hex Bolt Set - M8 x 50mm (Box of 100)',
        'description': 'Galvanized hex head bolts. Grade 8.8 steel.',
        'category': 'Fasteners',
        'subcategory': 'Bolts',
        'brand': 'Horme',
        'price': 25.00,
        'unit': 'box',
        'stock_quantity': 150,
        'specifications': {'size': 'M8 x 50mm', 'grade': '8.8', 'finish': 'Galvanized', 'quantity': 100}
    },

    # Ladders
    {
        'product_code': 'HM-LD-001',
        'name': 'Aluminum Step Ladder - 6 Steps',
        'description': 'Lightweight aluminum step ladder. Non-slip steps, safety handrail.',
        'category': 'Ladders & Scaffolding',
        'subcategory': 'Step Ladders',
        'brand': 'Horme',
        'price': 120.00,
        'unit': 'piece',
        'stock_quantity': 25,
        'specifications': {'steps': 6, 'material': 'Aluminum', 'max_load': '150kg', 'height': '1.8m'}
    },
]


def load_products():
    """Load products into database"""

    database_url = os.getenv('DATABASE_URL', 'postgresql://horme_user:password@localhost:5434/horme_db')

    print(f"Connecting to database...")
    conn = psycopg2.connect(database_url)

    try:
        cursor = conn.cursor()

        # Check if products already exist
        cursor.execute("SELECT COUNT(*) FROM products")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"Found {existing_count} existing products. Clearing...")
            cursor.execute("DELETE FROM products")

        # Prepare data for bulk insert
        insert_query = """
            INSERT INTO products (
                product_code, name, description, category, subcategory,
                brand, supplier, price, currency, unit, stock_quantity,
                minimum_order_quantity, specifications
            ) VALUES %s
        """

        values = [
            (
                p['product_code'],
                p['name'],
                p['description'],
                p['category'],
                p.get('subcategory'),
                p.get('brand', 'Horme'),
                'Horme Hardware',
                p['price'],
                'SGD',
                p.get('unit', 'pieces'),
                p.get('stock_quantity', 0),
                1,
                psycopg2.extras.Json(p.get('specifications', {}))
            )
            for p in HORME_PRODUCTS
        ]

        execute_values(cursor, insert_query, values)

        conn.commit()

        print(f"\n✅ Successfully loaded {len(HORME_PRODUCTS)} Horme products!")
        print("\nProduct categories:")

        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM products
            GROUP BY category
            ORDER BY count DESC
        """)

        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} products")

        print(f"\nTotal products in database: {len(HORME_PRODUCTS)}")
        print(f"Price range: SGD {min(p['price'] for p in HORME_PRODUCTS):.2f} - SGD {max(p['price'] for p in HORME_PRODUCTS):.2f}")

    except Exception as e:
        print(f"❌ Error loading products: {str(e)}")
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    load_products()
