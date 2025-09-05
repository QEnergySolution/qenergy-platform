#!/usr/bin/env python3
"""
Simple database persistence test using direct SQL
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Set up environment
os.environ["DATABASE_URL"] = "postgresql://yuxin.xue@localhost:5432/qenergy_platform"

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import hashlib
    import datetime
    
    def test_direct_db_insertion():
        """Test direct database insertion"""
        
        # Setup database connection
        engine = create_engine(os.environ["DATABASE_URL"])
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test file
        test_file = Path("uploads/2025_CW01_DEV.docx")
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"✅ Test file found: {test_file}")
        
        # Calculate SHA256
        sha256_hash = hashlib.sha256()
        with open(test_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        sha256 = sha256_hash.hexdigest()
        
        try:
            with SessionLocal() as db:
                # Check initial counts
                initial_uploads = db.execute(text("SELECT COUNT(*) FROM report_uploads")).scalar()
                initial_history = db.execute(text("SELECT COUNT(*) FROM project_history")).scalar()
                
                print(f"Initial report_uploads count: {initial_uploads}")
                print(f"Initial project_history count: {initial_history}")
                
                # Insert test upload record
                upload_result = db.execute(text("""
                    INSERT INTO report_uploads (
                        original_filename, storage_path, mime_type, file_size_bytes,
                        sha256, status, cw_label, created_by, updated_by
                    ) VALUES (
                        :filename, :path, :mime_type, :size,
                        :sha256, 'parsed', :cw_label, :created_by, :updated_by
                    ) RETURNING id
                """), {
                    "filename": test_file.name,
                    "path": str(test_file),
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "size": test_file.stat().st_size,
                    "sha256": sha256,
                    "cw_label": "CW01",
                    "created_by": "test_user",
                    "updated_by": "test_user"
                })
                
                upload_id = upload_result.scalar()
                print(f"✅ Created upload record with ID: {upload_id}")
                
                # Insert test project history records using existing project codes
                test_projects = [
                    {
                        "project_code": "2ES00009",
                        "category": "Development",
                        "title": "Test Upload - Boedo 1",
                        "summary": "This is a test project summary from AI parsing for Boedo 1",
                        "source_upload_id": upload_id
                    },
                    {
                        "project_code": "2DE00001", 
                        "category": "Development",
                        "title": "Test Upload - Illmersdorf",
                        "summary": "This is a test project summary from AI parsing for Illmersdorf",
                        "source_upload_id": upload_id
                    }
                ]
                
                for project in test_projects:
                    db.execute(text("""
                        INSERT INTO project_history (
                            project_code, category, entry_type, log_date, cw_label,
                            title, summary, created_by, updated_by, source_upload_id
                        ) VALUES (
                            :project_code, :category, 'Report', :log_date, :cw_label,
                            :title, :summary, :created_by, :updated_by, :source_upload_id
                        )
                    """), {
                        **project,
                        "entry_type": "Report",
                        "log_date": datetime.date(2025, 1, 6),  # Monday of CW01 2025
                        "cw_label": "CW01",
                        "created_by": "test_user",
                        "updated_by": "test_user"
                    })
                
                print(f"✅ Created {len(test_projects)} project history records")
                
                # Commit the transaction
                db.commit()
                
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
                    print("✅ SUCCESS: Data successfully persisted to database!")
                    
                    # Show sample data
                    upload_sample = db.execute(text("""
                        SELECT id, original_filename, status, cw_label, created_by 
                        FROM report_uploads 
                        WHERE id = :upload_id
                    """), {"upload_id": upload_id}).first()
                    
                    history_sample = db.execute(text("""
                        SELECT id, project_code, category, title, summary 
                        FROM project_history 
                        WHERE source_upload_id = :upload_id
                    """), {"upload_id": upload_id}).fetchall()
                    
                    print(f"\n📝 Upload record:")
                    print(f"  ID: {upload_sample.id}")
                    print(f"  Filename: {upload_sample.original_filename}")
                    print(f"  Status: {upload_sample.status}")
                    print(f"  CW Label: {upload_sample.cw_label}")
                    print(f"  Created by: {upload_sample.created_by}")
                    
                    print(f"\n📝 Project history records:")
                    for i, record in enumerate(history_sample, 1):
                        print(f"  {i}. Project: {record.project_code} | Category: {record.category}")
                        print(f"     Title: {record.title}")
                        print(f"     Summary: {record.summary}")
                    
                    # Test foreign key relationship
                    linked_records = db.execute(text("""
                        SELECT ru.original_filename, ph.project_code, ph.title
                        FROM report_uploads ru 
                        JOIN project_history ph ON ph.source_upload_id = ru.id 
                        WHERE ru.id = :upload_id
                    """), {"upload_id": upload_id}).fetchall()
                    
                    print(f"\n🔗 Foreign key relationships:")
                    for record in linked_records:
                        print(f"  File: {record.original_filename} → Project: {record.project_code} ({record.title})")
                    
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
        print("🔍 Testing Direct Database Persistence...")
        success = test_direct_db_insertion()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install dependencies: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)
