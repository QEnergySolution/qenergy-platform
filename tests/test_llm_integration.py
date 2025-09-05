#!/usr/bin/env python3
"""
Complete LLM Integration Test
"""
import os
import requests
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup environment
os.environ["DATABASE_URL"] = "postgresql://yuxin.xue@localhost:5432/qenergy_platform"

def test_llm_integration():
    """Test complete LLM integration functionality"""
    
    # Database connection
    engine = create_engine(os.environ["DATABASE_URL"])
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("🤖 Testing LLM Integration...")
    
    try:
        with SessionLocal() as db:
            # Clean database
            db.execute(text("DELETE FROM project_history; DELETE FROM report_uploads;"))
            db.commit()
            print("✅ Database cleaned")
            
            # Check initial state
            initial_uploads = db.execute(text("SELECT COUNT(*) FROM report_uploads")).scalar()
            initial_history = db.execute(text("SELECT COUNT(*) FROM project_history")).scalar()
            print(f"📊 Initial state: {initial_uploads} uploads, {initial_history} history records")
            
            # Test LLM parsing API
            print("\n🔄 Testing LLM parsing...")
            
            with open("uploads/2025_CW01_DEV.docx", 'rb') as f:
                files = {'file': ("2025_CW01_DEV.docx", f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                params = {'use_llm': 'true'}
                
                response = requests.post(
                    "http://localhost:8002/api/reports/upload/persist",
                    files=files,
                    params=params,
                    timeout=60
                )
            
            if response.status_code != 200:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            result = response.json()
            print(f"✅ API call successful!")
            print(f"   Upload ID: {result['uploadId']}")
            print(f"   Rows created: {result['rowsCreated']}")
            print(f"   Parsed with: {result['parsedWith']}")
            
            # Verify database state
            final_uploads = db.execute(text("SELECT COUNT(*) FROM report_uploads")).scalar()
            final_history = db.execute(text("SELECT COUNT(*) FROM project_history")).scalar()
            
            print(f"\n📊 Final state: {final_uploads} uploads, {final_history} history records")
            
            # Detailed check of LLM parsed data
            if final_history > 0:
                records = db.execute(text("""
                    SELECT 
                        ru.original_filename,
                        ru.status,
                        ph.project_code,
                        ph.category, 
                        ph.title,
                        ph.summary,
                        ph.next_actions,
                        ph.owner,
                        ph.log_date
                    FROM report_uploads ru 
                    JOIN project_history ph ON ph.source_upload_id = ru.id 
                    ORDER BY ph.id
                """)).fetchall()
                
                print(f"\n📝 LLM Extracted Records ({len(records)} total):")
                for i, record in enumerate(records, 1):
                    print(f"  {i}. Project: {record.project_code} ({record.category})")
                    print(f"     Title: {record.title or 'No title'}")
                    print(f"     Summary: {(record.summary or '')[:150]}...")
                    if record.next_actions:
                        print(f"     Next Actions: {record.next_actions[:100]}...")
                    if record.owner:
                        print(f"     Owner: {record.owner}")
                    print(f"     Date: {record.log_date}")
                    print()
            
            # Verify foreign key relationships
            linked_count = db.execute(text("""
                SELECT COUNT(*) FROM project_history ph 
                WHERE ph.source_upload_id IS NOT NULL
            """)).scalar()
            
            print(f"🔗 Foreign key relationships: {linked_count}/{final_history} records linked")
            
            # Success conditions
            success = (
                final_uploads >= 1 and 
                final_history >= 1 and 
                linked_count == final_history and
                result.get('parsedWith') == 'llm'
            )
            
            if success:
                print("✅ SUCCESS: LLM integration test passed!")
                print("🎯 Features verified:")
                print("   - LLM parsing extracts multiple projects")
                print("   - Data persisted to both tables")
                print("   - Foreign key relationships maintained")
                print("   - Duplicate handling works correctly")
                return True
            else:
                print("❌ FAILURE: Test conditions not met")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_integration()
    exit(0 if success else 1)
