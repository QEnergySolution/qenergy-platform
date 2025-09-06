#!/usr/bin/env python3
"""
Test script to verify the Weekly Report analysis functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_analysis_endpoints():
    print("🧪 Testing Weekly Report Analysis Endpoints")
    print("=" * 50)
    
    # Test 1: Get project candidates
    print("\n1. Testing project candidates endpoint...")
    response = requests.get(f"{BASE_URL}/api/projects/by-cw-pair", params={
        "past_cw": "CW16",
        "latest_cw": "CW18",
        "category": "Development"
    })
    
    if response.status_code == 200:
        candidates = response.json()
        dev_projects = [p for p in candidates if p['project_code'].startswith('DEV')]
        print(f"✅ Found {len(candidates)} total projects, {len(dev_projects)} test projects")
        for proj in dev_projects:
            print(f"   - {proj['project_code']}: {proj['project_name']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 2: Clear existing analysis for our test projects
    print("\n2. Clearing existing analysis data...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="qenergy_platform", 
            user="qenergy_user",
            password="qenergy_password"
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM weekly_report_analysis WHERE project_code IN ('DEV001', 'DEV002')")
        conn.commit()
        print(f"✅ Cleared existing analysis data")
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not clear data: {e}")
    
    # Test 3: Trigger analysis
    print("\n3. Triggering analysis...")
    analysis_payload = {
        "past_cw": "CW16",
        "latest_cw": "CW18",
        "language": "EN", 
        "category": "Development",
        "created_by": "test-script"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/reports/analyze",
        json=analysis_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Analysis completed: {result['message']}")
        print(f"   - Analyzed: {result['analyzed_count']}")
        print(f"   - Skipped: {result['skipped_count']}")
        print(f"   - Results: {len(result['results'])}")
        
        # Show some results
        for i, res in enumerate(result['results'][:3]):
            print(f"   Result {i+1}: {res['project_code']} - Risk: {res.get('risk_lvl', 'N/A')}%, Similarity: {res.get('similarity_lvl', 'N/A')}%")
    else:
        print(f"❌ Analysis failed: {response.status_code} - {response.text}")
        return False
    
    # Test 4: Get analysis results
    print("\n4. Getting analysis results...")
    response = requests.get(f"{BASE_URL}/api/weekly-analysis", params={
        "past_cw": "CW16",
        "latest_cw": "CW18",
        "category": "Development"
    })
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Retrieved {len(results)} analysis results")
        for res in results[:3]:
            print(f"   - {res['project_code']}: Risk={res.get('risk_lvl', 'N/A')}%, Sim={res.get('similarity_lvl', 'N/A')}%")
    else:
        print(f"❌ Failed to get results: {response.status_code} - {response.text}")
        return False
    
    print("\n🎉 All tests passed! The Weekly Report analysis is working correctly.")
    print("\nYou can now:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Navigate to Weekly Report")
    print("3. Select:")
    print("   - Past Report: 2025 - CW16")
    print("   - Latest Report: 2025 - CW18") 
    print("   - Category: Development (or any other)")
    print("4. Click 'Start Analysis'")
    
    return True

if __name__ == "__main__":
    test_analysis_endpoints()
