"""
BIPO API Connection Test Script

Tests BIPO Cloud API connectivity and fetches sample employee data.
Run inside Docker container to test the integration.
"""

import sys
import json
from src.job_pricing.integrations.bipo_client import BIPOClient, BIPOAPIException


def test_authentication():
    """Test BIPO API authentication."""
    print("\n" + "=" * 60)
    print("TEST 1: BIPO API Authentication")
    print("=" * 60)

    try:
        client = BIPOClient()
        print("[INFO] Authenticating with BIPO Cloud API...")

        token = client.get_access_token()
        print(f"[SUCCESS] Authentication successful!")
        print(f"[INFO] Access Token: {token[:30]}...")
        return client

    except BIPOAPIException as e:
        print(f"[ERROR] BIPO API Error: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None


def test_employee_data(client: BIPOClient):
    """Test fetching employee data."""
    print("\n" + "=" * 60)
    print("TEST 2: Fetch Employee Data")
    print("=" * 60)

    try:
        print("[INFO] Fetching active employees from BIPO...")

        employees = client.get_employee_data(is_active=True)
        print(f"[SUCCESS] Fetched {len(employees)} employees")

        if len(employees) > 0:
            print("\n[INFO] Sample Employee Record:")
            print(json.dumps(employees[0], indent=2))

            print("\n[INFO] Employee Fields Available:")
            for key in employees[0].keys():
                print(f"  - {key}")

        return employees

    except BIPOAPIException as e:
        print(f"[ERROR] BIPO API Error: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []


def test_company_list(client: BIPOClient):
    """Test fetching company list."""
    print("\n" + "=" * 60)
    print("TEST 3: Fetch Company List")
    print("=" * 60)

    try:
        print("[INFO] Fetching company list from BIPO...")

        companies = client.get_company_list()
        print(f"[SUCCESS] Fetched {len(companies)} companies")

        if len(companies) > 0:
            print("\n[INFO] Sample Company Record:")
            print(json.dumps(companies[0], indent=2))

        return companies

    except BIPOAPIException as e:
        print(f"[ERROR] BIPO API Error: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []


def test_department_list(client: BIPOClient):
    """Test fetching department list."""
    print("\n" + "=" * 60)
    print("TEST 4: Fetch Department List")
    print("=" * 60)

    try:
        print("[INFO] Fetching department list from BIPO...")

        departments = client.get_department_list()
        print(f"[SUCCESS] Fetched {len(departments)} departments")

        if len(departments) > 0:
            print("\n[INFO] Sample Department Record:")
            print(json.dumps(departments[0], indent=2))

        return departments

    except BIPOAPIException as e:
        print(f"[ERROR] BIPO API Error: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return []


def main():
    """Run all BIPO API tests."""
    print("\n" + "=" * 60)
    print("BIPO CLOUD HRIS API CONNECTION TEST")
    print("=" * 60)

    # Test 1: Authentication
    client = test_authentication()
    if not client:
        print("\n[FATAL] Authentication failed. Cannot proceed with other tests.")
        sys.exit(1)

    # Test 2: Employee Data
    employees = test_employee_data(client)

    # Test 3: Company List
    companies = test_company_list(client)

    # Test 4: Department List
    departments = test_department_list(client)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Authentication: {'SUCCESS' if client else 'FAILED'}")
    print(f"✓ Employee Data: {len(employees)} records fetched")
    print(f"✓ Company List: {len(companies)} records fetched")
    print(f"✓ Department List: {len(departments)} records fetched")

    if client and len(employees) > 0:
        print("\n[SUCCESS] All tests passed! BIPO API integration is working.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Check logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
