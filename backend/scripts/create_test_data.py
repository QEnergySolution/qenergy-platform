#!/usr/bin/env python3
"""
Create test data for Weekly Report analysis functionality.
This script creates project history entries for testing the analysis comparison
between different calendar weeks and categories.
"""

import os
import sys
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.project import Project
from app.models.project_history import ProjectHistory
from app.database import get_db

# Test data for different calendar weeks and categories
TEST_DATA = [
    # Development category projects
    {
        "project_code": "DEV001",
        "project_name": "AI Platform Development",
        "category": "Development",
        "entries": [
            {
                "cw_label": "CW16",
                "log_date": "2025-04-21",
                "title": "Sprint 16 Progress",
                "summary": "Completed user authentication module. Working on dashboard implementation. All tests passing. Team velocity is good.",
                "next_actions": "Continue with dashboard features, implement user roles"
            },
            {
                "cw_label": "CW18",
                "log_date": "2025-05-05",
                "title": "Sprint 18 Progress", 
                "summary": "Dashboard implementation completed with some delays due to API integration issues. Performance optimization needed. Critical bug found in authentication.",
                "next_actions": "Fix authentication bug, optimize performance, prepare for testing phase"
            }
        ]
    },
    {
        "project_code": "DEV002", 
        "project_name": "Mobile App Redesign",
        "category": "Development",
        "entries": [
            {
                "cw_label": "CW16",
                "log_date": "2025-04-22",
                "title": "Design Phase Completion",
                "summary": "UI/UX design completed successfully. Stakeholder approval received. Development team ready to start implementation.",
                "next_actions": "Begin development of core screens, set up development environment"
            },
            {
                "cw_label": "CW18", 
                "log_date": "2025-05-06",
                "title": "Development Progress",
                "summary": "Core screens implemented. Minor issues with responsive design. Testing phase started earlier than planned. Good progress overall.",
                "next_actions": "Fix responsive design issues, continue with remaining screens"
            }
        ]
    },
    # EPC category projects
    {
        "project_code": "EPC001",
        "project_name": "Solar Farm Construction",
        "category": "EPC", 
        "entries": [
            {
                "cw_label": "CW16",
                "log_date": "2025-04-23",
                "title": "Construction Update",
                "summary": "Foundation work completed on schedule. Equipment delivery confirmed for next week. Weather conditions favorable.",
                "next_actions": "Prepare for equipment installation, coordinate with suppliers"
            },
            {
                "cw_label": "CW18",
                "log_date": "2025-05-07", 
                "title": "Installation Progress",
                "summary": "Significant delays in equipment delivery due to supply chain issues. Weather has been problematic with heavy rain. Project timeline at risk.",
                "next_actions": "Escalate supply chain issues, revise timeline, implement weather contingency plan"
            }
        ]
    },
    {
        "project_code": "EPC002",
        "project_name": "Wind Turbine Installation",
        "category": "EPC",
        "entries": [
            {
                "cw_label": "CW16", 
                "log_date": "2025-04-24",
                "title": "Site Preparation",
                "summary": "Site preparation completed successfully. All permits approved. Turbine components arrived on schedule.",
                "next_actions": "Begin turbine assembly, coordinate crane operations"
            },
            {
                "cw_label": "CW18",
                "log_date": "2025-05-08",
                "title": "Assembly Progress", 
                "summary": "Two turbines successfully installed. Third turbine assembly delayed due to technical issues. Safety protocols maintained.",
                "next_actions": "Resolve technical issues, complete remaining installations"
            }
        ]
    },
    # Finance category projects
    {
        "project_code": "FIN001",
        "project_name": "Budget Optimization Initiative", 
        "category": "Finance",
        "entries": [
            {
                "cw_label": "CW16",
                "log_date": "2025-04-25",
                "title": "Q1 Analysis Complete",
                "summary": "Q1 financial analysis completed. Cost savings identified in operations. Budget variance within acceptable range.",
                "next_actions": "Implement cost saving measures, prepare Q2 forecast"
            },
            {
                "cw_label": "CW18",
                "log_date": "2025-05-09",
                "title": "Cost Reduction Progress",
                "summary": "Cost reduction measures implemented successfully. Savings exceeded expectations. Some concerns about impact on service quality.",
                "next_actions": "Monitor service quality metrics, adjust cost measures if needed"
            }
        ]
    },
    # Investment category projects  
    {
        "project_code": "INV001",
        "project_name": "Green Energy Portfolio Expansion",
        "category": "Investment",
        "entries": [
            {
                "cw_label": "CW16",
                "log_date": "2025-04-26", 
                "title": "Market Analysis",
                "summary": "Market research completed for renewable energy investments. Promising opportunities identified in solar and wind sectors.",
                "next_actions": "Conduct due diligence on target investments, prepare investment proposals"
            },
            {
                "cw_label": "CW18",
                "log_date": "2025-05-10",
                "title": "Investment Decisions",
                "summary": "Due diligence completed with mixed results. Some investments show high risk due to regulatory changes. Portfolio diversification needed.",
                "next_actions": "Revise investment strategy, focus on lower-risk opportunities"
            }
        ]
    }
]

def create_test_data():
    """Create test data for weekly report analysis"""
    try:
        # Get database session
        db = next(get_db())
        
        print("Creating test data for Weekly Report analysis...")
        
        # Create or update projects first
        for project_data in TEST_DATA:
            # Check if project exists
            existing_project = db.query(Project).filter(
                Project.project_code == project_data["project_code"]
            ).first()
            
            if not existing_project:
                # Create new project
                new_project = Project(
                    project_code=project_data["project_code"],
                    project_name=project_data["project_name"],
                    portfolio_cluster="Test Portfolio",
                    status=1,
                    created_by="test-script",
                    updated_by="test-script"
                )
                db.add(new_project)
                print(f"Created project: {project_data['project_code']} - {project_data['project_name']}")
            else:
                print(f"Project exists: {project_data['project_code']} - {existing_project.project_name}")
        
        db.commit()
        
        # Create project history entries
        for project_data in TEST_DATA:
            for entry in project_data["entries"]:
                # Check if entry already exists
                existing_entry = db.query(ProjectHistory).filter(
                    ProjectHistory.project_code == project_data["project_code"],
                    ProjectHistory.cw_label == entry["cw_label"],
                    ProjectHistory.category == project_data["category"]
                ).first()
                
                if not existing_entry:
                    # Create new history entry
                    new_entry = ProjectHistory(
                        project_code=project_data["project_code"],
                        category=project_data["category"],
                        entry_type="Report",
                        log_date=datetime.strptime(entry["log_date"], "%Y-%m-%d").date(),
                        cw_label=entry["cw_label"],
                        title=entry["title"],
                        summary=entry["summary"],
                        next_actions=entry["next_actions"],
                        owner="Test Manager",
                        created_by="test-script",
                        updated_by="test-script"
                    )
                    db.add(new_entry)
                    print(f"Created history entry: {project_data['project_code']} - {entry['cw_label']} - {project_data['category']}")
                else:
                    print(f"History entry exists: {project_data['project_code']} - {entry['cw_label']} - {project_data['category']}")
        
        db.commit()
        print("\nTest data creation completed successfully!")
        
        # Print summary
        print("\nTest Data Summary:")
        print("==================")
        for project_data in TEST_DATA:
            print(f"Project: {project_data['project_code']} ({project_data['category']})")
            for entry in project_data["entries"]:
                print(f"  - {entry['cw_label']}: {entry['title']}")
        
        print(f"\nYou can now test the analysis by comparing:")
        print("- CW16 vs CW18 (All Categories)")
        print("- CW16 vs CW18 (Development only)")
        print("- CW16 vs CW18 (EPC only)")
        print("- CW16 vs CW18 (Finance only)")
        print("- CW16 vs CW18 (Investment only)")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
