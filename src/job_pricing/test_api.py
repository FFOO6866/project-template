"""Test script for Salary Recommendation API."""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_salary_recommendation():
    """Test salary recommendation endpoint."""
    print("=" * 70)
    print("TESTING SALARY RECOMMENDATION API")
    print("=" * 70)

    # Test 1: Salary recommendation
    print("\n1. Testing POST /api/v1/salary/recommend")
    print("-" * 70)

    payload = {
        "job_title": "Senior HR Business Partner",
        "job_description": "Strategic HR partner supporting business units",
        "location": "Tampines",
        "job_family": "HRM"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/salary/recommend",
        json=payload
    )

    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))

    # Test 2: Job matching only
    print("\n\n2. Testing POST /api/v1/salary/match")
    print("-" * 70)

    payload2 = {
        "job_title": "HR Director",
        "job_description": "Leads HR strategy",
        "job_family": "HRM",
        "top_k": 3
    }

    response2 = requests.post(
        f"{BASE_URL}/api/v1/salary/match",
        json=payload2
    )

    print(f"Status Code: {response2.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response2.json(), indent=2))

    # Test 3: Get locations
    print("\n\n3. Testing GET /api/v1/salary/locations")
    print("-" * 70)

    response3 = requests.get(f"{BASE_URL}/api/v1/salary/locations")

    print(f"Status Code: {response3.status_code}")
    result3 = response3.json()
    print(f"\nTotal locations: {result3.get('count')}")
    print(f"Sample locations:")
    for loc in result3.get('locations', [])[:5]:
        print(f"  - {loc['name']}: {loc['cost_of_living_index']:.2f} ({loc['adjustment_note']})")

    # Test 4: Get stats
    print("\n\n4. Testing GET /api/v1/salary/stats")
    print("-" * 70)

    response4 = requests.get(f"{BASE_URL}/api/v1/salary/stats")

    print(f"Status Code: {response4.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response4.json(), indent=2))

    print("\n" + "=" * 70)
    print("API TESTS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_salary_recommendation()
