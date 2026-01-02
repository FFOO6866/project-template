# -*- coding: utf-8 -*-
"""
Detailed Field Extraction Quality Verification
Compares extracted fields against document content
"""

import requests
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

ROLE_PROFILES = [
    r"C:\Users\fujif\OneDrive\Desktop\RRRR\Role Profile_Manager Total Rewards  Technology_2025_DY.pdf",
    r"C:\Users\fujif\OneDrive\Desktop\RRRR\Role Profile_AD PO Gov_20250710.pdf",
    r"C:\Users\fujif\OneDrive\Desktop\RRRR\Role Profile_AD Group Total Rewards_20250519.pdf",
    r"C:\Users\fujif\OneDrive\Desktop\RRRR\Role Profile_TA PO Gov_20250708.pdf",
]


def login():
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "testpno", "password": "testpassword123"}
    )
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def extract_and_display(token, file_path):
    """Extract and display all fields in detail"""
    print(f"\n{'='*80}")
    print(f"FILE: {Path(file_path).name}")
    print(f"{'='*80}")

    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f, "application/pdf")}
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(
            f"{BASE_URL}/api/v1/documents/extract",
            files=files,
            headers=headers
        )

    if resp.status_code != 200:
        print(f"[ERROR] Extraction failed: {resp.text[:200]}")
        return None

    data = resp.json()

    # Display each field in detail
    print(f"\n1. JOB TITLE:")
    print(f"   {data.get('job_title', 'NOT EXTRACTED')}")

    print(f"\n2. JOB SUMMARY:")
    summary = data.get('job_summary', 'NOT EXTRACTED')
    print(f"   {summary}")

    print(f"\n3. DEPARTMENT:")
    print(f"   {data.get('department', 'NOT EXTRACTED')}")

    print(f"\n4. JOB FAMILY:")
    print(f"   {data.get('job_family', 'NOT EXTRACTED')}")

    print(f"\n5. PORTFOLIO:")
    print(f"   {data.get('portfolio', 'NOT EXTRACTED')}")

    print(f"\n6. EMPLOYMENT TYPE:")
    print(f"   {data.get('employment_type', 'NOT EXTRACTED')}")

    print(f"\n7. EXPERIENCE REQUIRED:")
    print(f"   {data.get('experience_required', 'NOT EXTRACTED')}")

    print(f"\n8. KEY RESPONSIBILITIES ({len(data.get('key_responsibilities', []))} items):")
    for i, resp_item in enumerate(data.get('key_responsibilities', []), 1):
        print(f"   {i}. {resp_item[:100]}{'...' if len(resp_item) > 100 else ''}")

    print(f"\n9. SKILLS REQUIRED ({len(data.get('skills_required', []))} items):")
    for i, skill in enumerate(data.get('skills_required', []), 1):
        print(f"   {i}. {skill}")

    print(f"\n10. QUALIFICATIONS ({len(data.get('qualifications', []))} items):")
    for i, qual in enumerate(data.get('qualifications', []), 1):
        print(f"   {i}. {qual}")

    return data


def test_mercer_and_alternatives(token, job_data):
    """Test Mercer mapping and alternative titles"""
    job_title = job_data.get('job_title')
    job_summary = job_data.get('job_summary', '')

    print(f"\n{'='*80}")
    print(f"MERCER MAPPING & ALTERNATIVES FOR: {job_title}")
    print(f"{'='*80}")

    # Mercer Mapping
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{BASE_URL}/api/v1/ai/map-mercer-code",
        json={"job_title": job_title, "job_description": job_summary},
        headers=headers
    )

    if resp.status_code == 200:
        mercer = resp.json()
        print(f"\nMERCER JOB MATCHES:")
        for i, match in enumerate(mercer.get('matches', []), 1):
            print(f"   {i}. {match['mercer_job_code']}")
            print(f"      Title: {match['mercer_job_title']}")
            print(f"      Similarity: {match['similarity_score']:.1%}")
            print(f"      Family: {match.get('job_family', 'N/A')}")
            if match.get('mercer_job_description'):
                desc = match['mercer_job_description'][:150]
                print(f"      Description: {desc}...")
            print()
    else:
        print(f"   [ERROR] Mercer mapping failed: {resp.text[:200]}")

    # Alternative Titles
    resp = requests.post(
        f"{BASE_URL}/api/v1/ai/generate-alternative-titles",
        json={"job_title": job_title, "job_family": job_data.get('job_family')},
        headers=headers
    )

    if resp.status_code == 200:
        alts = resp.json()
        print(f"\nALTERNATIVE MARKET TITLES:")
        for i, title in enumerate(alts.get('alternative_titles', []), 1):
            print(f"   {i}. {title}")
    else:
        print(f"   [ERROR] Alternative titles failed: {resp.text[:200]}")


def test_salary_details(token, job_data):
    """Get detailed salary recommendation"""
    job_title = job_data.get('job_title')

    print(f"\n{'='*80}")
    print(f"SALARY RECOMMENDATION FOR: {job_title}")
    print(f"{'='*80}")

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{BASE_URL}/api/v1/salary/recommend",
        json={
            "job_title": job_title,
            "job_description": job_data.get('job_summary', ''),
            "job_family": job_data.get('job_family', ''),
            "location": "Singapore"
        },
        headers=headers
    )

    if resp.status_code == 200:
        salary = resp.json()

        print(f"\nRECOMMENDED SALARY RANGE:")
        rec_range = salary.get('recommended_range', {})
        print(f"   Min: ${rec_range.get('min', 0):,.0f}")
        print(f"   Max: ${rec_range.get('max', 0):,.0f}")
        print(f"   Mid: ${rec_range.get('mid', 0):,.0f}")

        print(f"\nPERCENTILES:")
        percentiles = salary.get('percentiles', {})
        print(f"   P25: ${percentiles.get('p25', 0):,.0f}")
        print(f"   P50: ${percentiles.get('p50', 0):,.0f}")
        print(f"   P75: ${percentiles.get('p75', 0):,.0f}")

        print(f"\nCONFIDENCE:")
        confidence = salary.get('confidence', {})
        print(f"   Score: {confidence.get('score', 0)}")
        print(f"   Level: {confidence.get('level', 'N/A')}")

        print(f"\nMATCHED JOBS ({len(salary.get('matched_jobs', []))} jobs):")
        for i, job in enumerate(salary.get('matched_jobs', [])[:3], 1):
            print(f"   {i}. {job.get('job_code', 'N/A')} - {job.get('job_title', 'N/A')}")
            print(f"      Similarity: {job.get('similarity_score', 0):.1%}")

        print(f"\nDATA SOURCES:")
        sources = salary.get('data_sources', {})
        print(f"   Mercer: {sources.get('mercer_jobs', 0)} jobs")
        print(f"   Sample Size: {sources.get('total_sample_size', 0)}")

        print(f"\nSUMMARY:")
        print(f"   {salary.get('summary', 'N/A')}")
    else:
        print(f"   [ERROR] Salary recommendation failed: {resp.text[:300]}")


def main():
    print("\n" + "="*80)
    print("DETAILED FIELD EXTRACTION QUALITY VERIFICATION")
    print("="*80)

    token = login()
    if not token:
        print("[ERROR] Login failed")
        return

    all_extractions = []

    # Extract all documents first
    for file_path in ROLE_PROFILES:
        data = extract_and_display(token, file_path)
        if data:
            all_extractions.append(data)

    # Then test Mercer and alternatives for each
    print("\n\n" + "#"*80)
    print("MERCER MAPPING & ALTERNATIVE TITLES")
    print("#"*80)

    for data in all_extractions:
        test_mercer_and_alternatives(token, data)

    # Then test salary for each
    print("\n\n" + "#"*80)
    print("SALARY RECOMMENDATIONS")
    print("#"*80)

    for data in all_extractions:
        test_salary_details(token, data)


if __name__ == "__main__":
    main()
