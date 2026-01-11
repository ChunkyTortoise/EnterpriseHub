#!/bin/bash
# TLS Certificate Generation for Redis Cluster
# Enterprise-grade security for Phase 4 scaling

set -e

echo "🔐 Generating TLS Certificates for Redis Cluster..."

# Certificate directory
CERT_DIR="/Users/cave/enterprisehub/config/redis/tls"
mkdir -p "$CERT_DIR"

# Certificate configuration
CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"
REDIS_KEY="$CERT_DIR/redis.key"
REDIS_CSR="$CERT_DIR/redis.csr"
REDIS_CERT="$CERT_DIR/redis.crt"

# Certificate validity (1 year)
VALIDITY_DAYS=365

echo "📋 Creating CA certificate..."

# Generate CA private key
openssl genrsa -out "$CA_KEY" 4096

# Generate CA certificate
openssl req -new -x509 -days $VALIDITY_DAYS -key "$CA_KEY" -out "$CA_CERT" -subj "/C=US/ST=CA/L=San Francisco/O=EnterpriseHub/OU=Redis Cluster/CN=Redis-CA"

echo "🔑 Creating Redis server certificate..."

# Generate Redis private key
openssl genrsa -out "$REDIS_KEY" 4096

# Create certificate signing request with SAN
cat > "$CERT_DIR/redis.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = EnterpriseHub
OU = Redis Cluster
CN = redis-cluster

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = redis-master-1
DNS.2 = redis-master-2
DNS.3 = redis-master-3
DNS.4 = redis-replica-1
DNS.5 = redis-replica-2
DNS.6 = redis-replica-3
DNS.7 = redis-cluster-monitor
DNS.8 = localhost
IP.1 = 172.20.0.11
IP.2 = 172.20.0.12
IP.3 = 172.20.0.13
IP.4 = 172.20.0.21
IP.5 = 172.20.0.22
IP.6 = 172.20.0.23
IP.7 = 127.0.0.1
EOF

# Generate certificate signing request
openssl req -new -key "$REDIS_KEY" -out "$REDIS_CSR" -config "$CERT_DIR/redis.conf"

# Sign the certificate with CA
openssl x509 -req -in "$REDIS_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
    -out "$REDIS_CERT" -days $VALIDITY_DAYS -extensions v3_req -extfile "$CERT_DIR/redis.conf"

echo "🔒 Setting secure permissions..."

# Set secure permissions
chmod 600 "$CA_KEY" "$REDIS_KEY"
chmod 644 "$CA_CERT" "$REDIS_CERT"

echo "✅ Verifying certificates..."

# Verify certificate
openssl verify -CAfile "$CA_CERT" "$REDIS_CERT"

# Show certificate info
echo ""
echo "📋 Certificate Information:"
openssl x509 -in "$REDIS_CERT" -text -noout | grep -A 10 "Subject Alternative Name"

echo ""
echo "🎉 TLS certificates generated successfully!"
echo ""
echo "📁 Certificate files:"
echo "  CA Certificate: $CA_CERT"
echo "  CA Private Key: $CA_KEY (secure)"
echo "  Redis Certificate: $REDIS_CERT"
echo "  Redis Private Key: $REDIS_KEY (secure)"
echo ""
echo "🔧 Next steps:"
echo "  1. Copy certificates to Docker volume: redis_ssl_certs"
echo "  2. Update docker-compose.yml to mount certificates"
echo "  3. Start Redis cluster with TLS enabled"