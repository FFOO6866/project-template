import asyncio
import asyncpg
import json
from datetime import datetime

async def main():
    # Use the CORRECT port 5432
    conn = await asyncpg.connect(
        'postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5432/horme_db'
    )

    print("=" * 80)
    print("CURRENT DOCUMENT STATUS - REAL-TIME ANALYSIS")
    print("=" * 80)
    print()

    # Get all recent documents
    rows = await conn.fetch('''
        SELECT id, original_filename, ai_status, ai_extracted_data, created_at, file_path, updated_at
        FROM documents
        ORDER BY created_at DESC
        LIMIT 10
    ''')

    if not rows:
        print("❌ NO DOCUMENTS FOUND IN DATABASE")
        await conn.close()
        return

    for row in rows:
        print(f"\n📄 Document ID: {row['id']}")
        print(f"   Filename: {row['original_filename']}")
        print(f"   File Path: {row['file_path']}")
        print(f"   Status: {row['ai_status']}")
        print(f"   Created: {row['created_at']}")
        print(f"   Updated: {row['updated_at']}")

        # Check if file exists
        import os
        file_exists = os.path.exists(row['file_path']) if row['file_path'] else False
        print(f"   File Exists: {'✅ YES' if file_exists else '❌ NO'}")

        if row['ai_extracted_data']:
            try:
                data = json.loads(row['ai_extracted_data']) if isinstance(row['ai_extracted_data'], str) else row['ai_extracted_data']
                print(f"\n   📋 Extracted Data:")

                if 'requirements' in data and 'items' in data.get('requirements', {}):
                    items = data['requirements']['items']
                    print(f"      - Found {len(items)} requirement items")
                    if len(items) > 0:
                        print(f"      - First item: {items[0]}")
                else:
                    print(f"      - ❌ No 'requirements.items' found")
                    print(f"      - Data keys: {list(data.keys())}")

                if 'error' in data:
                    print(f"      - ⚠️  ERROR: {data['error']}")

                if 'full_text_length' in data:
                    print(f"      - Text length: {data['full_text_length']} chars")

            except Exception as e:
                print(f"      - ⚠️  Failed to parse extracted data: {e}")
                print(f"      - Raw data: {row['ai_extracted_data'][:200]}...")
        else:
            print("   ❌ No extracted data")

        print("-" * 80)

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
