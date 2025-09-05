#!/usr/bin/env python3
"""
Test database persistence functionality via API
"""
import os
import sys
import requests
import time
from pathlib import Path

# Set up environment
os.environ["DATABASE_URL"] = "postgresql://yuxin.xue@localhost:5432/qenergy_platform"

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    def test_api_persistence():
        """Test API-based database persistence functionality"""
        
        # Setup database connection
        engine = create_engine(os.environ["DATABASE_URL"])
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test file
        test_file = Path("uploads/2025_CW01_DEV.docx")
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"✅ Test file found: {test_file}")
        
        # API endpoint
        api_url = "http://localhost:8002/api/reports/upload/persist"
        
        try:
            with SessionLocal() as db:
                # Check initial counts
                initial_uploads = db.execute(text("SELECT COUNT(*) FROM report_uploads")).scalar()
                initial_history = db.execute(text("SELECT COUNT(*) FROM project_history")).scalar()
                
                print(f"Initial report_uploads count: {initial_uploads}")
                print(f"Initial project_history count: {initial_history}")
                
                # Test the API endpoint (use simple parsing for now)
                print("\n🔄 Testing API persistence with simple parsing...")
                
                with open(test_file, 'rb') as f:
                    files = {'file': (test_file.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                    params = {'use_llm': 'false'}  # Use simple parsing for now
                    
                    response = requests.post(api_url, files=files, params=params, timeout=60)
                
                if response.status_code != 200:
                    print(f"❌ API call failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                
                result = response.json()
                print(f"✅ API call successful: {result}")
                
                # If we get a task ID, monitor the task progress
                task_id = result.get("taskId")
                if task_id:
                    print(f"📋 Monitoring task: {task_id}")
                    
                    for i in range(30):  # Wait up to 30 seconds
                        try:
                            task_response = requests.get(f"http://localhost:8002/api/tasks/{task_id}")
                            if task_response.status_code == 200:
                                task_status = task_response.json()
                                print(f"[{i}s] Status: {task_status.get('status')} - {task_status.get('message')} ({task_status.get('progress', 0)}%)")
                                
                                if task_status.get('status') in ['completed', 'failed']:
                                    break
                            else:
                                print(f"Task status check failed: {task_response.status_code}")
                        except Exception as e:
                            print(f"Task monitoring error: {e}")
                        
                        time.sleep(1)
                
                # Wait a moment for database operations to complete
                time.sleep(2)
                
                # Check final counts
                final_uploads = db.execute(text("SELECT COUNT(*) FROM report_uploads")).scalar()
                final_history = db.execute(text("SELECT COUNT(*) FROM project_history")).scalar()
                
                print(f"\nFinal report_uploads count: {final_uploads}")
                print(f"Final project_history count: {final_history}")
                
                # Verify data was inserted
                uploads_added = final_uploads - initial_uploads
                history_added = final_history - initial_history
                
                print(f"\n📊 Results:")
                print(f"  - Report uploads added: {uploads_added}")
                print(f"  - Project history entries added: {history_added}")
                
                if uploads_added >= 1 and history_added >= 1:
                    print("✅ SUCCESS: Data successfully persisted to database via API!")
                    
                    # Show sample data
                    upload_sample = db.execute(text("""
                        SELECT id, original_filename, status, cw_label, created_by 
                        FROM report_uploads 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """)).first()
                    
                    history_sample = db.execute(text("""
                        SELECT id, project_code, category, title, summary 
                        FROM project_history 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)).fetchall()
                    
                    print(f"\n📝 Latest upload record:")
                    print(f"  ID: {upload_sample.id}")
                    print(f"  Filename: {upload_sample.original_filename}")
                    print(f"  Status: {upload_sample.status}")
                    print(f"  CW Label: {upload_sample.cw_label}")
                    print(f"  Created by: {upload_sample.created_by}")
                    
                    print(f"\n📝 Latest project history records:")
                    for i, record in enumerate(history_sample, 1):
                        print(f"  {i}. Project: {record.project_code} | Category: {record.category}")
                        print(f"     Title: {record.title}")
                        if record.summary:
                            print(f"     Summary: {record.summary[:100]}...")
                    
                    # Test foreign key relationship
                    linked_records = db.execute(text("""
                        SELECT ru.original_filename, ph.project_code, ph.title
                        FROM report_uploads ru 
                        JOIN project_history ph ON ph.source_upload_id = ru.id 
                        WHERE ru.id = :upload_id
                    """), {"upload_id": upload_sample.id}).fetchall()
                    
                    print(f"\n🔗 Foreign key relationships:")
                    for record in linked_records[:3]:  # Show first 3
                        print(f"  File: {record.original_filename} → Project: {record.project_code} ({record.title})")
                    
                    if len(linked_records) > 3:
                        print(f"  ... and {len(linked_records) - 3} more relationships")
                    
                    return True
                else:
                    print("❌ FAILURE: No data was persisted to database")
                    return False
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        print("🔍 Testing API-based Database Persistence...")
        success = test_api_persistence()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install dependencies and setup the environment.")
    sys.exit(1)
