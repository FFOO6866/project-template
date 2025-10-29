#!/bin/bash
# ============================================================================
# Horme POV - Cloud Deployment Script (UV-Based Images)
# ============================================================================
#
# Builds UV-optimized Docker images and pushes to container registry
#
# Usage:
#   ./scripts/deploy-cloud-uv.sh                  # Build and push all
#   ./scripts/deploy-cloud-uv.sh --service api    # Build specific service
#   ./scripts/deploy-cloud-uv.sh --no-push        # Build only, don't push
#
# Prerequisites:
#   1. Docker BuildKit enabled: export DOCKER_BUILDKIT=1
#   2. Registry authentication: docker login ghcr.io
#   3. Environment variables set (see below)
#
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# ============================================================================
# Configuration from Environment
# ✅ PRODUCTION: All values from environment (no hardcoding)
# ============================================================================

REGISTRY="${REGISTRY:-ghcr.io}"
ORGANIZATION="${ORGANIZATION:-your-org}"
VERSION="${VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BUILD_REVISION="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"

# Service selection
SERVICE="${1:-all}"
PUSH_IMAGES="${PUSH_IMAGES:-true}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

build_image() {
    local service=$1
    local dockerfile=$2
    local image_name="${REGISTRY}/${ORGANIZATION}/horme-${service}"

    log_info "Building ${service} image with UV..."
    log_info "Dockerfile: ${dockerfile}"
    log_info "Image: ${image_name}:${VERSION}"

    # Build with BuildKit for optimal performance
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --build-arg BUILD_VERSION="${VERSION}" \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg BUILD_REVISION="${BUILD_REVISION}" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from "${image_name}:latest" \
        --tag "${image_name}:${VERSION}" \
        --tag "${image_name}:latest" \
        --file "${dockerfile}" \
        ${PUSH_IMAGES:+--push} \
        .

    if [ $? -eq 0 ]; then
        log_info "✅ ${service} image built successfully"
    else
        log_error "❌ ${service} image build failed"
        return 1
    fi
}

push_image() {
    local service=$1
    local image_name="${REGISTRY}/${ORGANIZATION}/horme-${service}"

    if [ "${PUSH_IMAGES}" = "true" ]; then
        log_info "Pushing ${service} image to registry..."
        docker push "${image_name}:${VERSION}"
        docker push "${image_name}:latest"
        log_info "✅ ${service} image pushed successfully"
    else
        log_warn "Skipping push (PUSH_IMAGES=false)"
    fi
}

# ============================================================================
# Validation
# ============================================================================

log_info "🚀 Starting Horme POV Cloud Deployment (UV-Based)"
log_info "Registry: ${REGISTRY}"
log_info "Organization: ${ORGANIZATION}"
log_info "Version: ${VERSION}"
log_info "Build Date: ${BUILD_DATE}"

# Check Docker BuildKit
if [ -z "${DOCKER_BUILDKIT:-}" ]; then
    log_warn "DOCKER_BUILDKIT not set. Enabling..."
    export DOCKER_BUILDKIT=1
fi

# Check if logged into registry
if [ "${PUSH_IMAGES}" = "true" ]; then
    if ! docker info | grep -q "Username"; then
        log_error "Not logged into Docker registry. Run: docker login ${REGISTRY}"
        exit 1
    fi
fi

# ============================================================================
# Build Services
# ============================================================================

case "${SERVICE}" in
    api)
        log_info "Building API service only..."
        build_image "api" "Dockerfile.api.uv"
        ;;
    websocket)
        log_info "Building WebSocket service only..."
        build_image "websocket" "Dockerfile.websocket.uv"
        ;;
    nexus)
        log_info "Building Nexus service only..."
        build_image "nexus" "Dockerfile.nexus.uv"
        ;;
    all|*)
        log_info "Building all services..."
        build_image "api" "Dockerfile.api.uv"
        build_image "websocket" "Dockerfile.websocket.uv"
        build_image "nexus" "Dockerfile.nexus.uv"
        ;;
esac

# ============================================================================
# Summary
# ============================================================================

log_info "✅ Deployment complete!"
log_info ""
log_info "Images built:"
log_info "  ${REGISTRY}/${ORGANIZATION}/horme-api:${VERSION}"
log_info "  ${REGISTRY}/${ORGANIZATION}/horme-websocket:${VERSION}"
log_info "  ${REGISTRY}/${ORGANIZATION}/horme-nexus:${VERSION}"
log_info ""

if [ "${PUSH_IMAGES}" = "true" ]; then
    log_info "Images pushed to ${REGISTRY}"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Deploy to cloud platform (AWS/GCP/Azure)"
    log_info "  2. Update service configurations to use ${VERSION}"
    log_info "  3. Run health checks and smoke tests"
else
    log_info "Images available locally only (not pushed)"
fi

# ============================================================================
# Cloud Platform Deploy Commands (Reference)
# ============================================================================

cat <<EOF

📋 Cloud Platform Deployment Commands:

AWS ECS:
  aws ecs update-service --cluster horme-cluster --service horme-api \\
    --force-new-deployment --image ${REGISTRY}/${ORGANIZATION}/horme-api:${VERSION}

Google Cloud Run:
  gcloud run deploy horme-api --image ${REGISTRY}/${ORGANIZATION}/horme-api:${VERSION} \\
    --region us-central1 --platform managed

Azure Container Apps:
  az containerapp update --name horme-api --resource-group horme-rg \\
    --image ${REGISTRY}/${ORGANIZATION}/horme-api:${VERSION}

Kubernetes:
  kubectl set image deployment/horme-api \\
    horme-api=${REGISTRY}/${ORGANIZATION}/horme-api:${VERSION}

EOF

log_info "🎉 Deployment script complete!"
