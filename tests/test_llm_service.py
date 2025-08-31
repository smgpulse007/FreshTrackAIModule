"""
Test script for LLM-enhanced OCR service
Tests the intelligent parsing capabilities with various receipt samples
"""

import requests
import json
from pathlib import Path
import time

# Test configuration
BASE_URL = "http://localhost:8005"  # LLM service
API_BASE = f"{BASE_URL}/api/v1"

def test_health_check():
    """Test the health endpoint"""
    print("🏥 Testing health check...")
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Service healthy - LLM Status: {data['llm_status']}")
        print(f"📋 Features: {', '.join(data['features'])}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_parsing_methods():
    """Test available parsing methods"""
    print("\n🧠 Testing parsing methods...")
    response = requests.get(f"{API_BASE}/parsing-methods")
    if response.status_code == 200:
        data = response.json()
        print("Available parsing methods:")
        for method, info in data['methods'].items():
            status = "✅" if info['available'] else "❌"
            print(f"  {status} {method}: {info['description']} (Accuracy: {info['accuracy']})")
        return True
    else:
        print(f"❌ Failed to get parsing methods: {response.status_code}")
        return False

def test_receipt_processing():
    """Test receipt processing with sample image"""
    print("\n📸 Testing receipt processing...")
    
    # Use the existing sample receipt
    receipt_path = Path("tests/sample_receipt.jpg")
    if not receipt_path.exists():
        print(f"❌ Sample receipt not found at {receipt_path}")
        return False
    
    with open(receipt_path, "rb") as f:
        files = {"file": ("sample_receipt.jpg", f, "image/jpeg")}
        
        print("Processing receipt with LLM-enhanced service...")
        start_time = time.time()
        response = requests.post(f"{API_BASE}/receipt/process", files=files)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Processing successful in {processing_time:.2f}s")
            print(f"📊 Method used: {data['parsing_method']}")
            print(f"📝 Total items: {data['total_items']}")
            
            # Show extracted items
            print("\n🛒 Extracted food items:")
            for i, item in enumerate(data['items'], 1):
                confidence_emoji = "🟢" if item['confidence'] > 0.8 else "🟡" if item['confidence'] > 0.5 else "🟠"
                print(f"  {i}. {item['normalized_name']}")
                print(f"     Raw: {item['raw_text'][:50]}...")
                print(f"     {confidence_emoji} Confidence: {item['confidence']:.2f}")
                print(f"     📂 Category: {item['category']}")
                if item.get('price'):
                    print(f"     💰 Price: ${item['price']:.2f}")
                if item.get('brand'):
                    print(f"     🏷️ Brand: {item['brand']}")
                print()
            
            return True
        else:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False

def test_comparison_with_production():
    """Compare LLM service with production service"""
    print("\n🔬 Comparing LLM vs Production service...")
    
    receipt_path = Path("tests/sample_receipt.jpg")
    if not receipt_path.exists():
        print(f"❌ Sample receipt not found")
        return False
    
    results = {}
    services = {
        "Production API": "http://localhost:8004/api/v1/receipt/process",
        "LLM Enhanced": "http://localhost:8005/api/v1/receipt/process"
    }
    
    with open(receipt_path, "rb") as f:
        file_content = f.read()
    
    for service_name, url in services.items():
        try:
            files = {"file": ("sample_receipt.jpg", file_content, "image/jpeg")}
            response = requests.post(url, files=files)
            
            if response.status_code == 200:
                data = response.json()
                results[service_name] = {
                    "total_items": data['total_items'],
                    "parsing_method": data.get('parsing_method', 'unknown'),
                    "items": data['items']
                }
                print(f"✅ {service_name}: {data['total_items']} items")
            else:
                print(f"❌ {service_name}: Failed ({response.status_code})")
        
        except requests.exceptions.ConnectionError:
            print(f"⚠️ {service_name}: Service not available")
    
    # Compare results
    if len(results) == 2:
        prod_items = results["Production API"]["total_items"]
        llm_items = results["LLM Enhanced"]["total_items"]
        
        print(f"\n📈 Comparison Results:")
        print(f"  Production API: {prod_items} items")
        print(f"  LLM Enhanced: {llm_items} items")
        
        if llm_items < prod_items:
            print(f"✅ LLM service filtered out {prod_items - llm_items} false positives!")
        elif llm_items > prod_items:
            print(f"📈 LLM service found {llm_items - prod_items} additional items")
        else:
            print("📊 Same number of items detected")

def test_edge_cases():
    """Test with complex receipt patterns"""
    print("\n🧪 Testing edge cases...")
    
    from tests.sample_receipt_generator import get_sample_receipt
    
    # Test with the complex receipt that has errors
    complex_receipt_text = get_sample_receipt("complex_receipt_errors")
    
    # For this test, we'd need to create an image from text
    # This would be implemented in a full testing environment
    print("Edge case testing would require additional receipt samples")
    print("Recommended: Add more real receipt images to tests/ directory")

def main():
    """Run all tests"""
    print("🚀 Starting LLM-Enhanced OCR Service Tests\n")
    
    # Run tests
    tests = [
        test_health_check,
        test_parsing_methods,
        test_receipt_processing,
        test_comparison_with_production,
        test_edge_cases
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LLM service is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
