#!/bin/bash
mkdir -p ssl

# Generate self-signed certificate for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048     -keyout ssl/ai-operations.key     -out ssl/ai-operations.crt     -subj "/C=US/ST=State/L=City/O=EnterpriseHub/CN=ai-operations.enterprisehub.local"

# Set proper permissions
chmod 600 ssl/ai-operations.key
chmod 644 ssl/ai-operations.crt

echo "SSL certificates generated in ssl/ directory"
echo "For production, replace with CA-signed certificates"
