#!/bin/bash
# ==============================================================================
# Generate Self-Signed SSL Certificates for Development
# ==============================================================================
# For production, use Let's Encrypt instead
# ==============================================================================

echo "Generating self-signed SSL certificates for development..."

# Create ssl directory
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=SG/ST=Singapore/L=Singapore/O=Job Pricing Engine/CN=localhost"

echo "✅ SSL certificates generated:"
echo "   - ssl/cert.pem (certificate)"
echo "   - ssl/key.pem (private key)"
echo ""
echo "⚠️  These are self-signed certificates for DEVELOPMENT only!"
echo "   For production, use Let's Encrypt or commercial certificates."
