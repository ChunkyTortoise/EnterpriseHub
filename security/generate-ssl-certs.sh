#!/bin/bash
# ==============================================================================
# JORGE'S BI DASHBOARD - SSL CERTIFICATE GENERATION SCRIPT
# Production-grade SSL/TLS certificate setup
# ==============================================================================

set -e

# Configuration
CERT_DIR="/etc/nginx/ssl"
DOMAIN="bi.jorge-platform.com"
ALT_DOMAINS="dashboard.jorge-platform.com"
COUNTRY="US"
STATE="California"
CITY="Rancho Cucamonga"
ORG="Jorge Real Estate AI"
ORG_UNIT="Business Intelligence"
EMAIL="ssl@jorge-platform.com"
KEY_SIZE=4096
DAYS_VALID=365

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# CERTIFICATE GENERATION FUNCTIONS
# ==============================================================================

create_cert_directory() {
    log_info "Creating SSL certificate directory..."

    if [[ ! -d "$CERT_DIR" ]]; then
        sudo mkdir -p "$CERT_DIR"
        sudo chmod 755 "$CERT_DIR"
        log_success "Created certificate directory: $CERT_DIR"
    else
        log_info "Certificate directory already exists: $CERT_DIR"
    fi
}

generate_private_key() {
    log_info "Generating ${KEY_SIZE}-bit RSA private key..."

    sudo openssl genrsa -out "$CERT_DIR/jorge-bi.key" $KEY_SIZE

    if [[ $? -eq 0 ]]; then
        sudo chmod 600 "$CERT_DIR/jorge-bi.key"
        sudo chown root:root "$CERT_DIR/jorge-bi.key"
        log_success "Private key generated: jorge-bi.key"
    else
        log_error "Failed to generate private key"
        exit 1
    fi
}

create_openssl_config() {
    log_info "Creating OpenSSL configuration file..."

    cat > /tmp/jorge-bi.conf << EOF
[req]
default_bits = $KEY_SIZE
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=$COUNTRY
ST=$STATE
L=$CITY
O=$ORG
OU=$ORG_UNIT
CN=$DOMAIN
emailAddress=$EMAIL

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = $ALT_DOMAINS
DNS.3 = *.jorge-platform.com
DNS.4 = localhost
IP.1 = 127.0.0.1
EOF

    log_success "OpenSSL configuration created"
}

generate_csr() {
    log_info "Generating Certificate Signing Request (CSR)..."

    sudo openssl req -new \
        -key "$CERT_DIR/jorge-bi.key" \
        -out "$CERT_DIR/jorge-bi.csr" \
        -config /tmp/jorge-bi.conf

    if [[ $? -eq 0 ]]; then
        sudo chmod 644 "$CERT_DIR/jorge-bi.csr"
        log_success "CSR generated: jorge-bi.csr"
    else
        log_error "Failed to generate CSR"
        exit 1
    fi
}

generate_self_signed_cert() {
    log_info "Generating self-signed certificate (valid for $DAYS_VALID days)..."

    sudo openssl x509 -req \
        -in "$CERT_DIR/jorge-bi.csr" \
        -signkey "$CERT_DIR/jorge-bi.key" \
        -out "$CERT_DIR/jorge-bi.crt" \
        -days $DAYS_VALID \
        -extensions v3_req \
        -extfile /tmp/jorge-bi.conf

    if [[ $? -eq 0 ]]; then
        sudo chmod 644 "$CERT_DIR/jorge-bi.crt"
        log_success "Self-signed certificate generated: jorge-bi.crt"
    else
        log_error "Failed to generate self-signed certificate"
        exit 1
    fi
}

generate_chain_file() {
    log_info "Creating certificate chain file..."

    # For self-signed, chain is just the certificate itself
    sudo cp "$CERT_DIR/jorge-bi.crt" "$CERT_DIR/jorge-bi-chain.crt"
    sudo chmod 644 "$CERT_DIR/jorge-bi-chain.crt"

    log_success "Certificate chain created: jorge-bi-chain.crt"
}

generate_dhparam() {
    log_info "Generating Diffie-Hellman parameters (this may take a while)..."

    sudo openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

    if [[ $? -eq 0 ]]; then
        sudo chmod 644 "$CERT_DIR/dhparam.pem"
        log_success "DH parameters generated: dhparam.pem"
    else
        log_error "Failed to generate DH parameters"
        exit 1
    fi
}

generate_default_cert() {
    log_info "Generating default server certificate..."

    # Generate key for default server
    sudo openssl genrsa -out "$CERT_DIR/default.key" 2048
    sudo chmod 600 "$CERT_DIR/default.key"

    # Generate self-signed cert for default server
    sudo openssl req -new -x509 \
        -key "$CERT_DIR/default.key" \
        -out "$CERT_DIR/default.crt" \
        -days 30 \
        -subj "/C=US/ST=State/L=City/O=Default/OU=Default/CN=default"

    sudo chmod 644 "$CERT_DIR/default.crt"
    log_success "Default server certificate generated"
}

verify_certificates() {
    log_info "Verifying generated certificates..."

    # Verify private key
    if sudo openssl rsa -in "$CERT_DIR/jorge-bi.key" -check -noout; then
        log_success "Private key is valid"
    else
        log_error "Private key verification failed"
        exit 1
    fi

    # Verify certificate
    if sudo openssl x509 -in "$CERT_DIR/jorge-bi.crt" -text -noout > /dev/null; then
        log_success "Certificate is valid"
    else
        log_error "Certificate verification failed"
        exit 1
    fi

    # Verify key and certificate match
    key_md5=$(sudo openssl rsa -noout -modulus -in "$CERT_DIR/jorge-bi.key" | openssl md5)
    cert_md5=$(sudo openssl x509 -noout -modulus -in "$CERT_DIR/jorge-bi.crt" | openssl md5)

    if [[ "$key_md5" == "$cert_md5" ]]; then
        log_success "Private key and certificate match"
    else
        log_error "Private key and certificate do not match"
        exit 1
    fi
}

display_certificate_info() {
    log_info "Certificate Information:"
    echo

    # Display certificate details
    sudo openssl x509 -in "$CERT_DIR/jorge-bi.crt" -text -noout | head -20

    echo
    log_info "Certificate validity:"
    sudo openssl x509 -in "$CERT_DIR/jorge-bi.crt" -noout -dates

    echo
    log_info "Certificate subject alternative names:"
    sudo openssl x509 -in "$CERT_DIR/jorge-bi.crt" -noout -ext subjectAltName
}

create_renewal_script() {
    log_info "Creating certificate renewal script..."

    cat > /tmp/renew-jorge-bi-certs.sh << 'EOF'
#!/bin/bash
# Auto-generated certificate renewal script for Jorge BI Dashboard

CERT_DIR="/etc/nginx/ssl"
BACKUP_DIR="/etc/nginx/ssl/backup"
DATE=$(date +%Y%m%d)

# Create backup
mkdir -p "$BACKUP_DIR"
cp "$CERT_DIR/jorge-bi.crt" "$BACKUP_DIR/jorge-bi.crt.$DATE"
cp "$CERT_DIR/jorge-bi.key" "$BACKUP_DIR/jorge-bi.key.$DATE"

# Check if certificate expires in 30 days
if openssl x509 -checkend 2592000 -noout -in "$CERT_DIR/jorge-bi.crt"; then
    echo "Certificate is still valid for more than 30 days"
    exit 0
else
    echo "Certificate expires within 30 days - renewal recommended"
    # Add actual renewal logic here (Let's Encrypt, etc.)
fi
EOF

    sudo mv /tmp/renew-jorge-bi-certs.sh "$CERT_DIR/renew-certs.sh"
    sudo chmod +x "$CERT_DIR/renew-certs.sh"

    log_success "Renewal script created: $CERT_DIR/renew-certs.sh"
}

setup_file_permissions() {
    log_info "Setting proper file permissions..."

    # Set ownership to root
    sudo chown -R root:root "$CERT_DIR"

    # Set permissions
    sudo chmod 755 "$CERT_DIR"
    sudo chmod 600 "$CERT_DIR"/*.key
    sudo chmod 644 "$CERT_DIR"/*.crt
    sudo chmod 644 "$CERT_DIR"/*.csr
    sudo chmod 644 "$CERT_DIR"/*.pem

    log_success "File permissions set correctly"
}

cleanup_temp_files() {
    log_info "Cleaning up temporary files..."

    rm -f /tmp/jorge-bi.conf

    log_success "Cleanup completed"
}

# ==============================================================================
# LET'S ENCRYPT INTEGRATION (OPTIONAL)
# ==============================================================================

install_certbot() {
    log_info "Installing Certbot for Let's Encrypt integration..."

    if command -v certbot &> /dev/null; then
        log_info "Certbot already installed"
        return 0
    fi

    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot python3-certbot-nginx
    else
        log_warn "Could not install Certbot automatically"
        return 1
    fi

    if command -v certbot &> /dev/null; then
        log_success "Certbot installed successfully"
    else
        log_error "Certbot installation failed"
        return 1
    fi
}

setup_letsencrypt() {
    log_info "Setting up Let's Encrypt certificates..."

    if ! command -v certbot &> /dev/null; then
        log_error "Certbot not installed. Run with --install-certbot first"
        return 1
    fi

    log_warn "This will attempt to obtain real SSL certificates from Let's Encrypt"
    log_warn "Make sure your domains are pointing to this server"
    read -p "Continue? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo certbot certonly --nginx \
            -d "$DOMAIN" \
            -d "$ALT_DOMAINS" \
            --email "$EMAIL" \
            --agree-tos \
            --non-interactive

        if [[ $? -eq 0 ]]; then
            # Link Let's Encrypt certificates to our expected paths
            sudo ln -sf "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/jorge-bi.crt"
            sudo ln -sf "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/jorge-bi.key"
            sudo ln -sf "/etc/letsencrypt/live/$DOMAIN/chain.pem" "$CERT_DIR/jorge-bi-chain.crt"

            log_success "Let's Encrypt certificates installed and linked"
        else
            log_error "Let's Encrypt certificate generation failed"
            return 1
        fi
    else
        log_info "Let's Encrypt setup cancelled"
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

show_help() {
    echo "Jorge BI Dashboard SSL Certificate Generator"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help                Show this help message"
    echo "  --self-signed        Generate self-signed certificates (default)"
    echo "  --letsencrypt        Set up Let's Encrypt certificates"
    echo "  --install-certbot    Install Certbot for Let's Encrypt"
    echo "  --verify-only        Only verify existing certificates"
    echo "  --renew              Renew existing certificates"
    echo
    echo "Examples:"
    echo "  $0                   # Generate self-signed certificates"
    echo "  $0 --letsencrypt    # Set up Let's Encrypt certificates"
    echo "  $0 --verify-only    # Verify existing certificates"
}

main() {
    log_info "🔐 Jorge's BI Dashboard SSL Certificate Setup"
    log_info "Domain: $DOMAIN"
    log_info "Alternative domains: $ALT_DOMAINS"
    echo

    case "${1:-self-signed}" in
        "--help")
            show_help
            exit 0
            ;;
        "--verify-only")
            if [[ -f "$CERT_DIR/jorge-bi.crt" && -f "$CERT_DIR/jorge-bi.key" ]]; then
                verify_certificates
                display_certificate_info
            else
                log_error "Certificates not found. Generate them first."
                exit 1
            fi
            ;;
        "--install-certbot")
            install_certbot
            ;;
        "--letsencrypt")
            create_cert_directory
            setup_letsencrypt
            ;;
        "--self-signed"|"")
            create_cert_directory
            generate_private_key
            create_openssl_config
            generate_csr
            generate_self_signed_cert
            generate_chain_file
            generate_dhparam
            generate_default_cert
            verify_certificates
            display_certificate_info
            create_renewal_script
            setup_file_permissions
            cleanup_temp_files

            echo
            log_success "🎉 SSL certificates generated successfully!"
            log_info "Certificates are located in: $CERT_DIR"
            log_info "Don't forget to restart Nginx: sudo systemctl reload nginx"
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Check if running as root or with sudo
if [[ $EUID -ne 0 && -z "$SUDO_USER" ]]; then
    log_error "This script must be run as root or with sudo"
    exit 1
fi

# Execute main function
main "$@"