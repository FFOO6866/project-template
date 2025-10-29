#!/bin/bash
# Frontend Build Automation Script
# =================================
# Builds and optimizes the Next.js frontend for production deployment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Frontend Build Automation${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
FRONTEND_DIR="fe-reference"
BUILD_DIR="${FRONTEND_DIR}/.next"
OUTPUT_DIR="${FRONTEND_DIR}/out"

# Check if frontend directory exists
if [ ! -d "${FRONTEND_DIR}" ]; then
    echo -e "${RED}ERROR: Frontend directory not found: ${FRONTEND_DIR}${NC}"
    exit 1
fi

cd "${FRONTEND_DIR}"

echo -e "\n${YELLOW}Step 1: Cleaning previous builds...${NC}"
rm -rf .next out node_modules/.cache

echo -e "\n${YELLOW}Step 2: Installing dependencies...${NC}"
if [ -f "package-lock.json" ]; then
    npm ci
elif [ -f "pnpm-lock.yaml" ]; then
    pnpm install --frozen-lockfile
else
    echo -e "${RED}ERROR: No lockfile found${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 3: Running linter...${NC}"
npm run lint || echo -e "${YELLOW}Warning: Linting found issues${NC}"

echo -e "\n${YELLOW}Step 4: Building Next.js application...${NC}"
npm run build

echo -e "\n${YELLOW}Step 5: Build analysis...${NC}"
if [ -d "${BUILD_DIR}" ]; then
    BUILD_SIZE=$(du -sh "${BUILD_DIR}" | cut -f1)
    echo -e "Build directory size: ${GREEN}${BUILD_SIZE}${NC}"

    # Count files
    FILE_COUNT=$(find "${BUILD_DIR}" -type f | wc -l)
    echo -e "Total files: ${GREEN}${FILE_COUNT}${NC}"

    # Check for large files
    echo -e "\nLargest files:"
    find "${BUILD_DIR}" -type f -exec du -h {} + | sort -rh | head -5
else
    echo -e "${RED}ERROR: Build directory not found${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 6: Validating build...${NC}"

# Check for required files
REQUIRED_FILES=(
    ".next/BUILD_ID"
    ".next/package.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${file}" ]; then
        echo -e "${GREEN}✓${NC} Found: ${file}"
    else
        echo -e "${RED}✗${NC} Missing: ${file}"
        exit 1
    fi
done

# Check standalone output (if configured)
if [ -d ".next/standalone" ]; then
    echo -e "${GREEN}✓${NC} Standalone build detected"
    STANDALONE_SIZE=$(du -sh ".next/standalone" | cut -f1)
    echo -e "  Standalone size: ${GREEN}${STANDALONE_SIZE}${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Frontend build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

cd ..

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Test the build locally: ${GREEN}cd ${FRONTEND_DIR} && npm start${NC}"
echo -e "2. Build Docker image: ${GREEN}docker-compose -f docker-compose.production.yml build frontend${NC}"
echo -e "3. Deploy: ${GREEN}docker-compose -f docker-compose.production.yml up -d frontend${NC}"
