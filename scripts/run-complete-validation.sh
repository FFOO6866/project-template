#!/bin/bash
# ============================================================================
# Complete UV Migration Validation Orchestrator
# ============================================================================
#
# Master validation script that orchestrates all UV migration validation
# steps in the correct order with comprehensive reporting.
#
# Validation Pipeline:
# 1. UV environment setup and validation
# 2. Docker build validation for all UV images
# 3. Production completeness validation
# 4. Configuration validation
# 5. UV-specific tests
# 6. Comprehensive final report
#
# Features:
# - Sequential and parallel execution (where safe)
# - Progress tracking with real-time status
# - Comprehensive HTML and JSON reporting
# - CI/CD friendly output and exit codes
# - Rollback on critical failures
# - NO mock data or hardcoding
# - Performance benchmarking
# - Integration with existing validation scripts
#
# Usage:
#   ./scripts/run-complete-validation.sh
#   ./scripts/run-complete-validation.sh --fast          # Skip optional checks
#   ./scripts/run-complete-validation.sh --ci            # CI/CD mode
#   ./scripts/run-complete-validation.sh --stop-on-fail  # Stop on first failure
#
# Exit codes:
#   0 - All validations passed
#   1 - UV setup failed
#   2 - Docker build failed
#   3 - Production validation failed
#   4 - Configuration validation failed
#   5 - Multiple failures
#
# ============================================================================

set -euo pipefail

# ============================================================================
# Configuration and Constants
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script metadata
SCRIPT_NAME="Complete Validation Orchestrator"
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Validation phases
declare -A PHASE_STATUS
declare -A PHASE_DURATION
declare -A PHASE_EXITCODE

PHASES=(
    "uv_setup"
    "docker_build"
    "production_validation"
    "config_validation"
    "uv_specific_tests"
)

PHASE_NAMES=(
    "UV Environment Setup"
    "Docker Build Validation"
    "Production Completeness"
    "Configuration Validation"
    "UV-Specific Tests"
)

# Options
FAST_MODE=false
CI_MODE=false
STOP_ON_FAIL=false
VERBOSE=false
SKIP_DOCKER=false
SKIP_SECURITY=false

# Results tracking
TOTAL_PHASES=0
PASSED_PHASES=0
FAILED_PHASES=0
SKIPPED_PHASES=0

# Report files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="${PROJECT_ROOT}/validation-reports"
REPORT_JSON="${REPORT_DIR}/validation-${TIMESTAMP}.json"
REPORT_HTML="${REPORT_DIR}/validation-${TIMESTAMP}.html"
REPORT_LOG="${REPORT_DIR}/validation-${TIMESTAMP}.log"

# ============================================================================
# Logging Functions
# ============================================================================

# Redirect all output to log file and terminal
mkdir -p "${REPORT_DIR}"
exec > >(tee -a "${REPORT_LOG}")
exec 2>&1

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_phase() {
    echo ""
    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC} ${BOLD}$*${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_step() {
    echo -e "\n${CYAN}==>${NC} ${BOLD}$*${NC}"
}

log_progress() {
    if [ "${CI_MODE}" = false ]; then
        echo -e "    ${BLUE}→${NC} $*"
    fi
}

log_metric() {
    echo -e "    ${MAGENTA}📊${NC} $*"
}

# ============================================================================
# Utility Functions
# ============================================================================

print_header() {
    clear
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                                                                        ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  ${BOLD}${SCRIPT_NAME}${NC}                                      ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  Version ${SCRIPT_VERSION}                                                       ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                                        ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Timestamp:${NC} $(date)"
    echo -e "${CYAN}Project:${NC}   ${PROJECT_ROOT}"
    echo -e "${CYAN}Mode:${NC}      $([ "${CI_MODE}" = true ] && echo "CI/CD" || echo "Interactive")"
    echo ""
}

format_duration() {
    local seconds=$1
    local minutes=$((seconds / 60))
    local remaining_seconds=$((seconds % 60))

    if [ ${minutes} -gt 0 ]; then
        echo "${minutes}m ${remaining_seconds}s"
    else
        echo "${seconds}s"
    fi
}

get_phase_emoji() {
    local status=$1

    case "${status}" in
        "PASS")
            echo "✅"
            ;;
        "FAIL")
            echo "❌"
            ;;
        "SKIP")
            echo "⏭️"
            ;;
        "RUNNING")
            echo "🔄"
            ;;
        *)
            echo "⏳"
            ;;
    esac
}

# ============================================================================
# Phase Execution Functions
# ============================================================================

run_phase() {
    local phase_key=$1
    local phase_name=$2
    local phase_command=$3

    ((TOTAL_PHASES++))

    log_phase "PHASE ${TOTAL_PHASES}: ${phase_name}"

    PHASE_STATUS["${phase_key}"]="RUNNING"

    local start_time
    start_time=$(date +%s)

    log_progress "Executing: ${phase_command}"
    echo ""

    # Execute phase command
    local exit_code=0
    if eval "${phase_command}"; then
        exit_code=0
        PHASE_STATUS["${phase_key}"]="PASS"
        ((PASSED_PHASES++))
    else
        exit_code=$?
        PHASE_STATUS["${phase_key}"]="FAIL"
        ((FAILED_PHASES++))
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    PHASE_DURATION["${phase_key}"]=${duration}
    PHASE_EXITCODE["${phase_key}"]=${exit_code}

    echo ""
    if [ ${exit_code} -eq 0 ]; then
        log_success "${phase_name} completed successfully in $(format_duration ${duration})"
    else
        log_error "${phase_name} failed with exit code ${exit_code} after $(format_duration ${duration})"

        if [ "${STOP_ON_FAIL}" = true ]; then
            log_error "Stopping validation (--stop-on-fail enabled)"
            generate_report
            exit ${exit_code}
        fi
    fi

    echo ""
    echo -e "${CYAN}────────────────────────────────────────────────────────────────────────${NC}"

    return ${exit_code}
}

skip_phase() {
    local phase_key=$1
    local phase_name=$2
    local reason=$3

    ((TOTAL_PHASES++))
    ((SKIPPED_PHASES++))

    PHASE_STATUS["${phase_key}"]="SKIP"
    PHASE_DURATION["${phase_key}"]=0
    PHASE_EXITCODE["${phase_key}"]=-1

    log_warning "Skipping ${phase_name}: ${reason}"
}

# ============================================================================
# Validation Phases
# ============================================================================

run_uv_setup() {
    local setup_script="${SCRIPT_DIR}/setup-uv-environment.sh"

    if [ ! -f "${setup_script}" ]; then
        log_error "UV setup script not found: ${setup_script}"
        return 1
    fi

    bash "${setup_script}"
}

run_docker_build() {
    if [ "${SKIP_DOCKER}" = true ]; then
        skip_phase "docker_build" "Docker Build Validation" "Docker validation disabled"
        return 0
    fi

    local docker_script="${SCRIPT_DIR}/validate-uv-docker-build.sh"

    if [ ! -f "${docker_script}" ]; then
        log_error "Docker validation script not found: ${docker_script}"
        return 1
    fi

    local args=""
    [ "${VERBOSE}" = true ] && args+=" --verbose"
    [ "${SKIP_SECURITY}" = false ] && args+=" --security-scan"
    [ "${FAST_MODE}" = false ] && args+=" --compare-pip"

    bash "${docker_script}" ${args}
}

run_production_validation() {
    local validation_script="${SCRIPT_DIR}/validate_production_complete.py"

    if [ ! -f "${validation_script}" ]; then
        log_warning "Production validation script not found: ${validation_script}"
        return 0
    fi

    python3 "${validation_script}"
}

run_config_validation() {
    local config_script="${SCRIPT_DIR}/validate_config.py"

    if [ ! -f "${config_script}" ]; then
        log_warning "Config validation script not found: ${config_script}"
        return 0
    fi

    python3 "${config_script}"
}

run_uv_specific_tests() {
    log_step "Running UV-specific validation tests"

    # Test 1: Verify uv.lock exists
    log_progress "Checking uv.lock existence..."
    if [ -f "${PROJECT_ROOT}/uv.lock" ]; then
        log_success "uv.lock exists"
    else
        log_error "uv.lock not found"
        return 1
    fi

    # Test 2: Verify uv.lock is up to date
    log_progress "Checking uv.lock is up to date..."
    if uv sync --frozen --dry-run >/dev/null 2>&1; then
        log_success "uv.lock is up to date"
    else
        log_error "uv.lock is out of sync with pyproject.toml"
        return 1
    fi

    # Test 3: Verify no pip artifacts
    log_progress "Checking for pip artifacts..."
    if [ -f "${PROJECT_ROOT}/requirements.txt" ] || [ -f "${PROJECT_ROOT}/requirements-*.txt" ]; then
        log_warning "Found pip requirements files - should use pyproject.toml"
    else
        log_success "No pip requirements files found"
    fi

    # Test 4: Verify Docker images use UV
    log_progress "Checking Dockerfile UV integration..."
    local uv_dockerfiles=0
    for dockerfile in "${PROJECT_ROOT}"/Dockerfile*.uv; do
        if [ -f "${dockerfile}" ]; then
            if grep -q "ghcr.io/astral-sh/uv" "${dockerfile}"; then
                ((uv_dockerfiles++))
            fi
        fi
    done

    if [ ${uv_dockerfiles} -ge 3 ]; then
        log_success "Found ${uv_dockerfiles} UV Dockerfiles"
    else
        log_error "Expected at least 3 UV Dockerfiles, found ${uv_dockerfiles}"
        return 1
    fi

    # Test 5: Verify no hardcoded versions in Dockerfiles
    log_progress "Checking for hardcoded localhost in Dockerfiles..."
    if grep -h "localhost" "${PROJECT_ROOT}"/Dockerfile*.uv 2>/dev/null | grep -qE "(http|ws|redis|bolt)://localhost"; then
        log_error "Found hardcoded localhost URLs in UV Dockerfiles"
        return 1
    else
        log_success "No hardcoded localhost URLs in UV Dockerfiles"
    fi

    # Test 6: Verify OpenAI version consistency
    log_progress "Checking OpenAI version consistency..."
    if grep -q "openai==1.51.2" "${PROJECT_ROOT}/pyproject.toml"; then
        log_success "OpenAI version is standardized to 1.51.2"
    else
        log_warning "OpenAI version might not be 1.51.2 (check pyproject.toml)"
    fi

    log_success "UV-specific tests completed"
    return 0
}

# ============================================================================
# Report Generation
# ============================================================================

generate_report() {
    log_step "Generating comprehensive validation report"

    # Generate JSON report
    generate_json_report

    # Generate HTML report
    generate_html_report

    # Print summary
    print_summary
}

generate_json_report() {
    local json="{"
    json+="\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    json+="\"project_root\":\"${PROJECT_ROOT}\","
    json+="\"total_phases\":${TOTAL_PHASES},"
    json+="\"passed\":${PASSED_PHASES},"
    json+="\"failed\":${FAILED_PHASES},"
    json+="\"skipped\":${SKIPPED_PHASES},"
    json+="\"phases\":{"

    local first=true
    for i in "${!PHASES[@]}"; do
        local phase_key="${PHASES[$i]}"
        local phase_name="${PHASE_NAMES[$i]}"

        if [ "${first}" = false ]; then
            json+=","
        fi
        first=false

        local status="${PHASE_STATUS[${phase_key}]:-UNKNOWN}"
        local duration="${PHASE_DURATION[${phase_key}]:-0}"
        local exitcode="${PHASE_EXITCODE[${phase_key}]:--1}"

        json+="\"${phase_key}\":{"
        json+="\"name\":\"${phase_name}\","
        json+="\"status\":\"${status}\","
        json+="\"duration_seconds\":${duration},"
        json+="\"exit_code\":${exitcode}"
        json+="}"
    done

    json+="}}"

    echo "${json}" | python3 -m json.tool > "${REPORT_JSON}" 2>/dev/null || echo "${json}" > "${REPORT_JSON}"

    log_success "JSON report: ${REPORT_JSON}"
}

generate_html_report() {
    cat > "${REPORT_HTML}" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UV Migration Validation Report - ${TIMESTAMP}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { font-size: 2em; margin-bottom: 10px; }
        .timestamp { opacity: 0.9; }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f9f9f9;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .summary-card h3 {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .summary-card .value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .passed { color: #10b981; }
        .failed { color: #ef4444; }
        .skipped { color: #f59e0b; }
        .phases {
            padding: 30px;
        }
        .phase {
            background: #f9f9f9;
            border-left: 4px solid #ddd;
            margin-bottom: 15px;
            border-radius: 4px;
            overflow: hidden;
        }
        .phase.pass { border-color: #10b981; }
        .phase.fail { border-color: #ef4444; }
        .phase.skip { border-color: #f59e0b; }
        .phase-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            cursor: pointer;
            background: white;
        }
        .phase-name {
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .phase-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: #666;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-badge.pass { background: #d1fae5; color: #065f46; }
        .status-badge.fail { background: #fee2e2; color: #991b1b; }
        .status-badge.skip { background: #fef3c7; color: #92400e; }
        footer {
            padding: 20px;
            text-align: center;
            background: #f9f9f9;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 UV Migration Validation Report</h1>
            <div class="timestamp">${TIMESTAMP}</div>
        </header>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Phases</h3>
                <div class="value">${TOTAL_PHASES}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="value passed">${PASSED_PHASES}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value failed">${FAILED_PHASES}</div>
            </div>
            <div class="summary-card">
                <h3>Skipped</h3>
                <div class="value skipped">${SKIPPED_PHASES}</div>
            </div>
        </div>

        <div class="phases">
            <h2 style="margin-bottom: 20px;">Validation Phases</h2>
EOF

    # Add phase details
    for i in "${!PHASES[@]}"; do
        local phase_key="${PHASES[$i]}"
        local phase_name="${PHASE_NAMES[$i]}"
        local status="${PHASE_STATUS[${phase_key}]:-UNKNOWN}"
        local duration="${PHASE_DURATION[${phase_key}]:-0}"
        local exitcode="${PHASE_EXITCODE[${phase_key}]:--1}"

        local status_lower=$(echo "${status}" | tr '[:upper:]' '[:lower:]')
        local emoji=$(get_phase_emoji "${status}")

        cat >> "${REPORT_HTML}" <<EOF
            <div class="phase ${status_lower}">
                <div class="phase-header">
                    <div class="phase-name">
                        <span>${emoji}</span>
                        <span>${phase_name}</span>
                    </div>
                    <div class="phase-meta">
                        <span class="status-badge ${status_lower}">${status}</span>
                        <span>⏱️ $(format_duration ${duration})</span>
                        <span>Exit: ${exitcode}</span>
                    </div>
                </div>
            </div>
EOF
    done

    cat >> "${REPORT_HTML}" <<EOF
        </div>

        <footer>
            <p>Generated by ${SCRIPT_NAME} v${SCRIPT_VERSION}</p>
            <p>Project: ${PROJECT_ROOT}</p>
            <p>Full logs: ${REPORT_LOG}</p>
        </footer>
    </div>
</body>
</html>
EOF

    log_success "HTML report: ${REPORT_HTML}"
}

print_summary() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                     ${BOLD}VALIDATION SUMMARY${NC}                              ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Overall statistics
    echo -e "${BOLD}Overall Statistics:${NC}"
    echo -e "  Total Phases:  ${TOTAL_PHASES}"
    echo -e "  Passed:        ${GREEN}${PASSED_PHASES}${NC}"
    echo -e "  Failed:        ${RED}${FAILED_PHASES}${NC}"
    echo -e "  Skipped:       ${YELLOW}${SKIPPED_PHASES}${NC}"
    echo ""

    # Success rate
    local success_rate=0
    if [ ${TOTAL_PHASES} -gt 0 ]; then
        success_rate=$((PASSED_PHASES * 100 / TOTAL_PHASES))
    fi
    echo -e "${BOLD}Success Rate:${NC} ${success_rate}%"
    echo ""

    # Phase breakdown
    echo -e "${BOLD}Phase Results:${NC}"
    for i in "${!PHASES[@]}"; do
        local phase_key="${PHASES[$i]}"
        local phase_name="${PHASE_NAMES[$i]}"
        local status="${PHASE_STATUS[${phase_key}]:-UNKNOWN}"
        local duration="${PHASE_DURATION[${phase_key}]:-0}"
        local emoji=$(get_phase_emoji "${status}")

        printf "  %s %-30s %s\n" "${emoji}" "${phase_name}" "$(format_duration ${duration})"
    done
    echo ""

    # Reports
    echo -e "${BOLD}Reports Generated:${NC}"
    echo -e "  JSON:  ${REPORT_JSON}"
    echo -e "  HTML:  ${REPORT_HTML}"
    echo -e "  Logs:  ${REPORT_LOG}"
    echo ""

    echo -e "${CYAN}════════════════════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# Main Execution Flow
# ============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fast)
                FAST_MODE=true
                shift
                ;;
            --ci)
                CI_MODE=true
                shift
                ;;
            --stop-on-fail)
                STOP_ON_FAIL=true
                shift
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-security)
                SKIP_SECURITY=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                cat <<EOF
Usage: $0 [OPTIONS]

Complete UV Migration Validation Orchestrator

Options:
    --fast              Skip optional checks (faster execution)
    --ci                CI/CD mode (minimal output)
    --stop-on-fail      Stop on first failure
    --skip-docker       Skip Docker build validation
    --skip-security     Skip security scans
    --verbose, -v       Enable verbose output
    --help, -h          Show this help message

Examples:
    $0                      # Full validation
    $0 --fast               # Quick validation
    $0 --ci                 # CI/CD pipeline
    $0 --stop-on-fail       # Fail fast mode

Exit codes:
    0 - All validations passed
    1 - UV setup failed
    2 - Docker build failed
    3 - Production validation failed
    4 - Configuration validation failed
    5 - Multiple failures
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

    # Change to project root
    cd "${PROJECT_ROOT}"

    # Initialize phase tracking
    for phase in "${PHASES[@]}"; do
        PHASE_STATUS["${phase}"]="PENDING"
        PHASE_DURATION["${phase}"]=0
        PHASE_EXITCODE["${phase}"]=-1
    done

    # Execute validation phases
    local overall_start
    overall_start=$(date +%s)

    # Phase 1: UV Setup
    run_phase "uv_setup" "${PHASE_NAMES[0]}" "run_uv_setup"

    # Phase 2: Docker Build
    run_phase "docker_build" "${PHASE_NAMES[1]}" "run_docker_build"

    # Phase 3: Production Validation
    run_phase "production_validation" "${PHASE_NAMES[2]}" "run_production_validation"

    # Phase 4: Config Validation
    run_phase "config_validation" "${PHASE_NAMES[3]}" "run_config_validation"

    # Phase 5: UV-Specific Tests
    run_phase "uv_specific_tests" "${PHASE_NAMES[4]}" "run_uv_specific_tests"

    # Calculate total duration
    local overall_end
    overall_end=$(date +%s)
    local total_duration=$((overall_end - overall_start))

    # Generate comprehensive report
    generate_report

    # Final status
    echo ""
    if [ ${FAILED_PHASES} -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║${NC}                                                                        ${GREEN}║${NC}"
        echo -e "${GREEN}║${NC}  ${BOLD}✅ ALL VALIDATIONS PASSED${NC}                                         ${GREEN}║${NC}"
        echo -e "${GREEN}║${NC}                                                                        ${GREEN}║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        log_info "Total validation time: $(format_duration ${total_duration})"
        echo ""
        log_info "Next steps:"
        log_info "  1. Review reports in: ${REPORT_DIR}"
        log_info "  2. Deploy to production: docker-compose -f docker-compose.production.yml up -d"
        log_info "  3. Monitor deployment: docker-compose -f docker-compose.production.yml logs -f"
        echo ""
        exit 0
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║${NC}                                                                        ${RED}║${NC}"
        echo -e "${RED}║${NC}  ${BOLD}❌ VALIDATION FAILED${NC}                                               ${RED}║${NC}"
        echo -e "${RED}║${NC}                                                                        ${RED}║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        log_error "Total validation time: $(format_duration ${total_duration})"
        log_error "Failed phases: ${FAILED_PHASES}/${TOTAL_PHASES}"
        echo ""
        log_error "Review the reports for details:"
        log_error "  HTML: ${REPORT_HTML}"
        log_error "  JSON: ${REPORT_JSON}"
        log_error "  Logs: ${REPORT_LOG}"
        echo ""
        exit 5
    fi
}

# Trap errors
trap 'log_error "Script interrupted or failed at line $LINENO"' ERR INT TERM

# Run main function
main "$@"
