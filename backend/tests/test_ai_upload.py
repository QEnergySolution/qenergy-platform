#!/usr/bin/env python3
"""
Test script for AI-powered upload functionality
"""
import requests
import time
import json
from pathlib import Path

def test_upload_api():
    """Test the upload API with AI parsing"""
    
    # API endpoint
    base_url = "http://localhost:8002/api"
    
    # Test health check first
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test file path (use a sample DOCX file)
    test_file = Path("/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
    
    # Test without AI parsing
    print("\n=== Testing Basic Upload ===")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(f"{base_url}/reports/upload", files=files)
            
        if response.status_code == 200:
            result = response.json()
            print(f"Basic upload successful!")
            print(f"Task ID: {result.get('taskId')}")
            print(f"Rows extracted: {len(result.get('rows', []))}")
            print(f"Parsed with: {result.get('parsedWith')}")
        else:
            print(f"Basic upload failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Basic upload error: {e}")
    
    # Test with AI parsing
    print("\n=== Testing AI Upload ===")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(f"{base_url}/reports/upload?use_llm=true", files=files)
            
        if response.status_code == 200:
            result = response.json()
            print(f"AI upload successful!")
            print(f"Task ID: {result.get('taskId')}")
            print(f"Rows extracted: {len(result.get('rows', []))}")
            print(f"Parsed with: {result.get('parsedWith')}")
            
            # Monitor task progress
            task_id = result.get('taskId')
            if task_id:
                print(f"\n=== Monitoring Task {task_id} ===")
                for i in range(10):  # Poll for up to 10 seconds
                    try:
                        task_response = requests.get(f"{base_url}/tasks/{task_id}")
                        if task_response.status_code == 200:
                            task_status = task_response.json()
                            print(f"[{i}s] Status: {task_status.get('status')} - {task_status.get('message')} ({task_status.get('progress')}%)")
                            
                            if task_status.get('status') in ['completed', 'failed']:
                                break
                        else:
                            print(f"Task status check failed: {task_response.status_code}")
                            break
                    except Exception as e:
                        print(f"Task monitoring error: {e}")
                        break
                    
                    time.sleep(1)
        else:
            print(f"AI upload failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"AI upload error: {e}")

if __name__ == "__main__":
    test_upload_api()
