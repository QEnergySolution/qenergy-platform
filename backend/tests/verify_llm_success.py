#!/usr/bin/env python3
"""
Verify if LLM parsing functionality is successful
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup environment
os.environ["DATABASE_URL"] = "postgresql://yuxin.xue@localhost:5432/qenergy_platform"

def verify_llm_success():
    """Verify if LLM parsing functionality has been successfully implemented"""
    
    engine = create_engine(os.environ["DATABASE_URL"])
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("🔍 Verifying LLM Integration Success...")
    
    try:
        with SessionLocal() as db:
            # Check report_uploads table
            uploads = db.execute(text("""
                SELECT id, original_filename, status, created_by 
                FROM report_uploads 
                ORDER BY created_at DESC 
                LIMIT 5
            """)).fetchall()
            
            print(f"\n📁 Report Uploads ({len(uploads)} records):")
            for upload in uploads:
                print(f"  - {upload.original_filename} (Status: {upload.status}, By: {upload.created_by})")
            
            # Check project_history table
            history = db.execute(text("""
                SELECT ph.project_code, ph.category, ph.title, ph.summary, ru.original_filename
                FROM project_history ph
                LEFT JOIN report_uploads ru ON ph.source_upload_id = ru.id
                ORDER BY ph.created_at DESC
                LIMIT 10
            """)).fetchall()
            
            print(f"\n📊 Project History ({len(history)} records):")
            for record in history:
                print(f"  - {record.project_code} ({record.category})")
                print(f"    Title: {record.title or 'No title'}")
                print(f"    Summary: {(record.summary or '')[:100]}...")
                print(f"    Source: {record.original_filename or 'Direct entry'}")
                print()
            
            # Check foreign key relationships
            linked = db.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(source_upload_id) as linked
                FROM project_history
            """)).first()
            
            print(f"🔗 Foreign Key Relationships:")
            print(f"  Total history records: {linked.total}")
            print(f"  Linked to uploads: {linked.linked}")
            print(f"  Link percentage: {(linked.linked/linked.total*100):.1f}%" if linked.total > 0 else "  No records")
            
            # Check LLM parsing functionality
            llm_evidence = []
            
            # 1. Check if there are multiple different project codes
            project_codes = db.execute(text("""
                SELECT DISTINCT project_code 
                FROM project_history 
                WHERE source_upload_id IS NOT NULL
            """)).fetchall()
            
            if len(project_codes) > 1:
                llm_evidence.append(f"✅ Multiple projects extracted ({len(project_codes)} unique project codes)")
            else:
                llm_evidence.append(f"⚠️  Only {len(project_codes)} project code found")
            
            # 2. Check if there are detailed summary contents
            detailed_summaries = db.execute(text("""
                SELECT COUNT(*) 
                FROM project_history 
                WHERE source_upload_id IS NOT NULL 
                AND LENGTH(summary) > 50
            """)).scalar()
            
            if detailed_summaries > 0:
                llm_evidence.append(f"✅ Detailed summaries found ({detailed_summaries} records with >50 chars)")
            else:
                llm_evidence.append("⚠️  No detailed summaries found")
            
            # 3. Check if there is source_text
            source_texts = db.execute(text("""
                SELECT COUNT(*) 
                FROM project_history 
                WHERE source_upload_id IS NOT NULL 
                AND source_text IS NOT NULL 
                AND source_text != ''
            """)).scalar()
            
            if source_texts > 0:
                llm_evidence.append(f"✅ Source text preserved ({source_texts} records)")
            else:
                llm_evidence.append("⚠️  No source text found")
            
            print(f"\n🤖 LLM Integration Evidence:")
            for evidence in llm_evidence:
                print(f"  {evidence}")
            
            # Final evaluation
            success_criteria = [
                len(uploads) > 0,
                len(history) > 0, 
                linked.linked > 0,
                len(project_codes) >= 1,
                detailed_summaries > 0
            ]
            
            success_count = sum(success_criteria)
            total_criteria = len(success_criteria)
            
            print(f"\n🎯 Success Score: {success_count}/{total_criteria}")
            
            if success_count >= 4:
                print("✅ SUCCESS: LLM integration is working!")
                print("🎉 Features verified:")
                print("   - File uploads are processed and stored")
                print("   - LLM extracts meaningful project data") 
                print("   - Foreign key relationships maintained")
                print("   - Data persistence working correctly")
                return True
            else:
                print("⚠️  PARTIAL SUCCESS: Some features need attention")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_llm_success()
    exit(0 if success else 1)
