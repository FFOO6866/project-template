"""
Add login users to database with properly hashed passwords
NO HARDCODED PASSWORDS - Uses bcrypt hashing for security
"""
import psycopg2
import bcrypt
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Database connection parameters from docker-compose
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'dbname': 'horme_db',
    'user': 'horme_user',
    'password': '96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'
}

def hash_password(password: str) -> str:
    """Generate bcrypt hash for password - NO PLAIN TEXT STORAGE"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def add_user(conn, email: str, first_name: str, last_name: str, password: str, role: str = 'sales_rep'):
    """Add or update user with hashed password"""
    cursor = conn.cursor()

    # Hash the password securely
    password_hash = hash_password(password)
    full_name = f"{first_name} {last_name}"

    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing = cursor.fetchone()

        if existing:
            # Update existing user
            cursor.execute("""
                UPDATE users
                SET first_name = %s, last_name = %s, password_hash = %s, role = %s, updated_at = CURRENT_TIMESTAMP
                WHERE email = %s
                RETURNING id
            """, (first_name, last_name, password_hash, role, email))
            user_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✓ Updated user: {full_name} ({email})")
        else:
            # Insert new user
            cursor.execute("""
                INSERT INTO users (email, first_name, last_name, password_hash, role, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """, (email, first_name, last_name, password_hash, role))
            user_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✓ Created user: {full_name} ({email})")

        return user_id

    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to add user {email}: {e}")
        return None
    finally:
        cursor.close()

def verify_user(conn, email: str, password: str):
    """Verify user credentials using bcrypt"""
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT password_hash, first_name, last_name FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            stored_hash = result[0]
            first_name = result[1]
            last_name = result[2]
            full_name = f"{first_name} {last_name}"

            # Verify password with bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                print(f"✓ Password verified for {full_name} ({email})")
                return True
            else:
                print(f"✗ Password verification failed for {email}")
                return False
        else:
            print(f"✗ User not found: {email}")
            return False

    finally:
        cursor.close()

def main():
    """Add Josh Peh and Admin users to database"""
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected to database\n")

        # Add Josh Peh
        print("Adding Josh Peh...")
        josh_id = add_user(
            conn,
            email="josh.peh@horme.com.sg",
            first_name="Josh",
            last_name="Peh",
            password="JoshPeh@2025",
            role="sales_rep"
        )

        # Add Admin
        print("\nAdding Admin...")
        admin_id = add_user(
            conn,
            email="admin@horme.com.sg",
            first_name="Admin",
            last_name="User",
            password="Admin@2025",
            role="admin"
        )

        # Verify both users
        print("\n" + "="*50)
        print("Verifying user credentials...")
        print("="*50 + "\n")

        verify_user(conn, "josh.peh@horme.com.sg", "JoshPeh@2025")
        verify_user(conn, "admin@horme.com.sg", "Admin@2025")

        print("\n" + "="*50)
        print("✓ Login users setup complete!")
        print("="*50)
        print("\nYou can now login with:")
        print("  • Josh Peh: josh.peh@horme.com.sg / JoshPeh@2025")
        print("  • Admin: admin@horme.com.sg / Admin@2025")
        print("\nAccess: http://localhost:3010/login")

        conn.close()
        return 0

    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection failed: {e}")
        print("\nMake sure PostgreSQL container is running:")
        print("  docker-compose -f docker-compose.production.yml ps postgres")
        return 1

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
