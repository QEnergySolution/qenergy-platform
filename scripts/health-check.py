#!/usr/bin/env python3
"""
QEnergy Platform Health Check Script (Python版本)
Health check windows
"""

import requests
import psycopg2
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration
FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8002"
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "qenergy_platform",
    "user": "yuxin.xue"
}

# Icons and colors
ICONS = {
    "check": "✅",
    "cross": "❌", 
    "warning": "⚠️",
    "info": "ℹ️",
    "rocket": "🚀",
    "database": "🗄️",
    "globe": "🌐",
    "gear": "⚙️",
    "clean": "🧹"
}

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class HealthChecker:
    def __init__(self):
        self.results = {
            "frontend": False,
            "backend": False,
            "database": False,
            "api": False,
            "uploads": False
        }
        self.start_time = datetime.now()
        
    def print_colored(self, text: str, color: str = Colors.NC) -> None:
        """Print colored text"""
        print(f"{color}{text}{Colors.NC}")
        
    def test_http_endpoint(self, url: str, timeout: int = 10, expected_status: int = 200) -> bool:
        """Test HTTP endpoint availability"""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == expected_status
        except Exception:
            return False
            
    def test_database_connection(self) -> Tuple[bool, Optional[str]]:
        """Test database connection"""
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            conn.close()
            return result[0] == 1, None
        except Exception as e:
            return False, str(e)
            
    def get_database_stats(self) -> Dict[str, int]:
        """Get database table statistics"""
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()
            
            stats = {}
            tables = ["projects", "project_history", "report_uploads", "weekly_report_analysis"]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                stats[table] = count
                
            # Get recent uploads
            cursor.execute("""
                SELECT COUNT(*) FROM report_uploads 
                WHERE uploaded_at > NOW() - INTERVAL '24 hours';
            """)
            stats["recent_uploads_24h"] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception:
            return {}
            
    def check_frontend(self) -> bool:
        """Check frontend health"""
        self.print_colored(f"\n{Colors.BLUE}{ICONS['globe']} Frontend Health Check{Colors.NC}")
        self.print_colored("---------------------------")
        
        if self.test_http_endpoint(FRONTEND_URL):
            self.print_colored(f"{ICONS['check']} Frontend server is {Colors.GREEN}HEALTHY{Colors.NC} ({FRONTEND_URL})")
            
            # Check if content loads
            try:
                response = requests.get(FRONTEND_URL, timeout=10)
                if any(keyword in response.text.lower() for keyword in ["qenergy", "dashboard", "platform"]):
                    self.print_colored(f"{ICONS['check']} Frontend content is {Colors.GREEN}LOADING CORRECTLY{Colors.NC}")
                else:
                    self.print_colored(f"{ICONS['warning']} Frontend is running but content may not be loading properly")
            except Exception:
                self.print_colored(f"{ICONS['warning']} Could not verify frontend content")
                
            self.results["frontend"] = True
            return True
        else:
            self.print_colored(f"{ICONS['cross']} Frontend server is {Colors.RED}NOT RESPONDING{Colors.NC} ({FRONTEND_URL})")
            self.print_colored(f"{ICONS['info']} Try: {Colors.CYAN}pnpm dev:fe{Colors.NC}")
            return False
            
    def check_backend(self) -> bool:
        """Check backend health"""
        self.print_colored(f"\n{Colors.BLUE}{ICONS['gear']} Backend Health Check{Colors.NC}")
        self.print_colored("--------------------------")
        
        health_url = f"{BACKEND_URL}/api/health"
        if self.test_http_endpoint(health_url):
            self.print_colored(f"{ICONS['check']} Backend server is {Colors.GREEN}HEALTHY{Colors.NC} ({BACKEND_URL})")
            self.results["backend"] = True
            
            # Test API endpoints
            self.print_colored(f"{ICONS['info']} Testing API endpoints...")
            
            endpoints = {
                "Reports API": f"{BACKEND_URL}/api/reports/uploads",
                "Projects API": f"{BACKEND_URL}/api/projects", 
                "Task Queue": f"{BACKEND_URL}/api/tasks"
            }
            
            for name, url in endpoints.items():
                if self.test_http_endpoint(url):
                    self.print_colored(f"  {ICONS['check']} {name}: {Colors.GREEN}OK{Colors.NC}")
                    if name == "Reports API":
                        self.results["api"] = True
                else:
                    self.print_colored(f"  {ICONS['warning']} {name}: {Colors.YELLOW}NOT AVAILABLE{Colors.NC}")
                    
            return True
        else:
            self.print_colored(f"{ICONS['cross']} Backend server is {Colors.RED}NOT RESPONDING{Colors.NC} ({BACKEND_URL})")
            self.print_colored(f"{ICONS['info']} Try: {Colors.CYAN}conda activate qenergy-backend && cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload{Colors.NC}")
            return False
            
    def check_database(self) -> bool:
        """Check database health"""
        self.print_colored(f"\n{Colors.BLUE}{ICONS['database']} Database Health Check{Colors.NC}")
        self.print_colored("----------------------------")
        
        db_healthy, error = self.test_database_connection()
        
        if db_healthy:
            db_info = f"{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
            self.print_colored(f"{ICONS['check']} PostgreSQL database is {Colors.GREEN}HEALTHY{Colors.NC} ({db_info})")
            self.results["database"] = True
            
            # Get and display stats
            stats = self.get_database_stats()
            if stats:
                self.print_colored(f"{ICONS['info']} Database statistics:")
                for table, count in stats.items():
                    if table != "recent_uploads_24h":
                        self.print_colored(f"  {table}: {count}")
                        
                recent_uploads = stats.get("recent_uploads_24h", 0)
                if recent_uploads > 0:
                    self.print_colored(f"  {ICONS['check']} Recent uploads (24h): {Colors.GREEN}{recent_uploads}{Colors.NC}")
                    self.results["uploads"] = True
                else:
                    self.print_colored(f"  {ICONS['info']} Recent uploads (24h): {Colors.YELLOW}0{Colors.NC}")
            
            return True
        else:
            self.print_colored(f"{ICONS['cross']} PostgreSQL database is {Colors.RED}NOT ACCESSIBLE{Colors.NC}")
            if error:
                self.print_colored(f"{ICONS['info']} Error: {error}")
            self.print_colored(f"{ICONS['info']} Check if PostgreSQL is running")
            return False
            
    def check_environment(self) -> None:
        """Check environment setup"""
        self.print_colored(f"\n{Colors.BLUE}🔧 Environment Check{Colors.NC}")
        self.print_colored("--------------------")
        
        # Check if we're in the right directory
        if os.path.exists("backend") and os.path.exists("frontend"):
            self.print_colored(f"{ICONS['check']} Project structure: {Colors.GREEN}VALID{Colors.NC}")
        else:
            self.print_colored(f"{ICONS['cross']} Project structure: {Colors.RED}INVALID{Colors.NC}")
            self.print_colored(f"{ICONS['info']} Run this script from the project root directory")
            
        # Check environment files
        if os.path.exists("backend/.env"):
            self.print_colored(f"{ICONS['check']} Backend .env file: {Colors.GREEN}EXISTS{Colors.NC}")
        else:
            self.print_colored(f"{ICONS['warning']} Backend .env file: {Colors.YELLOW}MISSING{Colors.NC}")
            
        if os.path.exists("frontend/.env.local"):
            self.print_colored(f"{ICONS['check']} Frontend .env.local file: {Colors.GREEN}EXISTS{Colors.NC}")
        else:
            self.print_colored(f"{ICONS['warning']} Frontend .env.local file: {Colors.YELLOW}MISSING{Colors.NC}")
            
        # Check dependencies
        if os.path.exists("frontend/node_modules"):
            self.print_colored(f"{ICONS['check']} Frontend dependencies: {Colors.GREEN}INSTALLED{Colors.NC}")
        else:
            self.print_colored(f"{ICONS['cross']} Frontend dependencies: {Colors.RED}MISSING{Colors.NC}")
            
    def generate_summary(self) -> int:
        """Generate health summary and return exit code"""
        self.print_colored(f"\n{Colors.PURPLE}📊 Health Summary{Colors.NC}")
        self.print_colored("==================")
        
        total_checks = len(self.results)
        healthy_checks = sum(self.results.values())
        
        status_items = [
            ("Frontend", self.results["frontend"]),
            ("Backend", self.results["backend"]), 
            ("Database", self.results["database"]),
            ("API Endpoints", self.results["api"]),
            ("Upload System", self.results["uploads"])
        ]
        
        for name, healthy in status_items:
            if healthy:
                self.print_colored(f"{ICONS['check']} {name}: {Colors.GREEN}HEALTHY{Colors.NC}")
            else:
                status = "UNHEALTHY" if name != "Upload System" else "NO RECENT ACTIVITY"
                color = Colors.RED if name != "Upload System" else Colors.YELLOW
                icon = ICONS['cross'] if name != "Upload System" else ICONS['warning']
                self.print_colored(f"{icon} {name}: {color}{status}{Colors.NC}")
                
        health_percentage = (healthy_checks * 100) // total_checks
        
        print()
        if health_percentage == 100:
            self.print_colored(f"{ICONS['rocket']} Overall Status: {Colors.GREEN}EXCELLENT{Colors.NC} ({health_percentage}%)")
            self.print_colored(f"{ICONS['check']} All systems operational! Ready for development.")
        elif health_percentage >= 80:
            self.print_colored(f"{ICONS['check']} Overall Status: {Colors.GREEN}GOOD{Colors.NC} ({health_percentage}%)")
            self.print_colored(f"{ICONS['info']} Most systems operational. Minor issues detected.")
        elif health_percentage >= 60:
            self.print_colored(f"{ICONS['warning']} Overall Status: {Colors.YELLOW}FAIR{Colors.NC} ({health_percentage}%)")
            self.print_colored(f"{ICONS['warning']} Some systems need attention.")
        else:
            self.print_colored(f"{ICONS['cross']} Overall Status: {Colors.RED}POOR{Colors.NC} ({health_percentage}%)")
            self.print_colored(f"{ICONS['cross']} Major issues detected. System may not function properly.")
            
        return 0 if health_percentage >= 80 else 1
        
    def show_quick_access(self) -> None:
        """Show quick access URLs"""
        self.print_colored(f"\n{Colors.BLUE}🔗 Quick Access URLs{Colors.NC}")
        self.print_colored("====================")
        self.print_colored(f"Frontend: {Colors.CYAN}{FRONTEND_URL}{Colors.NC}")
        self.print_colored(f"Backend API: {Colors.CYAN}{BACKEND_URL}/api{Colors.NC}")
        self.print_colored(f"API Health: {Colors.CYAN}{BACKEND_URL}/api/health{Colors.NC}")
        self.print_colored(f"API Docs: {Colors.CYAN}{BACKEND_URL}/docs{Colors.NC}")
        
    def run_health_check(self) -> int:
        """Run complete health check"""
        self.print_colored(f"{Colors.PURPLE}{ICONS['rocket']} QEnergy Platform Health Check{Colors.NC}")
        self.print_colored("==================================================")
        self.print_colored(f"Checking system health at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all checks
        self.check_frontend()
        self.check_backend() 
        self.check_database()
        self.check_environment()
        
        # Generate summary
        exit_code = self.generate_summary()
        
        # Show URLs
        self.show_quick_access()
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print()
        self.print_colored(f"Health check completed in {duration:.1f} seconds")
        
        return exit_code


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("QEnergy Platform Health Check")
        print("Usage: python health-check.py")
        print("\nThis script checks the health of:")
        print("- Frontend (Next.js)")
        print("- Backend (FastAPI)")
        print("- Database (PostgreSQL)")
        print("- API endpoints")
        print("- Upload system")
        return 0
        
    checker = HealthChecker()
    return checker.run_health_check()


if __name__ == "__main__":
    sys.exit(main())
