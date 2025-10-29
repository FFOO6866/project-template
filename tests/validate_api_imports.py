"""
API Endpoint Import Validation
Checks if all necessary imports are present in nexus_backend_api.py
NO MOCK - Validates actual code imports
"""

import os
import ast
import sys
from typing import Set, List, Tuple

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def extract_imports(file_path: str) -> Set[str]:
    """Extract all import statements from a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError as e:
            print(f"{RED}✗ Syntax error in {file_path}: {e}{RESET}")
            return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.add(f"{module}.{alias.name}")

    return imports


def check_email_quotation_imports(api_file: str) -> Tuple[bool, List[str]]:
    """Check if email quotation related imports are present"""
    required_imports = {
        # Models
        'src.models.email_quotation_models.EmailQuotationRequest',
        'src.models.email_quotation_models.EmailQuotationRequestResponse',
        'src.models.email_quotation_models.EmailQuotationRequestDetail',
        'src.models.email_quotation_models.EmailQuotationRequestUpdate',

        # Services
        'src.services.email_processor.EmailProcessor',
        'src.services.product_matcher.ProductMatcher',
        'src.services.quotation_generator.QuotationGenerator',

        # FastAPI
        'fastapi.BackgroundTasks',
    }

    imports = extract_imports(api_file)
    missing = []

    for req_import in required_imports:
        if req_import not in imports:
            # Check if imported with different syntax
            parts = req_import.split('.')
            module = '.'.join(parts[:-1])
            name = parts[-1]

            # Check if module is imported as "from X import Y"
            found = False
            for imp in imports:
                if imp == req_import or imp.endswith(f".{name}"):
                    found = True
                    break

            if not found:
                missing.append(req_import)

    return (len(missing) == 0, missing)


def check_endpoint_definitions(api_file: str) -> Tuple[bool, List[str]]:
    """Check if email quotation endpoints are defined"""
    required_endpoints = [
        '@app.get("/api/email-quotation-requests/recent"',
        '@app.get("/api/email-quotation-requests/{request_id}"',
        '@app.post("/api/email-quotation-requests/{request_id}/process"',
        '@app.put("/api/email-quotation-requests/{request_id}/status"',
        '@app.post("/api/email-quotation-requests/{request_id}/reprocess"',
    ]

    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()

    missing = []
    for endpoint in required_endpoints:
        if endpoint not in content:
            missing.append(endpoint)

    return (len(missing) == 0, missing)


def check_background_task_function(api_file: str) -> Tuple[bool, List[str]]:
    """Check if background task processing function exists"""
    required_functions = [
        'process_email_quotation_pipeline',
    ]

    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()

    missing = []
    for func in required_functions:
        if f"async def {func}" not in content and f"def {func}" not in content:
            missing.append(func)

    return (len(missing) == 0, missing)


def validate_python_syntax(file_path: str) -> Tuple[bool, str]:
    """Validate that a Python file has correct syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read(), filename=file_path)
        return (True, "")
    except SyntaxError as e:
        return (False, str(e))


def main():
    """Main validation workflow"""
    print("=" * 70)
    print("API ENDPOINT IMPORT VALIDATION")
    print("File: src/nexus_backend_api.py")
    print("=" * 70)
    print()

    api_file = "src/nexus_backend_api.py"

    if not os.path.exists(api_file):
        print(f"{RED}✗ File not found: {api_file}{RESET}")
        return 1

    # Step 1: Syntax validation
    print("Step 1: Validating Python syntax...")
    syntax_ok, syntax_error = validate_python_syntax(api_file)

    if not syntax_ok:
        print(f"{RED}✗ Syntax error: {syntax_error}{RESET}")
        return 1

    print(f"{GREEN}✓ Python syntax is valid{RESET}")
    print()

    # Step 2: Check imports
    print("Step 2: Checking required imports...")
    imports_ok, missing_imports = check_email_quotation_imports(api_file)

    if not imports_ok:
        print(f"{RED}✗ Missing imports:{RESET}")
        for imp in missing_imports:
            print(f"  - {imp}")
        print()
        print("Add these to the top of nexus_backend_api.py:")
        print()
        print("from src.models.email_quotation_models import (")
        print("    EmailQuotationRequest,")
        print("    EmailQuotationRequestResponse,")
        print("    EmailQuotationRequestDetail,")
        print("    EmailQuotationRequestUpdate,")
        print("    EmailQuotationStatusUpdate,")
        print(")")
        print("from src.services.email_processor import EmailProcessor")
        print("from src.services.product_matcher import ProductMatcher")
        print("from src.services.quotation_generator import QuotationGenerator")
        print()
        return 1

    print(f"{GREEN}✓ All required imports present{RESET}")
    print()

    # Step 3: Check endpoint definitions
    print("Step 3: Checking endpoint definitions...")
    endpoints_ok, missing_endpoints = check_endpoint_definitions(api_file)

    if not endpoints_ok:
        print(f"{RED}✗ Missing endpoints:{RESET}")
        for endpoint in missing_endpoints:
            print(f"  - {endpoint}")
        return 1

    print(f"{GREEN}✓ All 5 email quotation endpoints defined{RESET}")
    print()

    # Step 4: Check background task function
    print("Step 4: Checking background task function...")
    function_ok, missing_functions = check_background_task_function(api_file)

    if not function_ok:
        print(f"{RED}✗ Missing functions:{RESET}")
        for func in missing_functions:
            print(f"  - {func}")
        return 1

    print(f"{GREEN}✓ Background task function defined{RESET}")
    print()

    # Summary
    print("=" * 70)
    print(f"{GREEN}✓ API VALIDATION PASSED{RESET}")
    print()
    print("Summary:")
    print(f"  ✓ Python syntax valid")
    print(f"  ✓ All imports present")
    print(f"  ✓ All endpoints defined (5)")
    print(f"  ✓ Background task function exists")
    print()
    print("API endpoints should work correctly.")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    sys.exit(main())
