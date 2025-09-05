#!/usr/bin/env python3
"""
Database Data Checker Script for QEnergy Platform

This script provides various utilities to check and inspect the database data,
including projects, project history, report uploads, and more.

Usage:
    python scripts/check-database.py [command] [options]

Commands:
    summary         Show overall database summary
    projects        List all projects  
    history         Show project history records
    uploads         List report uploads
    recent          Show recent activity
    project <code>  Show details for specific project
    search <term>   Search across project names and history

Examples:
    python scripts/check-database.py summary
    python scripts/check-database.py projects
    python scripts/check-database.py history --limit 10
    python scripts/check-database.py project 2ES00069
    python scripts/check-database.py search "Carmona"
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import SessionLocal
from sqlalchemy import text, func
from tabulate import tabulate


def get_db():
    """Get database session."""
    return SessionLocal()


def show_summary(db):
    """Show overall database summary."""
    print("=" * 60)
    print("📊 QEnergy Platform Database Summary")
    print("=" * 60)
    
    # Basic counts
    project_count = db.execute(text("SELECT COUNT(*) FROM projects")).scalar()
    history_count = db.execute(text("SELECT COUNT(*) FROM project_history")).scalar()
    upload_count = db.execute(text("SELECT COUNT(*) FROM report_uploads")).scalar()
    
    print(f"📁 Total Projects: {project_count}")
    print(f"📋 Project History Records: {history_count}")
    print(f"📄 Report Uploads: {upload_count}")
    
    # Active vs inactive projects
    active_projects = db.execute(text("SELECT COUNT(*) FROM projects WHERE status = 1")).scalar()
    inactive_projects = project_count - active_projects
    
    print(f"\n🟢 Active Projects: {active_projects}")
    print(f"🔴 Inactive Projects: {inactive_projects}")
    
    # Virtual projects
    virtual_projects = db.execute(text("SELECT COUNT(*) FROM projects WHERE project_code LIKE 'VIRT_%'")).scalar()
    real_projects = project_count - virtual_projects
    
    print(f"\n🏢 Real Projects: {real_projects}")
    print(f"🤖 Virtual Projects: {virtual_projects}")
    
    # Recent activity (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_history = db.execute(
        text("SELECT COUNT(*) FROM project_history WHERE created_at >= :date"),
        {"date": seven_days_ago}
    ).scalar()
    
    recent_uploads = db.execute(
        text("SELECT COUNT(*) FROM report_uploads WHERE created_at >= :date"),
        {"date": seven_days_ago}
    ).scalar()
    
    print(f"\n📈 Recent Activity (Last 7 Days):")
    print(f"   📋 New History Records: {recent_history}")
    print(f"   📄 New Uploads: {recent_uploads}")
    
    # Portfolio clusters
    portfolio_counts = db.execute(
        text("""
            SELECT portfolio_cluster, COUNT(*) as count 
            FROM projects 
            WHERE portfolio_cluster IS NOT NULL 
            GROUP BY portfolio_cluster 
            ORDER BY count DESC 
            LIMIT 5
        """)
    ).fetchall()
    
    if portfolio_counts:
        print(f"\n🏗️ Top Portfolio Clusters:")
        for cluster, count in portfolio_counts:
            print(f"   {cluster}: {count} projects")


def show_projects(db, limit=None, status=None):
    """Show projects list."""
    print("=" * 80)
    print("🏢 Projects List")
    print("=" * 80)
    
    query = """
        SELECT project_code, project_name, portfolio_cluster, status,
               CASE WHEN project_code LIKE 'VIRT_%' THEN 'Virtual' ELSE 'Real' END as type
        FROM projects 
    """
    params = {}
    
    conditions = []
    if status is not None:
        conditions.append("status = :status")
        params["status"] = status
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY project_code"
    
    if limit:
        query += " LIMIT :limit"
        params["limit"] = limit
    
    projects = db.execute(text(query), params).fetchall()
    
    if not projects:
        print("No projects found.")
        return
    
    headers = ["Project Code", "Project Name", "Portfolio", "Status", "Type"]
    table_data = []
    
    for p in projects:
        status_icon = "🟢" if p.status == 1 else "🔴"
        type_icon = "🤖" if p.type == "Virtual" else "🏢"
        
        table_data.append([
            p.project_code,
            p.project_name[:40] + "..." if len(p.project_name) > 40 else p.project_name,
            p.portfolio_cluster[:20] + "..." if p.portfolio_cluster and len(p.portfolio_cluster) > 20 else p.portfolio_cluster or "N/A",
            f"{status_icon} {p.status}",
            f"{type_icon} {p.type}"
        ])
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nShowing {len(projects)} projects")


def show_history(db, limit=20, project_code=None):
    """Show project history records."""
    print("=" * 100)
    print("📋 Project History Records")
    print("=" * 100)
    
    query = """
        SELECT ph.project_code, ph.title, ph.category, ph.log_date, 
               ph.created_by, ph.created_at,
               LENGTH(ph.summary) as summary_length
        FROM project_history ph
    """
    params = {}
    
    if project_code:
        query += " WHERE ph.project_code = :project_code"
        params["project_code"] = project_code
    
    query += " ORDER BY ph.created_at DESC"
    
    if limit:
        query += " LIMIT :limit"
        params["limit"] = limit
    
    records = db.execute(text(query), params).fetchall()
    
    if not records:
        print("No history records found.")
        return
    
    headers = ["Project Code", "Title", "Category", "Log Date", "Creator", "Created", "Summary Len"]
    table_data = []
    
    for r in records:
        table_data.append([
            r.project_code,
            r.title[:30] + "..." if r.title and len(r.title) > 30 else r.title or "N/A",
            r.category,
            r.log_date,
            r.created_by,
            r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A",
            f"{r.summary_length} chars" if r.summary_length else "0 chars"
        ])
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nShowing {len(records)} history records")


def show_uploads(db, limit=20):
    """Show report uploads."""
    print("=" * 100)
    print("📄 Report Uploads")
    print("=" * 100)
    
    query = """
        SELECT original_filename, cw_label, status, file_size_bytes,
               created_by, created_at,
               (SELECT COUNT(*) FROM project_history WHERE source_upload_id = report_uploads.id) as history_count
        FROM report_uploads
        ORDER BY created_at DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    uploads = db.execute(text(query)).fetchall()
    
    if not uploads:
        print("No uploads found.")
        return
    
    headers = ["Filename", "CW Label", "Status", "Size", "Creator", "Uploaded", "History Count"]
    table_data = []
    
    for u in uploads:
        # Format file size
        size_mb = u.file_size_bytes / 1024 / 1024 if u.file_size_bytes else 0
        size_str = f"{size_mb:.1f} MB" if size_mb > 0 else "N/A"
        
        table_data.append([
            u.original_filename[:25] + "..." if len(u.original_filename) > 25 else u.original_filename,
            u.cw_label or "N/A",
            u.status,
            size_str,
            u.created_by,
            u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A",
            u.history_count
        ])
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nShowing {len(uploads)} uploads")


def show_project_details(db, project_code):
    """Show detailed information for a specific project."""
    print("=" * 80)
    print(f"🏢 Project Details: {project_code}")
    print("=" * 80)
    
    # Get project info
    project = db.execute(
        text("SELECT * FROM projects WHERE project_code = :code"),
        {"code": project_code}
    ).first()
    
    if not project:
        print(f"❌ Project {project_code} not found.")
        return
    
    print(f"📋 Basic Information:")
    print(f"   Code: {project.project_code}")
    print(f"   Name: {project.project_name}")
    print(f"   Portfolio: {project.portfolio_cluster or 'N/A'}")
    print(f"   Status: {'🟢 Active' if project.status == 1 else '🔴 Inactive'}")
    print(f"   Type: {'🤖 Virtual' if project.project_code.startswith('VIRT_') else '🏢 Real'}")
    print(f"   Created: {project.created_at}")
    print(f"   Updated: {project.updated_at}")
    
    # Get history records
    history = db.execute(
        text("""
            SELECT title, category, log_date, created_by, created_at,
                   LENGTH(summary) as summary_length
            FROM project_history 
            WHERE project_code = :code 
            ORDER BY created_at DESC
        """),
        {"code": project_code}
    ).fetchall()
    
    print(f"\n📋 History Records ({len(history)}):")
    if history:
        for h in history:
            print(f"   📌 {h.title} ({h.category})")
            print(f"      Date: {h.log_date} | Creator: {h.created_by}")
            print(f"      Summary: {h.summary_length} characters")
            print(f"      Created: {h.created_at}")
            print()
    else:
        print("   No history records found.")


def search_data(db, search_term, limit=20):
    """Search across project names and history."""
    print("=" * 80)
    print(f"🔍 Search Results for: '{search_term}'")
    print("=" * 80)
    
    # Search projects
    projects = db.execute(
        text("""
            SELECT project_code, project_name, portfolio_cluster
            FROM projects 
            WHERE LOWER(project_name) LIKE LOWER(:term) 
               OR LOWER(project_code) LIKE LOWER(:term)
               OR LOWER(portfolio_cluster) LIKE LOWER(:term)
            ORDER BY project_code
            LIMIT :limit
        """),
        {"term": f"%{search_term}%", "limit": limit}
    ).fetchall()
    
    if projects:
        print(f"🏢 Projects ({len(projects)}):")
        for p in projects:
            print(f"   {p.project_code}: {p.project_name}")
        print()
    
    # Search history
    history = db.execute(
        text("""
            SELECT project_code, title, category, log_date
            FROM project_history 
            WHERE LOWER(title) LIKE LOWER(:term) 
               OR LOWER(summary) LIKE LOWER(:term)
               OR LOWER(project_code) LIKE LOWER(:term)
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"term": f"%{search_term}%", "limit": limit}
    ).fetchall()
    
    if history:
        print(f"📋 History Records ({len(history)}):")
        for h in history:
            print(f"   {h.project_code}: {h.title} ({h.category}) - {h.log_date}")
        print()
    
    if not projects and not history:
        print("No results found.")


def show_recent_activity(db, days=7):
    """Show recent activity."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    print("=" * 80)
    print(f"📈 Recent Activity (Last {days} Days)")
    print("=" * 80)
    
    # Recent history
    recent_history = db.execute(
        text("""
            SELECT project_code, title, category, created_by, created_at
            FROM project_history 
            WHERE created_at >= :cutoff
            ORDER BY created_at DESC
            LIMIT 20
        """),
        {"cutoff": cutoff_date}
    ).fetchall()
    
    if recent_history:
        print(f"📋 Recent History Records ({len(recent_history)}):")
        for h in recent_history:
            print(f"   {h.created_at.strftime('%m-%d %H:%M')} | {h.project_code} | {h.title} | by {h.created_by}")
        print()
    
    # Recent uploads
    recent_uploads = db.execute(
        text("""
            SELECT original_filename, cw_label, status, created_by, created_at
            FROM report_uploads 
            WHERE created_at >= :cutoff
            ORDER BY created_at DESC
            LIMIT 10
        """),
        {"cutoff": cutoff_date}
    ).fetchall()
    
    if recent_uploads:
        print(f"📄 Recent Uploads ({len(recent_uploads)}):")
        for u in recent_uploads:
            print(f"   {u.created_at.strftime('%m-%d %H:%M')} | {u.original_filename} | {u.status} | by {u.created_by}")
        print()
    
    if not recent_history and not recent_uploads:
        print("No recent activity found.")


def main():
    parser = argparse.ArgumentParser(
        description="QEnergy Platform Database Data Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("command", nargs="?", default="summary",
                       help="Command to run (default: summary)")
    parser.add_argument("target", nargs="?",
                       help="Target for command (e.g., project code, search term)")
    parser.add_argument("--limit", "-l", type=int, default=20,
                       help="Limit number of results (default: 20)")
    parser.add_argument("--status", type=int, choices=[0, 1],
                       help="Filter projects by status (0=inactive, 1=active)")
    parser.add_argument("--days", "-d", type=int, default=7,
                       help="Number of days for recent activity (default: 7)")
    
    args = parser.parse_args()
    
    try:
        db = get_db()
        
        if args.command == "summary":
            show_summary(db)
        elif args.command == "projects":
            show_projects(db, limit=args.limit, status=args.status)
        elif args.command == "history":
            show_history(db, limit=args.limit)
        elif args.command == "uploads":
            show_uploads(db, limit=args.limit)
        elif args.command == "recent":
            show_recent_activity(db, days=args.days)
        elif args.command == "project":
            if not args.target:
                print("❌ Please provide a project code. Example: python scripts/check-database.py project 2ES00069")
                return
            show_project_details(db, args.target)
        elif args.command == "search":
            if not args.target:
                print("❌ Please provide a search term. Example: python scripts/check-database.py search Carmona")
                return
            search_data(db, args.target, limit=args.limit)
        else:
            print(f"❌ Unknown command: {args.command}")
            print("Available commands: summary, projects, history, uploads, recent, project, search")
            return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    finally:
        db.close()
    
    print(f"\n✅ Database check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
