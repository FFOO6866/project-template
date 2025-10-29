import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect(
        'postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5434/horme_db'
    )

    print("=" * 80)
    print("DOCUMENT PROCESSING STATUS ANALYSIS")
    print("=" * 80)

    rows = await conn.fetch('''
        SELECT id, original_filename, ai_status, ai_extracted_data, created_at, file_path
        FROM documents
        ORDER BY created_at DESC
        LIMIT 5
    ''')

    for row in rows:
        print(f"\nDocument ID: {row['id']}")
        print(f"Filename: {row['original_filename']}")
        print(f"File Path: {row['file_path']}")
        print(f"Status: {row['ai_status']}")
        print(f"Created: {row['created_at']}")

        if row['ai_extracted_data']:
            data = json.loads(row['ai_extracted_data'])
            print(f"\nExtracted Data:")
            print(f"  - Requirements items: {len(data.get('requirements', {}).get('items', []))}")
            if data.get('requirements', {}).get('items'):
                print(f"  - First item: {data['requirements']['items'][0]}")
            print(f"  - Full text length: {data.get('full_text_length', 'N/A')}")
            if 'error' in data:
                print(f"  - ERROR: {data['error']}")
        else:
            print("  - No extracted data")

        print("-" * 80)

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
