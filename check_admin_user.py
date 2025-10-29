"""
Check if admin user exists in database
"""
import psycopg2
import bcrypt

# Database configuration
DATABASE_HOST = 'localhost'
DATABASE_PORT = '5434'
DATABASE_NAME = 'horme_db'
DATABASE_USER = 'horme_user'
DATABASE_PASSWORD = '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'

# Connect to database
conn = psycopg2.connect(
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD
)

with conn.cursor() as cur:
    # Check if users table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'users'
        );
    """)
    table_exists = cur.fetchone()[0]
    print(f"Users table exists: {table_exists}")

    if table_exists:
        # Check for admin user
        cur.execute("SELECT email, role, password_hash FROM users WHERE email = %s", ('admin@yourdomain.com',))
        user = cur.fetchone()

        if user:
            email, role, password_hash = user
            print(f"\nAdmin user found:")
            print(f"  Email: {email}")
            print(f"  Role: {role}")
            print(f"  Password hash exists: {bool(password_hash)}")

            # Test password verification
            test_password = "admin123"
            try:
                if bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8')):
                    print(f"  Password 'admin123' matches: YES")
                else:
                    print(f"  Password 'admin123' matches: NO")
            except Exception as e:
                print(f"  Password verification error: {e}")
        else:
            print("\nAdmin user NOT found (admin@yourdomain.com)")

            # Check what users exist
            cur.execute("SELECT email, role FROM users LIMIT 5")
            users = cur.fetchall()
            print(f"\nExisting users ({len(users)}):")
            for email, role in users:
                print(f"  - {email} ({role})")
    else:
        print("\nUsers table does not exist!")
        print("\nDatabase tables:")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        for (table_name,) in tables:
            print(f"  - {table_name}")

conn.close()
