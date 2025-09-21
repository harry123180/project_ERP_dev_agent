#!/usr/bin/env python3
"""
Database Health Check for ERP System
Comprehensive assessment of database status, schema, and performance
"""

import sqlite3
import json
import time
import os
from datetime import datetime

class DatabaseHealthCheck:
    def __init__(self):
        self.db_paths = [
            "backend/instance/erp_system.db",
            "backend/database.db", 
            "backend/erp_test.db"
        ]
        self.results = {}
        
    def check_database_file(self, db_path):
        """Check database file existence and basic connectivity"""
        results = {}
        
        if not os.path.exists(db_path):
            results["file_exists"] = {"status": "❌", "message": f"Database file not found: {db_path}"}
            return results
            
        results["file_exists"] = {"status": "✅", "message": f"Database file found: {db_path}"}
        
        # Check file size
        file_size = os.path.getsize(db_path)
        results["file_size"] = {
            "status": "✅" if file_size > 0 else "❌",
            "message": f"File size: {file_size:,} bytes",
            "size_bytes": file_size
        }
        
        # Check file permissions
        readable = os.access(db_path, os.R_OK)
        writable = os.access(db_path, os.W_OK)
        
        if readable and writable:
            results["permissions"] = {"status": "✅", "message": "Read/Write permissions OK"}
        elif readable:
            results["permissions"] = {"status": "⚠️", "message": "Read-only access"}
        else:
            results["permissions"] = {"status": "❌", "message": "No access permissions"}
            
        return results
    
    def check_database_schema(self, db_path):
        """Check database schema completeness and integrity"""
        if not os.path.exists(db_path):
            return {"schema_check": {"status": "❌", "message": "Database file not found"}}
            
        results = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            results["tables_found"] = {
                "status": "✅" if len(tables) > 0 else "❌",
                "message": f"Found {len(tables)} tables: {tables}",
                "count": len(tables),
                "tables": tables
            }
            
            # Check for required core tables
            required_tables = [
                "users", "suppliers", "request_orders", "purchase_orders",
                "request_order_items", "purchase_order_items", "item_categories"
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if not missing_tables:
                results["required_tables"] = {
                    "status": "✅",
                    "message": "All required tables present",
                    "required": required_tables
                }
            else:
                results["required_tables"] = {
                    "status": "❌",
                    "message": f"Missing required tables: {missing_tables}",
                    "missing": missing_tables,
                    "required": required_tables
                }
            
            # Check table row counts
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except Exception as e:
                    table_counts[table] = f"Error: {str(e)}"
            
            results["table_counts"] = {
                "status": "✅",
                "message": f"Table row counts retrieved",
                "counts": table_counts
            }
            
            # Check for indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
            indexes = [row[0] for row in cursor.fetchall()]
            
            results["indexes"] = {
                "status": "✅" if len(indexes) > 0 else "⚠️",
                "message": f"Found {len(indexes)} indexes",
                "count": len(indexes),
                "indexes": indexes
            }
            
            conn.close()
            
        except Exception as e:
            results["connection_error"] = {
                "status": "❌",
                "message": f"Database connection failed: {str(e)}"
            }
            
        return results
    
    def check_database_performance(self, db_path):
        """Check database performance metrics"""
        if not os.path.exists(db_path):
            return {"performance_check": {"status": "❌", "message": "Database file not found"}}
            
        results = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test simple query performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            query_time = (time.time() - start_time) * 1000
            
            if query_time < 10:
                status = "✅"
                message = "Fast query response"
            elif query_time < 100:
                status = "⚠️" 
                message = "Acceptable query response"
            else:
                status = "❌"
                message = "Slow query response"
                
            results["query_performance"] = {
                "status": status,
                "message": f"{message}: {query_time:.2f}ms",
                "response_time_ms": query_time
            }
            
            # Check database size vs content efficiency
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            db_size_calc = page_count * page_size
            file_size = os.path.getsize(db_path)
            
            results["storage_efficiency"] = {
                "status": "✅",
                "message": f"DB size: {db_size_calc:,} bytes, File size: {file_size:,} bytes",
                "calculated_size": db_size_calc,
                "file_size": file_size,
                "efficiency": (db_size_calc / file_size * 100) if file_size > 0 else 0
            }
            
            # Check for potential issues
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            results["integrity"] = {
                "status": "✅" if integrity == "ok" else "❌",
                "message": f"Integrity check: {integrity}",
                "result": integrity
            }
            
            conn.close()
            
        except Exception as e:
            results["performance_error"] = {
                "status": "❌",
                "message": f"Performance check failed: {str(e)}"
            }
            
        return results
    
    def check_database_constraints(self, db_path):
        """Check foreign key constraints and data consistency"""
        if not os.path.exists(db_path):
            return {"constraints_check": {"status": "❌", "message": "Database file not found"}}
            
        results = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check foreign key enforcement
            cursor.execute("PRAGMA foreign_keys")
            fk_status = cursor.fetchone()[0]
            
            results["foreign_keys"] = {
                "status": "✅" if fk_status else "⚠️",
                "message": f"Foreign key enforcement: {'ON' if fk_status else 'OFF'}",
                "enabled": bool(fk_status)
            }
            
            # Check for foreign key violations
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()
            
            results["fk_violations"] = {
                "status": "✅" if not violations else "❌",
                "message": f"Foreign key violations: {len(violations)}",
                "count": len(violations),
                "violations": violations[:10] if violations else []  # Limit to first 10
            }
            
            conn.close()
            
        except Exception as e:
            results["constraints_error"] = {
                "status": "❌",
                "message": f"Constraints check failed: {str(e)}"
            }
            
        return results
    
    def run_comprehensive_check(self):
        """Run comprehensive database health assessment"""
        print("🗄️ Database Health Check - ERP System")
        print("=" * 50)
        
        overall_results = {}
        
        for db_path in self.db_paths:
            print(f"\nChecking database: {db_path}")
            print("-" * 40)
            
            db_results = {}
            
            # File checks
            file_results = self.check_database_file(db_path)
            db_results.update(file_results)
            
            # Only continue with other checks if file exists
            if file_results.get("file_exists", {}).get("status") == "✅":
                # Schema checks
                schema_results = self.check_database_schema(db_path)
                db_results.update(schema_results)
                
                # Performance checks
                perf_results = self.check_database_performance(db_path)
                db_results.update(perf_results)
                
                # Constraint checks
                constraint_results = self.check_database_constraints(db_path)
                db_results.update(constraint_results)
            
            overall_results[db_path] = db_results
            
            # Print results for this database
            for check_name, result in db_results.items():
                status = result.get("status", "❓")
                message = result.get("message", "No message")
                print(f"  {status} {check_name}: {message}")
        
        # Generate summary
        self.generate_summary(overall_results)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"database_health_report_{timestamp}.json"
        
        report_data = {
            "assessment_date": datetime.now().isoformat(),
            "databases_checked": len(self.db_paths),
            "results": overall_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return overall_results
    
    def generate_summary(self, results):
        """Generate summary of database health"""
        print(f"\n📊 DATABASE HEALTH SUMMARY")
        print("=" * 50)
        
        accessible_dbs = 0
        healthy_dbs = 0
        total_issues = 0
        
        for db_path, db_results in results.items():
            if db_results.get("file_exists", {}).get("status") == "✅":
                accessible_dbs += 1
                
                # Count issues
                issues = sum(1 for result in db_results.values() 
                           if result.get("status") in ["❌", "⚠️"])
                
                if issues == 0:
                    healthy_dbs += 1
                    
                total_issues += issues
                
                print(f"\n📁 {db_path}")
                print(f"   Status: {'🟢 Healthy' if issues == 0 else '🟡 Issues Found' if issues < 3 else '🔴 Critical'}")
                print(f"   Issues: {issues}")
                
                # Show table counts if available
                if "table_counts" in db_results:
                    counts = db_results["table_counts"].get("counts", {})
                    if counts:
                        print(f"   Data: {sum(v for v in counts.values() if isinstance(v, int)):,} total records")
        
        print(f"\n🎯 OVERALL ASSESSMENT")
        print(f"   Accessible databases: {accessible_dbs}/{len(self.db_paths)}")
        print(f"   Healthy databases: {healthy_dbs}/{accessible_dbs}" if accessible_dbs > 0 else "   No accessible databases")
        print(f"   Total issues found: {total_issues}")
        
        # Recommendations
        if total_issues == 0:
            print(f"   ✅ All databases are healthy")
        elif total_issues < 5:
            print(f"   ⚠️ Minor issues found - recommended maintenance")
        else:
            print(f"   ❌ Critical issues found - immediate attention required")

if __name__ == "__main__":
    checker = DatabaseHealthCheck()
    checker.run_comprehensive_check()