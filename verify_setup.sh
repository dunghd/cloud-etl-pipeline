#!/bin/bash

# Cloud ETL Pipeline - Setup Verification Script
# This script verifies that all prerequisites are installed correctly

echo "=================================================="
echo "Cloud ETL Pipeline - Setup Verification"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        if [ ! -z "$2" ]; then
            version=$($1 $2 2>&1 | head -n 1)
            echo "  Version: $version"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        return 1
    fi
}

# Check Poetry
echo "Checking Prerequisites..."
echo "------------------------"

check_command "python3" "--version"
check_command "java" "-version"
check_command "poetry" "--version"

echo ""
echo "Checking AWS CLI..."
echo "-------------------"
if check_command "aws" "--version"; then
    echo "  Checking AWS credentials..."
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} AWS credentials are configured"
    else
        echo -e "  ${YELLOW}!${NC} AWS credentials may not be configured"
    fi
else
    echo -e "  ${YELLOW}!${NC} AWS CLI is optional but recommended"
fi

echo ""
echo "Checking Project Structure..."
echo "-----------------------------"

required_files=(
    "pyproject.toml"
    "config/config.yml"
    ".env.example"
    "etl/pipeline.py"
    "etl/extract/s3_extractor.py"
    "etl/transform/transformer.py"
    "etl/load/redshift_loader.py"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file is missing"
        all_files_exist=false
    fi
done

echo ""
echo "Checking Environment Configuration..."
echo "-------------------------------------"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    # Check for required variables
    required_vars=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "S3_BUCKET_NAME")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env 2>/dev/null; then
            value=$(grep "^${var}=" .env | cut -d'=' -f2)
            if [ "$value" != "your_"* ] && [ ! -z "$value" ]; then
                echo -e "  ${GREEN}✓${NC} $var is set"
            else
                echo -e "  ${YELLOW}!${NC} $var needs to be configured"
            fi
        else
            echo -e "  ${RED}✗${NC} $var is not set"
        fi
    done
else
    echo -e "${YELLOW}!${NC} .env file does not exist"
    echo "  Run: cp .env.example .env"
fi

echo ""
echo "Checking Poetry Dependencies..."
echo "-------------------------------"

if [ -f "poetry.lock" ]; then
    echo -e "${GREEN}✓${NC} poetry.lock exists"
else
    echo -e "${YELLOW}!${NC} Dependencies not installed yet"
    echo "  Run: poetry install"
fi

echo ""
echo "Directory Structure..."
echo "---------------------"

required_dirs=(
    "etl"
    "etl/extract"
    "etl/transform"
    "etl/load"
    "etl/utils"
    "config"
    "tests"
    "logs"
    "data/raw"
    "data/processed"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/ is missing"
    fi
done

echo ""
echo "=================================================="
echo "Verification Complete!"
echo "=================================================="
echo ""

# Summary
echo "Next Steps:"
echo "----------"
if [ ! -f "poetry.lock" ]; then
    echo "1. Install dependencies: poetry install"
fi
if [ ! -f ".env" ]; then
    echo "2. Configure environment: cp .env.example .env && nano .env"
fi
echo "3. Generate sample data: poetry run python generate_sample_data.py"
echo "4. Review configuration: cat config/config.yml"
echo "5. Read documentation: cat QUICKSTART.md"
echo ""

echo "Run the pipeline:"
echo "  poetry run python examples.py"
echo ""
