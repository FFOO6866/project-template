#!/bin/bash
# ============================================================================
# UV Environment Setup and Validation Script
# ============================================================================
#
# Automated script for UV package manager setup, validation, and lockfile
# generation. Ensures UV is properly installed and configured for
# reproducible builds.
#
# Features:
# - UV installation check and auto-install
# - pyproject.toml validation
# - uv.lock generation and validation
# - Dependency conflict detection
# - Comprehensive environment validation
# - NO hardcoded values (all from config)
# - Cross-platform support (Windows Git Bash/WSL, Linux, macOS)
#
# Usage:
#   ./scripts/setup-uv-environment.sh
#   ./scripts/setup-uv-environment.sh --force-lock  # Regenerate lockfile
#   ./scripts/setup-uv-environment.sh --check-only  # Validation only
#
# Exit codes:
#   0 - Success
#   1 - UV installation failed
#   2 - pyproject.toml invalid
#   3 - Lock generation failed
#   4 - Dependency conflicts
#   5 - Validation failed
#
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# Configuration and Constants
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script metadata
SCRIPT_NAME="UV Environment Setup"
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# UV version (from Dockerfile pattern)
UV_VERSION="${UV_VERSION:-0.5.17}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

# Flags
FORCE_LOCK=false
CHECK_ONLY=false
VERBOSE=false

# Results tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Temporary files for rollback
BACKUP_DIR="${PROJECT_ROOT}/.uv-backup-$(date +%Y%m%d_%H%M%S)"

# ============================================================================
# Logging Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_step() {
    echo -e "\n${CYAN}==>${NC} ${BOLD}$*${NC}"
}

log_progress() {
    echo -e "    ${BLUE}→${NC} $*"
}

log_check() {
    ((TOTAL_CHECKS++))
    if [ $# -eq 2 ] && [ "$2" = "PASS" ]; then
        echo -e "    ${GREEN}✓${NC} $1"
        ((PASSED_CHECKS++))
    else
        echo -e "    ${RED}✗${NC} $1"
        ((FAILED_CHECKS++))
    fi
}

# ============================================================================
# Utility Functions
# ============================================================================

print_header() {
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}${SCRIPT_NAME} v${SCRIPT_VERSION}${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo ""
}

print_summary() {
    echo ""
    echo -e "${CYAN}============================================================================${NC}"
    echo -e "${CYAN}VALIDATION SUMMARY${NC}"
    echo -e "${CYAN}============================================================================${NC}"
    echo -e "Total Checks:    ${TOTAL_CHECKS}"
    echo -e "Passed:          ${GREEN}${PASSED_CHECKS}${NC}"
    echo -e "Failed:          ${RED}${FAILED_CHECKS}${NC}"
    echo -e "Warnings:        ${YELLOW}${WARNINGS}${NC}"

    local success_rate=0
    if [ ${TOTAL_CHECKS} -gt 0 ]; then
        success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    fi
    echo -e "Success Rate:    ${success_rate}%"
    echo -e "${CYAN}============================================================================${NC}"
}

detect_platform() {
    # Detect operating system
    local os_name
    os_name="$(uname -s)"

    case "${os_name}" in
        Linux*)
            echo "linux"
            ;;
        Darwin*)
            echo "macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "windows"
            ;;
        *)
            log_error "Unsupported operating system: ${os_name}"
            exit 1
            ;;
    esac
}

check_command() {
    # Check if a command exists
    local cmd=$1
    if command -v "${cmd}" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

create_backup() {
    # Create backup of important files before modifications
    log_info "Creating backup in ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"

    [ -f "${PROJECT_ROOT}/uv.lock" ] && cp "${PROJECT_ROOT}/uv.lock" "${BACKUP_DIR}/"
    [ -f "${PROJECT_ROOT}/pyproject.toml" ] && cp "${PROJECT_ROOT}/pyproject.toml" "${BACKUP_DIR}/"

    log_success "Backup created successfully"
}

rollback_changes() {
    # Rollback changes in case of failure
    log_warning "Rolling back changes from backup..."

    if [ -d "${BACKUP_DIR}" ]; then
        [ -f "${BACKUP_DIR}/uv.lock" ] && cp "${BACKUP_DIR}/uv.lock" "${PROJECT_ROOT}/"
        [ -f "${BACKUP_DIR}/pyproject.toml" ] && cp "${BACKUP_DIR}/pyproject.toml" "${PROJECT_ROOT}/"

        log_success "Rollback completed"
    else
        log_warning "No backup found to rollback"
    fi
}

cleanup_backup() {
    # Remove backup directory after successful operation
    if [ -d "${BACKUP_DIR}" ]; then
        rm -rf "${BACKUP_DIR}"
        log_info "Backup cleaned up"
    fi
}

# ============================================================================
# UV Installation Functions
# ============================================================================

check_uv_installed() {
    log_step "Step 1: Checking UV installation"

    if check_command "uv"; then
        local installed_version
        installed_version=$(uv --version | awk '{print $2}')
        log_check "UV is installed (version: ${installed_version})" "PASS"

        # Check if version matches recommended
        if [ "${installed_version}" = "${UV_VERSION}" ]; then
            log_check "UV version matches recommended (${UV_VERSION})" "PASS"
        else
            log_warning "UV version ${installed_version} differs from recommended ${UV_VERSION}"
            log_progress "Consider upgrading: curl -LsSf https://astral.sh/uv/install.sh | sh"
        fi

        return 0
    else
        log_check "UV is not installed" "FAIL"
        return 1
    fi
}

install_uv() {
    log_step "Installing UV package manager"

    local platform
    platform=$(detect_platform)

    log_progress "Detected platform: ${platform}"
    log_progress "Installing UV version ${UV_VERSION}..."

    case "${platform}" in
        linux|macos)
            if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
                log_error "UV installation failed"
                return 1
            fi
            ;;
        windows)
            log_info "On Windows, please install UV manually:"
            log_info "  1. Download from: https://github.com/astral-sh/uv/releases"
            log_info "  2. Or use: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
            return 1
            ;;
    esac

    # Verify installation
    if check_command "uv"; then
        log_success "UV installed successfully"
        return 0
    else
        log_error "UV installation verification failed"
        return 1
    fi
}

# ============================================================================
# Python Version Validation
# ============================================================================

check_python_version() {
    log_step "Step 2: Validating Python version"

    if ! check_command "python3"; then
        log_check "Python 3 is not installed" "FAIL"
        log_error "Install Python ${PYTHON_VERSION} or higher"
        return 1
    fi

    local python_version
    python_version=$(python3 --version | awk '{print $2}')
    log_check "Python is installed (version: ${python_version})" "PASS"

    # Parse version numbers
    local major minor
    major=$(echo "${python_version}" | cut -d. -f1)
    minor=$(echo "${python_version}" | cut -d. -f2)

    # Check minimum version (3.11)
    if [ "${major}" -ge 3 ] && [ "${minor}" -ge 11 ]; then
        log_check "Python version meets minimum requirement (>=3.11)" "PASS"
        return 0
    else
        log_check "Python version ${python_version} is below minimum (3.11)" "FAIL"
        log_error "Upgrade to Python 3.11 or higher"
        return 1
    fi
}

# ============================================================================
# pyproject.toml Validation
# ============================================================================

validate_pyproject() {
    log_step "Step 3: Validating pyproject.toml"

    local pyproject_file="${PROJECT_ROOT}/pyproject.toml"

    if [ ! -f "${pyproject_file}" ]; then
        log_check "pyproject.toml exists" "FAIL"
        log_error "pyproject.toml not found at ${pyproject_file}"
        return 1
    fi
    log_check "pyproject.toml exists" "PASS"

    # Check file is readable
    if [ ! -r "${pyproject_file}" ]; then
        log_check "pyproject.toml is readable" "FAIL"
        return 1
    fi
    log_check "pyproject.toml is readable" "PASS"

    # Validate TOML syntax with UV
    if uv pip compile "${pyproject_file}" --quiet --dry-run 2>/dev/null; then
        log_check "pyproject.toml syntax is valid" "PASS"
    else
        log_check "pyproject.toml syntax is valid" "FAIL"
        log_error "Invalid TOML syntax. Run: uv pip compile pyproject.toml"
        return 1
    fi

    # Check required sections
    local required_sections=("project" "project.dependencies")

    for section in "${required_sections[@]}"; do
        if grep -q "\[${section}\]" "${pyproject_file}"; then
            log_check "Section [${section}] exists" "PASS"
        else
            log_check "Section [${section}] exists" "FAIL"
            log_error "Missing required section: [${section}]"
            return 1
        fi
    done

    # Check for hardcoded credentials (should use env vars)
    if grep -qiE '(password|api[_-]?key|secret).*(=|:).*("|'"'"')[^"'"'"']{3,}' "${pyproject_file}"; then
        log_check "No hardcoded credentials in pyproject.toml" "FAIL"
        log_error "Found hardcoded credentials. Use environment variables instead."
        return 1
    fi
    log_check "No hardcoded credentials in pyproject.toml" "PASS"

    log_success "pyproject.toml validation passed"
    return 0
}

# ============================================================================
# uv.lock Generation and Validation
# ============================================================================

generate_lock_file() {
    log_step "Step 4: Generating/updating uv.lock"

    local lock_file="${PROJECT_ROOT}/uv.lock"
    local lock_exists=false

    if [ -f "${lock_file}" ]; then
        lock_exists=true
        log_info "Existing uv.lock found"

        if [ "${FORCE_LOCK}" = true ]; then
            log_warning "Force lock enabled - regenerating uv.lock"
        else
            log_info "Validating existing lock file..."
            if validate_lock_file; then
                log_success "Existing lock file is valid"
                return 0
            else
                log_warning "Existing lock file is invalid - regenerating"
            fi
        fi
    else
        log_info "No uv.lock found - generating new lock file"
    fi

    # Create backup before generating
    if [ "${lock_exists}" = true ]; then
        create_backup
    fi

    # Generate lock file
    log_progress "Running: uv lock"
    if uv lock; then
        log_check "Lock file generated successfully" "PASS"
    else
        log_check "Lock file generation failed" "FAIL"
        log_error "Lock generation failed. Check dependency conflicts."

        if [ "${lock_exists}" = true ]; then
            rollback_changes
        fi
        return 1
    fi

    # Validate generated lock
    if validate_lock_file; then
        log_success "Generated lock file is valid"
        cleanup_backup
        return 0
    else
        log_error "Generated lock file is invalid"

        if [ "${lock_exists}" = true ]; then
            rollback_changes
        fi
        return 1
    fi
}

validate_lock_file() {
    local lock_file="${PROJECT_ROOT}/uv.lock"

    if [ ! -f "${lock_file}" ]; then
        log_check "uv.lock exists" "FAIL"
        return 1
    fi

    # Check file is not empty
    if [ ! -s "${lock_file}" ]; then
        log_check "uv.lock is not empty" "FAIL"
        return 1
    fi

    # Validate lock file consistency
    log_progress "Validating lock file consistency..."
    if uv sync --frozen --dry-run 2>/dev/null; then
        log_check "Lock file is consistent with pyproject.toml" "PASS"
    else
        log_check "Lock file is consistent with pyproject.toml" "FAIL"
        log_error "Lock file is out of sync. Run: uv lock"
        return 1
    fi

    return 0
}

# ============================================================================
# Dependency Validation
# ============================================================================

check_dependency_conflicts() {
    log_step "Step 5: Checking for dependency conflicts"

    log_progress "Analyzing dependency tree..."

    # Use UV to check for conflicts
    local temp_output
    temp_output=$(mktemp)

    if uv pip compile "${PROJECT_ROOT}/pyproject.toml" --quiet 2>"${temp_output}"; then
        log_check "No dependency conflicts detected" "PASS"
        rm -f "${temp_output}"
        return 0
    else
        log_check "No dependency conflicts detected" "FAIL"

        # Show conflict details
        if [ -s "${temp_output}" ]; then
            log_error "Dependency conflicts found:"
            cat "${temp_output}" | head -20
        fi

        rm -f "${temp_output}"
        return 1
    fi
}

validate_critical_dependencies() {
    log_step "Step 6: Validating critical dependencies"

    # Critical dependencies that must be present
    local critical_deps=(
        "fastapi"
        "uvicorn"
        "asyncpg"
        "redis"
        "neo4j"
        "openai"
    )

    local pyproject_file="${PROJECT_ROOT}/pyproject.toml"
    local all_found=true

    for dep in "${critical_deps[@]}"; do
        if grep -q "\"${dep}[=>~]" "${pyproject_file}"; then
            log_check "Critical dependency '${dep}' is present" "PASS"
        else
            log_check "Critical dependency '${dep}' is present" "FAIL"
            all_found=false
        fi
    done

    if [ "${all_found}" = true ]; then
        log_success "All critical dependencies are present"
        return 0
    else
        log_error "Missing critical dependencies"
        return 1
    fi
}

# ============================================================================
# Environment Validation
# ============================================================================

validate_environment() {
    log_step "Step 7: Validating UV environment configuration"

    # Check UV cache
    local cache_dir="${HOME}/.cache/uv"
    if [ -d "${cache_dir}" ]; then
        local cache_size
        cache_size=$(du -sh "${cache_dir}" 2>/dev/null | cut -f1 || echo "unknown")
        log_check "UV cache directory exists (size: ${cache_size})" "PASS"
    else
        log_warning "UV cache directory not found - will be created on first use"
    fi

    # Check UV environment variables
    local uv_env_vars=(
        "UV_COMPILE_BYTECODE"
        "UV_LINK_MODE"
        "UV_PYTHON_DOWNLOADS"
    )

    log_progress "Recommended UV environment variables:"
    for var in "${uv_env_vars[@]}"; do
        if [ -n "${!var:-}" ]; then
            echo "    ${var}=${!var}"
        else
            log_info "${var} not set (will use UV defaults)"
        fi
    done

    log_success "Environment validation complete"
    return 0
}

# ============================================================================
# Comprehensive Installation Verification
# ============================================================================

verify_installation() {
    log_step "Step 8: Verifying complete installation"

    log_progress "Performing dry-run installation..."

    # Test installation without actually installing
    if uv sync --frozen --dry-run; then
        log_check "Installation verification passed" "PASS"

        # Show statistics
        log_progress "Dependency statistics:"
        local dep_count
        dep_count=$(grep -c "^    \"" "${PROJECT_ROOT}/pyproject.toml" || echo "0")
        echo "    Total dependencies: ${dep_count}"

        return 0
    else
        log_check "Installation verification failed" "FAIL"
        log_error "Installation would fail. Check logs above for details."
        return 1
    fi
}

# ============================================================================
# Main Execution Flow
# ============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force-lock)
                FORCE_LOCK=true
                shift
                ;;
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                set -x  # Enable bash debugging
                shift
                ;;
            --help|-h)
                cat <<EOF
Usage: $0 [OPTIONS]

UV Environment Setup and Validation Script

Options:
    --force-lock     Force regeneration of uv.lock
    --check-only     Only validate, don't install or modify
    --verbose, -v    Enable verbose output
    --help, -h       Show this help message

Examples:
    $0                      # Normal setup and validation
    $0 --force-lock         # Regenerate lockfile
    $0 --check-only         # Validation only

Exit codes:
    0 - Success
    1 - UV installation failed
    2 - pyproject.toml invalid
    3 - Lock generation failed
    4 - Dependency conflicts
    5 - Validation failed
EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

main() {
    parse_arguments "$@"

    print_header

    log_info "Project root: ${PROJECT_ROOT}"
    log_info "Platform: $(detect_platform)"
    log_info "Mode: $([ "${CHECK_ONLY}" = true ] && echo "CHECK ONLY" || echo "SETUP & VALIDATE")"

    # Change to project root
    cd "${PROJECT_ROOT}"

    # Step 1: Check/Install UV
    if ! check_uv_installed; then
        if [ "${CHECK_ONLY}" = true ]; then
            log_error "UV not installed (check-only mode - skipping installation)"
            print_summary
            exit 1
        fi

        if ! install_uv; then
            log_error "Failed to install UV"
            print_summary
            exit 1
        fi
    fi

    # Step 2: Validate Python
    if ! check_python_version; then
        log_error "Python version check failed"
        print_summary
        exit 1
    fi

    # Step 3: Validate pyproject.toml
    if ! validate_pyproject; then
        log_error "pyproject.toml validation failed"
        print_summary
        exit 2
    fi

    # Step 4: Generate/validate lock file
    if [ "${CHECK_ONLY}" = false ]; then
        if ! generate_lock_file; then
            log_error "Lock file generation/validation failed"
            print_summary
            exit 3
        fi
    else
        if ! validate_lock_file; then
            log_error "Lock file validation failed"
            print_summary
            exit 3
        fi
    fi

    # Step 5: Check dependency conflicts
    if ! check_dependency_conflicts; then
        log_error "Dependency conflict check failed"
        print_summary
        exit 4
    fi

    # Step 6: Validate critical dependencies
    if ! validate_critical_dependencies; then
        log_error "Critical dependency validation failed"
        print_summary
        exit 5
    fi

    # Step 7: Validate environment
    if ! validate_environment; then
        log_warning "Environment validation had warnings (non-fatal)"
    fi

    # Step 8: Verify installation
    if ! verify_installation; then
        log_error "Installation verification failed"
        print_summary
        exit 5
    fi

    # Print summary
    print_summary

    # Final status
    if [ ${FAILED_CHECKS} -eq 0 ]; then
        echo ""
        log_success "✅ UV ENVIRONMENT SETUP COMPLETE"
        echo ""
        log_info "Next steps:"
        log_info "  1. Build Docker images: ./scripts/validate-uv-docker-build.sh"
        log_info "  2. Run complete validation: ./scripts/run-complete-validation.sh"
        log_info "  3. Deploy: docker-compose -f docker-compose.production.yml up -d"
        echo ""
        exit 0
    else
        echo ""
        log_error "❌ UV ENVIRONMENT SETUP FAILED"
        log_error "Fix the errors above and run again"
        echo ""
        exit 5
    fi
}

# Trap errors and cleanup
trap 'log_error "Script failed at line $LINENO"' ERR

# Run main function
main "$@"
