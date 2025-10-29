"""
Test Document to Quotation Pipeline
Validates the complete flow from upload to quotation generation
NO MOCK DATA - Real API calls, real database, real AI processing
"""

import requests
import time
import os

API_BASE = "http://localhost:8002"

def test_complete_flow():
    """Test the complete document-to-quotation pipeline"""

    print("=" * 80)
    print("TESTING DOCUMENT TO QUOTATION PIPELINE")
    print("=" * 80)

    # Step 1: Login to get auth token
    print("\n1. Authenticating...")
    login_response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={
            "email": "admin@yourdomain.com",
            "password": "Admin@123"
        }
    )

    if login_response.status_code != 200:
        print(f"[FAIL] Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False

    token = login_response.json()["access_token"]
    print(f"[PASS] Authenticated successfully")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create test document
    print("\n2. Creating test RFP document...")
    test_document_content = """
REQUEST FOR PROPOSAL - CONSTRUCTION SAFETY EQUIPMENT

Project: Downtown Construction Site Safety Compliance
Date: 2024-10-21
Company: ABC Construction Ltd

REQUIREMENTS:

1. Safety Helmets
   - Quantity: 50 units
   - Specification: White color, CE certified, adjustable suspension
   - Required for: Construction workers

2. Safety Gloves
   - Quantity: 100 pairs
   - Specification: Heavy duty, cut resistant, Level 5 protection
   - Required for: General site work and material handling

3. Work Lights
   - Quantity: 10 units
   - Specification: Rechargeable LED, minimum 20W, IP54 rated
   - Required for: Night shift operations

DELIVERY:
Required delivery within 2 weeks from order placement.

PAYMENT TERMS:
Net 30 days from delivery.

Please provide quotation with detailed pricing and delivery schedule.
"""

    test_file_path = "/tmp/test_rfp.txt"
    with open(test_file_path, 'w') as f:
        f.write(test_document_content)

    print("[PASS] Test document created")

    # Step 3: Upload document
    print("\n3. Uploading document...")

    with open(test_file_path, 'rb') as f:
        files = {'file': ('test_rfp.txt', f, 'text/plain')}
        data = {
            'document_type': 'rfp',
            'category': 'safety_equipment'
        }

        upload_response = requests.post(
            f"{API_BASE}/api/files/upload",
            headers=headers,
            files=files,
            data=data
        )

    if upload_response.status_code != 200:
        print(f"[FAIL] Upload failed: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
        return False

    upload_result = upload_response.json()
    document_id = upload_result["document_id"]
    print(f"[PASS] Document uploaded successfully (ID: {document_id})")
    print(f"   Background processing started: {upload_result.get('processing_started', 'N/A')}")

    # Step 4: Wait for background processing
    print("\n4. Waiting for background processing...")
    print("   (This involves: AI extraction, product matching, quotation generation, PDF creation)")

    max_wait_time = 60  # 60 seconds max
    check_interval = 5
    elapsed_time = 0

    while elapsed_time < max_wait_time:
        print(f"   Checking status... ({elapsed_time}s elapsed)")

        # Check document status
        doc_response = requests.get(
            f"{API_BASE}/api/documents/{document_id}",
            headers=headers
        )

        if doc_response.status_code == 200:
            doc_data = doc_response.json()
            status = doc_data.get('status', 'unknown')
            quotation_id = doc_data.get('quotation_id')

            print(f"   Document status: {status}")

            if status == 'completed' and quotation_id:
                print(f"\n[PASS] Processing completed! Quotation ID: {quotation_id}")

                # Step 5: Verify quotation
                print("\n5. Verifying quotation...")
                quote_response = requests.get(
                    f"{API_BASE}/api/quotations/{quotation_id}",
                    headers=headers
                )

                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    print(f"\n[PASS] QUOTATION GENERATED SUCCESSFULLY!")
                    print(f"   Quote Number: {quote_data['quote_number']}")
                    print(f"   Customer: {quote_data['customer_name']}")
                    print(f"   Total Amount: {quote_data['currency']} {quote_data['total_amount']:.2f}")
                    print(f"   Line Items: {len(quote_data.get('items', []))}")
                    print(f"   Status: {quote_data['status']}")
                    print(f"   PDF Path: {quote_data.get('pdf_path', 'Not generated')}")

                    # Show line items
                    print("\n   Line Items:")
                    for idx, item in enumerate(quote_data.get('items', []), 1):
                        print(f"   {idx}. {item['product_name']}")
                        print(f"      Qty: {item['quantity']} {item['unit']} @ {quote_data['currency']} {item['unit_price']:.2f}")
                        print(f"      Total: {quote_data['currency']} {item['line_total']:.2f}")

                    print("\n" + "=" * 80)
                    print("TEST COMPLETED SUCCESSFULLY!")
                    print("=" * 80)
                    return True
                else:
                    print(f"[FAIL] Failed to retrieve quotation: {quote_response.status_code}")
                    return False

            elif status == 'failed':
                print(f"[FAIL] Processing failed!")
                print(f"   Document data: {doc_data}")
                return False

        time.sleep(check_interval)
        elapsed_time += check_interval

    print(f"\n[FAIL] Timeout waiting for processing (waited {max_wait_time}s)")
    return False


if __name__ == '__main__':
    try:
        success = test_complete_flow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
