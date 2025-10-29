#!/bin/bash
# ============================================================================
# UV Lock File Generator with Validation
# ============================================================================
#
# Generates uv.lock file from pyproject.toml and validates consistency
#
# Usage:
#   ./scripts/generate-uv-lock.sh           # Generate and validate
#   ./scripts/generate-uv-lock.sh --force   # Force regenerate
#   ./scripts/generate-uv-lock.sh --check   # Check only, no generation
#
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYPROJECT_FILE="${PROJECT_ROOT}/pyproject.toml"
LOCK_FILE="${PROJECT_ROOT}/uv.lock"

# Parse arguments
FORCE_REGENERATE=false
CHECK_ONLY=false

case "${1:-}" in
    --force)
        FORCE_REGENERATE=true
        ;;
    --check)
        CHECK_ONLY=true
        ;;
esac

# ============================================================================
# Validation Functions
# ============================================================================

check_uv_installed() {
    log_step "Checking UV installation..."

    if ! command -v uv &> /dev/null; then
        log_error "UV not installed!"
        log_info "Install UV with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        log_info "Then add to PATH and restart shell"
        return 1
    fi

    UV_VERSION=$(uv --version 2>&1 || echo "unknown")
    log_info "UV installed: ${UV_VERSION}"
    return 0
}

check_pyproject_exists() {
    log_step "Checking pyproject.toml..."

    if [ ! -f "${PYPROJECT_FILE}" ]; then
        log_error "pyproject.toml not found at ${PYPROJECT_FILE}"
        return 1
    fi

    log_info "Found pyproject.toml"
    return 0
}

validate_pyproject() {
    log_step "Validating pyproject.toml syntax..."

    # Check if file is valid TOML
    if ! python3 -c "import tomli; tomli.load(open('${PYPROJECT_FILE}', 'rb'))" 2>/dev/null; then
        # Try with toml library as fallback
        if ! python3 -c "import toml; toml.load('${PYPROJECT_FILE}')" 2>/dev/null; then
            log_error "pyproject.toml has invalid TOML syntax"
            return 1
        fi
    fi

    log_info "pyproject.toml syntax is valid"
    return 0
}

check_lock_file_exists() {
    if [ -f "${LOCK_FILE}" ]; then
        log_info "uv.lock exists"
        return 0
    else
        log_warn "uv.lock does not exist"
        return 1
    fi
}

generate_lock_file() {
    log_step "Generating uv.lock from pyproject.toml..."

    cd "${PROJECT_ROOT}"

    # Generate lock file
    if uv lock; then
        log_info "✅ uv.lock generated successfully"
        return 0
    else
        log_error "Failed to generate uv.lock"
        return 1
    fi
}

validate_lock_file() {
    log_step "Validating uv.lock consistency with pyproject.toml..."

    cd "${PROJECT_ROOT}"

    # Check if lock file is in sync with pyproject.toml
    if uv lock --check 2>&1 | grep -q "up-to-date"; then
        log_info "✅ uv.lock is consistent with pyproject.toml"
        return 0
    else
        log_warn "⚠️  uv.lock may be out of sync with pyproject.toml"
        log_info "Run './scripts/generate-uv-lock.sh --force' to regenerate"
        return 1
    fi
}

check_version_conflicts() {
    log_step "Checking for dependency version conflicts..."

    cd "${PROJECT_ROOT}"

    # UV automatically resolves conflicts, but let's verify
    if uv lock --dry-run 2>&1 | grep -i "conflict"; then
        log_error "Version conflicts detected!"
        uv lock --dry-run
        return 1
    else
        log_info "✅ No version conflicts detected"
        return 0
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

log_info "🚀 UV Lock File Generator"
log_info "Project: ${PROJECT_ROOT}"
echo ""

# Step 1: Check UV installed
if ! check_uv_installed; then
    exit 1
fi
echo ""

# Step 2: Check pyproject.toml exists
if ! check_pyproject_exists; then
    exit 1
fi

# Step 3: Validate pyproject.toml
if ! validate_pyproject; then
    exit 1
fi
echo ""

# Step 4: Handle different modes
if [ "${CHECK_ONLY}" = true ]; then
    log_info "📋 Check-only mode"

    if check_lock_file_exists; then
        validate_lock_file
        check_version_conflicts
    else
        log_error "uv.lock does not exist"
        log_info "Run './scripts/generate-uv-lock.sh' to generate"
        exit 1
    fi

elif [ "${FORCE_REGENERATE}" = true ]; then
    log_info "🔄 Force regenerate mode"

    if [ -f "${LOCK_FILE}" ]; then
        log_warn "Removing existing uv.lock"
        rm "${LOCK_FILE}"
    fi

    generate_lock_file
    validate_lock_file
    check_version_conflicts

else
    log_info "📦 Normal mode"

    if check_lock_file_exists; then
        log_info "uv.lock already exists"

        if ! validate_lock_file; then
            log_warn "uv.lock is out of sync"
            log_info "Regenerating uv.lock..."
            generate_lock_file
        fi
    else
        log_info "uv.lock does not exist, generating..."
        generate_lock_file
    fi

    check_version_conflicts
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
log_info "✅ UV lock file validation complete!"
echo ""

if [ -f "${LOCK_FILE}" ]; then
    LOCK_SIZE=$(stat -c%s "${LOCK_FILE}" 2>/dev/null || stat -f%z "${LOCK_FILE}" 2>/dev/null || echo "unknown")
    NUM_PACKAGES=$(grep -c "name = " "${LOCK_FILE}" 2>/dev/null || echo "unknown")

    log_info "Lock file details:"
    log_info "  Location: ${LOCK_FILE}"
    log_info "  Size: ${LOCK_SIZE} bytes"
    log_info "  Packages: ${NUM_PACKAGES}"
    echo ""

    log_info "Next steps:"
    log_info "  1. Review uv.lock file"
    log_info "  2. Commit to git: git add uv.lock pyproject.toml"
    log_info "  3. Test build: ./scripts/local-uv-dev.sh"
    log_info "  4. Deploy: ./scripts/deploy-cloud-uv.sh"
else
    log_error "uv.lock was not created!"
    exit 1
fi

log_info "🎉 Done!"
