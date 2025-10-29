# HashiCorp Vault Production Configuration for Horme POV
# Secure secrets management and encryption

# Storage backend - using integrated raft storage for production
storage "raft" {
  path    = "/vault/data"
  node_id = "vault-1"
}

# Listener configuration
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/tls/vault.crt"
  tls_key_file  = "/vault/tls/vault.key"
  
  # Security headers
  tls_min_version = "tls12"
  tls_cipher_suites = "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
  
  # Disable HTTP
  tls_disable = false
}

# API configuration
api_addr     = "https://vault.horme.local:8200"
cluster_addr = "https://vault.horme.local:8201"

# UI configuration
ui = true

# Logging
log_level = "INFO"
log_format = "json"

# Disable mlock in container environments
disable_mlock = true

# Performance and reliability
default_lease_ttl = "168h"    # 7 days
max_lease_ttl = "720h"        # 30 days

# Plugin directory
plugin_directory = "/vault/plugins"

# Entropy augmentation (for better random number generation)
entropy "seal" {
  mode = "augmentation"
}

# Auto-unseal using cloud KMS (configure based on cloud provider)
# For AWS
seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/vault-unseal-key"
}

# For development/testing - remove in production
# seal "shamir" {
#   key_shares    = 5
#   key_threshold = 3
# }

# Telemetry
telemetry {
  prometheus_enable = true
  disable_hostname  = false
}

# Administrative settings
raw_storage_endpoint = true
introspection_endpoint = true

# Cluster configuration
cluster_name = "horme-vault-cluster"