#!/usr/bin/env python3
"""
Production Credentials Generator
Generates secure random credentials for production deployment
"""

import secrets
import bcrypt
import sys
from pathlib import Path

def generate_secure_token(bytes_length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_hex(bytes_length)

def generate_secure_password(length: int = 32) -> str:
    """Generate a secure URL-safe password"""
    return secrets.token_urlsafe(length)

def hash_password(password: str) -> str:
    """Generate bcrypt hash for a password"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def generate_all_credentials():
    """Generate all required production credentials"""

    print("=" * 80)
    print("HORME POV PRODUCTION CREDENTIALS GENERATOR")
    print("=" * 80)
    print()
    print("⚠️  SECURITY WARNING:")
    print("   - Store these credentials securely")
    print("   - Never commit these to Git")
    print("   - Use a secrets manager in production (AWS Secrets Manager, etc.)")
    print("   - Rotate these credentials every 90 days")
    print()
    print("=" * 80)
    print()

    # Generate JWT and application secrets
    jwt_secret = generate_secure_token(32)
    secret_key = generate_secure_token(32)

    # Generate database credentials
    db_password = generate_secure_token(24)
    redis_password = generate_secure_token(24)
    neo4j_password = generate_secure_token(24)

    # Generate admin password
    admin_password = generate_secure_password(32)
    admin_password_hash = hash_password(admin_password)

    # Print credentials in .env format
    print("# =============================================================================")
    print("# GENERATED PRODUCTION CREDENTIALS")
    print(f"# Generated: {Path(__file__).stat().st_mtime}")
    print("# =============================================================================")
    print()
    print("# Copy these to your .env.production file")
    print()
    print("# JWT & Application Secrets (32 bytes each)")
    print(f"JWT_SECRET={jwt_secret}")
    print(f"NEXUS_JWT_SECRET={jwt_secret}")
    print(f"SECRET_KEY={secret_key}")
    print(f"API_SECRET_KEY={secret_key}")
    print()
    print("# Database Passwords (24 bytes each)")
    print(f"POSTGRES_PASSWORD={db_password}")
    print(f"REDIS_PASSWORD={redis_password}")
    print(f"NEO4J_PASSWORD={neo4j_password}")
    print()
    print("# Admin User Credentials")
    print(f"ADMIN_EMAIL=admin@yourdomain.com")
    print(f"ADMIN_PASSWORD={admin_password}")
    print(f"ADMIN_PASSWORD_HASH={admin_password_hash}")
    print()
    print("# Database URLs (update with your credentials)")
    print(f"DATABASE_URL=postgresql://horme_user:{db_password}@postgres:5432/horme_db")
    print(f"REDIS_URL=redis://:{redis_password}@redis:6379/0")
    print(f"NEO4J_URI=bolt://neo4j:{neo4j_password}@neo4j:7687")
    print()
    print("=" * 80)
    print()
    print("✅ CREDENTIALS GENERATED SUCCESSFULLY")
    print()
    print("📋 NEXT STEPS:")
    print("   1. Copy these credentials to your .env.production file")
    print("   2. Update ADMIN_EMAIL to your actual admin email")
    print("   3. Update CORS_ORIGINS with your production domain(s)")
    print("   4. Test with: python scripts/validate_production_config.py")
    print("   5. Store credentials in your secrets manager")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Save the ADMIN_PASSWORD securely (you'll need it to login)")
    print("   - DO NOT share these credentials via email or chat")
    print("   - DO NOT commit .env.production to Git (it's in .gitignore)")
    print()
    print("=" * 80)

    # Also save to a secure file
    output_file = Path(__file__).parent.parent / ".credentials.generated"
    with open(output_file, 'w') as f:
        f.write(f"JWT_SECRET={jwt_secret}\n")
        f.write(f"NEXUS_JWT_SECRET={jwt_secret}\n")
        f.write(f"SECRET_KEY={secret_key}\n")
        f.write(f"API_SECRET_KEY={secret_key}\n")
        f.write(f"POSTGRES_PASSWORD={db_password}\n")
        f.write(f"REDIS_PASSWORD={redis_password}\n")
        f.write(f"NEO4J_PASSWORD={neo4j_password}\n")
        f.write(f"ADMIN_EMAIL=admin@yourdomain.com\n")
        f.write(f"ADMIN_PASSWORD={admin_password}\n")
        f.write(f"ADMIN_PASSWORD_HASH={admin_password_hash}\n")
        f.write(f"DATABASE_URL=postgresql://horme_user:{db_password}@postgres:5432/horme_db\n")
        f.write(f"REDIS_URL=redis://:{redis_password}@redis:6379/0\n")
        f.write(f"NEO4J_URI=bolt://neo4j:{neo4j_password}@neo4j:7687\n")

    print(f"💾 Credentials also saved to: {output_file}")
    print(f"   (This file is in .gitignore for security)")
    print()

if __name__ == "__main__":
    try:
        generate_all_credentials()
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)
