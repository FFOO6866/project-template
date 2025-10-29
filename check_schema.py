import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        'postgresql://horme_user:96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42@localhost:5432/horme_db'
    )

    print("=" * 80)
    print("DATABASE SCHEMA CHECK - DOCUMENTS TABLE")
    print("=" * 80)
    print()

    # Get all columns from documents table
    schema = await conn.fetch('''
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    ''')

    if not schema:
        print("❌ 'documents' TABLE DOES NOT EXIST!")

        # Check what tables DO exist
        tables = await conn.fetch('''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        ''')

        print("\n📋 Available tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
    else:
        print("✅ Documents table exists with the following columns:")
        print()
        for col in schema:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"   {col['column_name']:<30} {col['data_type']:<20} {nullable}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
