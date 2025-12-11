#!/usr/bin/env python
"""
Test script for Analytics API endpoints.
Run this after the Django server is running.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/analytics"

def test_endpoint(name, url):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response keys: {list(data.keys())}")
        print(f"✓ Preview: {json.dumps(data, indent=2)[:500]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def main():
    """Test all analytics endpoints"""
    print("="*60)
    print("ANALYTICS API ENDPOINT TESTS")
    print("="*60)
    
    endpoints = [
        ("Monthly Analytics", f"{BASE_URL}/monthly/?months=6"),
        ("Top Categories", f"{BASE_URL}/top-categories/?limit=10"),
        ("Cashflow", f"{BASE_URL}/cashflow/?period=30&granularity=daily"),
        ("Recurring Payments", f"{BASE_URL}/recurring-payments/?min_occurrences=2"),
        ("Spending Trends", f"{BASE_URL}/spending-trends/"),
        ("Budget Insights", f"{BASE_URL}/budget-insights/"),
    ]
    
    results = []
    for name, url in endpoints:
        results.append(test_endpoint(name, url))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()
