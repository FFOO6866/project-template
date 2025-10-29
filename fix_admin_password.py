"""Fix admin password in database"""
import psycopg2
import bcrypt

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    port=5434,
    dbname='horme_db',
    user='horme_user',
    password='96831864edd3e18d5f9bd11089a5336a88ab9dec3cb87d42'
)

cursor = conn.cursor()

# Generate bcrypt hash for "admin123" (the password the frontend expects)
password = "admin123"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
correct_hash = password_hash.decode('utf-8')

print(f"Generating password hash for '{password}'...")
print(f"Hash: {correct_hash}")

cursor.execute(
    "UPDATE users SET password_hash = %s WHERE email = %s",
    (correct_hash, 'admin@yourdomain.com')
)

conn.commit()

# Verify the update
cursor.execute("SELECT password_hash FROM users WHERE email = 'admin@yourdomain.com'")
result = cursor.fetchone()
stored_hash = result[0]

# Test password verification
if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
    print(f"\n✓ Password verification successful!")
    print(f"✓ You can now login with: admin@yourdomain.com / {password}")
else:
    print(f"\n✗ Password verification FAILED!")

cursor.close()
conn.close()
print("\nAdmin password updated successfully!")
