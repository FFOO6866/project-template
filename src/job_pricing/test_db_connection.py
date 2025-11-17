"""Quick database connection test"""
import sys
from sqlalchemy import text

try:
    from src.job_pricing.core.database import engine

    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print(f"Database connected: {result.scalar()}")

        # Check if users table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'users'
            )
        """))
        users_exists = result.scalar()
        print(f"Users table exists: {users_exists}")

    print("\n[OK] Database is accessible")
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR] Database connection failed: {e}")
    print("\nThis is expected if:")
    print("1. PostgreSQL is not running")
    print("2. Docker containers are not started")
    print("3. Database credentials are incorrect")
    sys.exit(1)
