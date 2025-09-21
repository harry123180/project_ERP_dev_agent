#!/usr/bin/env python3
"""
Technical Debt Analyzer for ERP System
Comprehensive assessment of code quality, architecture violations, and technical debt

BMad Master - Brownfield Modernization Assessment
"""

import os
import re
import json
import glob
from datetime import datetime
from pathlib import Path

class TechnicalDebtAnalyzer:
    def __init__(self):
        self.results = {}
        self.debt_score = 0
        self.total_checks = 0
        
    def log_debt(self, category, item, severity, description, recommendation, files=None):
        """Log technical debt item"""
        if category not in self.results:
            self.results[category] = []
            
        debt_item = {
            "item": item,
            "severity": severity,  # Critical, High, Medium, Low
            "description": description,
            "recommendation": recommendation,
            "files": files or [],
            "timestamp": datetime.now().isoformat()
        }
        
        self.results[category].append(debt_item)
        
        # Add to debt score
        severity_weights = {"Critical": 10, "High": 5, "Medium": 2, "Low": 1}
        self.debt_score += severity_weights.get(severity, 0)
        self.total_checks += 1
    
    def analyze_code_duplication(self):
        """Analyze code duplication across the project"""
        print("🔍 Analyzing Code Duplication...")
        
        # Check for duplicated import patterns
        python_files = glob.glob("**/*.py", recursive=True)
        vue_files = glob.glob("**/*.vue", recursive=True)
        
        # Common duplication patterns
        import_patterns = {}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Check for repeated import blocks
                imports = re.findall(r'^(import .+|from .+ import .+)$', content, re.MULTILINE)
                for imp in imports:
                    if imp in import_patterns:
                        import_patterns[imp].append(file_path)
                    else:
                        import_patterns[imp] = [file_path]
                        
            except Exception:
                continue
        
        # Find highly duplicated imports (possible code duplication)
        high_dup_imports = {k: v for k, v in import_patterns.items() if len(v) > 5}
        
        if high_dup_imports:
            self.log_debt("Code Quality", "Import duplication", "Medium",
                         f"Found {len(high_dup_imports)} highly duplicated import patterns",
                         "Consider creating shared modules or utilities",
                         list(high_dup_imports.keys())[:5])
        
        # Check for duplicated utility functions
        function_patterns = {}
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Look for function definitions
                functions = re.findall(r'^def (\w+)\(', content, re.MULTILINE)
                for func in functions:
                    if func in function_patterns:
                        function_patterns[func].append(file_path)
                    else:
                        function_patterns[func] = [file_path]
                        
            except Exception:
                continue
        
        # Find potentially duplicated functions
        dup_functions = {k: v for k, v in function_patterns.items() if len(v) > 2}
        
        if len(dup_functions) > 10:
            self.log_debt("Code Quality", "Function duplication", "High",
                         f"Found {len(dup_functions)} potentially duplicated function names",
                         "Review for actual code duplication and extract to shared utilities",
                         list(dup_functions.keys())[:10])
    
    def analyze_dependency_issues(self):
        """Analyze dependency and version issues"""
        print("📦 Analyzing Dependencies...")
        
        # Check Python dependencies
        requirements_files = glob.glob("**/requirements*.txt", recursive=True)
        if not requirements_files:
            self.log_debt("Dependencies", "Missing requirements file", "High",
                         "No requirements.txt found for Python dependencies",
                         "Create requirements.txt for reproducible builds")
        
        # Check for package.json issues
        package_json_files = glob.glob("**/package.json", recursive=True)
        for pkg_file in package_json_files:
            try:
                with open(pkg_file, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # Check for version ranges vs fixed versions
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                
                flexible_versions = []
                for dep, version in {**deps, **dev_deps}.items():
                    if "^" in version or "~" in version or "*" in version:
                        flexible_versions.append(f"{dep}: {version}")
                
                if len(flexible_versions) > 5:
                    self.log_debt("Dependencies", "Flexible version ranges", "Medium",
                                 f"Found {len(flexible_versions)} dependencies with flexible versions",
                                 "Consider using lockfiles or more specific versions for production",
                                 flexible_versions[:5])
                
                # Check for missing scripts
                scripts = package_data.get("scripts", {})
                expected_scripts = ["build", "dev", "test"]
                missing_scripts = [s for s in expected_scripts if s not in scripts]
                
                if missing_scripts:
                    self.log_debt("Dependencies", "Missing npm scripts", "Low",
                                 f"Missing npm scripts: {missing_scripts}",
                                 "Add missing scripts for consistency",
                                 [pkg_file])
                        
            except Exception as e:
                self.log_debt("Dependencies", "Package.json parse error", "High",
                             f"Error parsing {pkg_file}: {str(e)}",
                             "Fix package.json syntax errors",
                             [pkg_file])
    
    def analyze_deprecated_usage(self):
        """Analyze deprecated API and pattern usage"""
        print("⚠️ Analyzing Deprecated Usage...")
        
        # Check for deprecated Python patterns
        python_files = glob.glob("**/*.py", recursive=True)
        deprecated_patterns = [
            (r'imp\.', "imp module is deprecated, use importlib"),
            (r'os\.path\.walk', "os.path.walk is deprecated, use os.walk"),
            (r'platform\.dist\(\)', "platform.dist() is deprecated"),
            (r'assertEquals', "assertEquals is deprecated, use assertEqual"),
            (r'assertNotEquals', "assertNotEquals is deprecated, use assertNotEqual")
        ]
        
        deprecated_found = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern, message in deprecated_patterns:
                    if re.search(pattern, content):
                        deprecated_found.append(f"{file_path}: {message}")
                        
            except Exception:
                continue
        
        if deprecated_found:
            self.log_debt("Code Quality", "Deprecated API usage", "Medium",
                         f"Found {len(deprecated_found)} deprecated API usages",
                         "Update to modern API alternatives",
                         deprecated_found[:5])
        
        # Check for deprecated JavaScript/Vue patterns
        js_vue_files = glob.glob("**/*.js", recursive=True) + glob.glob("**/*.vue", recursive=True) + glob.glob("**/*.ts", recursive=True)
        js_deprecated_patterns = [
            (r'var\s+\w+', "var is deprecated, use let/const"),
            (r'\.substr\(', "substr() is deprecated, use substring() or slice()"),
            (r'new Date\(\)\.getYear\(\)', "getYear() is deprecated, use getFullYear()"),
        ]
        
        js_deprecated_found = []
        for file_path in js_vue_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern, message in js_deprecated_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        js_deprecated_found.append(f"{file_path}: {message} ({len(matches)} occurrences)")
                        
            except Exception:
                continue
        
        if js_deprecated_found:
            self.log_debt("Code Quality", "Deprecated JavaScript usage", "Medium",
                         f"Found deprecated JavaScript patterns in {len(js_deprecated_found)} files",
                         "Update to modern JavaScript/ES6+ patterns",
                         js_deprecated_found[:5])
    
    def analyze_missing_documentation(self):
        """Analyze missing or inadequate documentation"""
        print("📚 Analyzing Documentation...")
        
        # Check for README files
        readme_files = glob.glob("**/README.md", recursive=True) + glob.glob("**/readme.md", recursive=True)
        if not readme_files:
            self.log_debt("Documentation", "Missing README", "High",
                         "No README.md found in project root",
                         "Create comprehensive README with setup instructions")
        
        # Check for API documentation
        api_docs = glob.glob("**/api*.md", recursive=True) + glob.glob("**/API*.md", recursive=True)
        if not api_docs:
            self.log_debt("Documentation", "Missing API documentation", "Medium",
                         "No API documentation found",
                         "Create API documentation for endpoints")
        
        # Check Python files for docstrings
        python_files = glob.glob("**/*.py", recursive=True)
        undocumented_functions = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Find function definitions
                functions = re.findall(r'^def (\w+)\([^)]*\):', content, re.MULTILINE)
                
                # Check for docstrings after function definitions
                for func in functions:
                    func_pattern = rf'def {func}\([^)]*\):\s*\n\s*"""'
                    if not re.search(func_pattern, content, re.MULTILINE):
                        undocumented_functions.append(f"{file_path}::{func}")
                        
            except Exception:
                continue
        
        if len(undocumented_functions) > 20:
            self.log_debt("Documentation", "Missing function docstrings", "Medium",
                         f"Found {len(undocumented_functions)} functions without docstrings",
                         "Add docstrings to public functions",
                         undocumented_functions[:10])
    
    def analyze_architectural_violations(self):
        """Analyze architectural violations and anti-patterns"""
        print("🏗️ Analyzing Architecture...")
        
        # Check for circular imports (basic detection)
        python_files = glob.glob("**/*.py", recursive=True)
        import_graph = {}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Extract imports
                imports = re.findall(r'^from ([\w.]+) import', content, re.MULTILINE)
                imports += re.findall(r'^import ([\w.]+)', content, re.MULTILINE)
                
                module_name = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
                import_graph[module_name] = imports
                
            except Exception:
                continue
        
        # Simple circular dependency check
        potential_cycles = []
        for module, imports in import_graph.items():
            for imp in imports:
                if imp in import_graph and module in import_graph[imp]:
                    potential_cycles.append(f"{module} <-> {imp}")
        
        if potential_cycles:
            self.log_debt("Architecture", "Potential circular dependencies", "High",
                         f"Found {len(potential_cycles)} potential circular dependencies",
                         "Refactor to eliminate circular dependencies",
                         potential_cycles[:5])
        
        # Check for God objects/classes (large files)
        large_files = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    if lines > 500:
                        large_files.append(f"{file_path}: {lines} lines")
            except Exception:
                continue
        
        if large_files:
            self.log_debt("Architecture", "Oversized files", "Medium",
                         f"Found {len(large_files)} files with >500 lines",
                         "Consider breaking down large files into smaller modules",
                         large_files[:5])
        
        # Check for hardcoded values
        hardcoded_patterns = [
            (r'localhost:\d+', "Hardcoded localhost URLs"),
            (r'127\.0\.0\.1:\d+', "Hardcoded IP addresses"),
            (r'["\']admin["\']', "Hardcoded admin credentials"),
            (r'["\']password["\']', "Hardcoded passwords"),
        ]
        
        hardcoded_issues = []
        for file_path in python_files + glob.glob("**/*.js", recursive=True) + glob.glob("**/*.vue", recursive=True):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern, description in hardcoded_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        hardcoded_issues.append(f"{file_path}: {description} ({len(matches)} occurrences)")
                        
            except Exception:
                continue
        
        if hardcoded_issues:
            self.log_debt("Architecture", "Hardcoded values", "High",
                         f"Found hardcoded values in {len(hardcoded_issues)} files",
                         "Move hardcoded values to configuration",
                         hardcoded_issues[:5])
    
    def analyze_security_issues(self):
        """Analyze potential security issues"""
        print("🔒 Analyzing Security Issues...")
        
        # Check for potential security issues
        security_patterns = [
            (r'eval\(', "Use of eval() function"),
            (r'exec\(', "Use of exec() function"),
            (r'shell=True', "Shell execution enabled"),
            (r'password.*=.*["\'][^"\']+["\']', "Hardcoded passwords"),
            (r'secret.*=.*["\'][^"\']+["\']', "Hardcoded secrets"),
            (r'\.format\([^)]*\%', "Potential string formatting injection"),
        ]
        
        security_issues = []
        python_files = glob.glob("**/*.py", recursive=True)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern, description in security_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        security_issues.append(f"{file_path}: {description}")
                        
            except Exception:
                continue
        
        if security_issues:
            self.log_debt("Security", "Potential security issues", "Critical",
                         f"Found {len(security_issues)} potential security issues",
                         "Review and fix security vulnerabilities",
                         security_issues[:5])
        
        # Check for HTTPS enforcement
        config_files = glob.glob("**/*.py", recursive=True) + glob.glob("**/*.js", recursive=True)
        http_usage = []
        
        for file_path in config_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Look for HTTP URLs (not HTTPS)
                http_matches = re.findall(r'["\']http://[^"\']+["\']', content)
                if http_matches:
                    http_usage.append(f"{file_path}: {len(http_matches)} HTTP URLs")
                    
            except Exception:
                continue
        
        if http_usage:
            self.log_debt("Security", "HTTP usage instead of HTTPS", "Medium",
                         f"Found HTTP URLs in {len(http_usage)} files",
                         "Enforce HTTPS for all external communications",
                         http_usage[:5])
    
    def analyze_performance_issues(self):
        """Analyze potential performance issues"""
        print("⚡ Analyzing Performance Issues...")
        
        # Check for N+1 query patterns
        python_files = glob.glob("**/*.py", recursive=True)
        query_patterns = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Look for potential N+1 queries
                if re.search(r'for.*in.*:.*query\(', content, re.IGNORECASE):
                    query_patterns.append(f"{file_path}: Potential N+1 query pattern")
                    
                # Look for missing database indexes
                if re.search(r'filter\(.*==.*\)', content) and not re.search(r'index', content):
                    query_patterns.append(f"{file_path}: Filtering without indexes mentioned")
                    
            except Exception:
                continue
        
        if query_patterns:
            self.log_debt("Performance", "Database query issues", "Medium",
                         f"Found {len(query_patterns)} potential database performance issues",
                         "Review queries and add appropriate indexes",
                         query_patterns[:5])
        
        # Check for large file operations
        large_operations = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Look for file operations that could be memory intensive
                if re.search(r'\.read\(\)(?!\s*\()', content):
                    large_operations.append(f"{file_path}: Full file read operations")
                    
                if re.search(r'\.readlines\(\)', content):
                    large_operations.append(f"{file_path}: Reading all lines at once")
                    
            except Exception:
                continue
        
        if large_operations:
            self.log_debt("Performance", "Memory-intensive file operations", "Low",
                         f"Found {len(large_operations)} potentially memory-intensive operations",
                         "Consider streaming or chunked processing for large files",
                         large_operations[:5])
    
    def run_comprehensive_analysis(self):
        """Run comprehensive technical debt analysis"""
        print("🔍 BMad Master - Technical Debt Analysis")
        print("=" * 50)
        
        start_time = datetime.now()
        
        # Run all analysis categories
        self.analyze_code_duplication()
        self.analyze_dependency_issues()
        self.analyze_deprecated_usage()
        self.analyze_missing_documentation()
        self.analyze_architectural_violations()
        self.analyze_security_issues()
        self.analyze_performance_issues()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate report
        self.generate_debt_report(duration)
    
    def generate_debt_report(self, duration):
        """Generate comprehensive technical debt report"""
        print(f"\n📊 Technical Debt Analysis completed in {duration:.2f} seconds")
        print("=" * 50)
        
        # Calculate debt statistics
        total_items = sum(len(items) for items in self.results.values())
        
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for category_items in self.results.values():
            for item in category_items:
                severity_counts[item["severity"]] += 1
        
        debt_level = "LOW"
        if self.debt_score > 100:
            debt_level = "CRITICAL"
        elif self.debt_score > 50:
            debt_level = "HIGH"
        elif self.debt_score > 20:
            debt_level = "MEDIUM"
        
        print(f"\n🎯 TECHNICAL DEBT SUMMARY")
        print(f"Total Debt Score: {self.debt_score}")
        print(f"Debt Level: {debt_level}")
        print(f"Total Issues: {total_items}")
        print(f"Critical: {severity_counts['Critical']} | High: {severity_counts['High']} | Medium: {severity_counts['Medium']} | Low: {severity_counts['Low']}")
        
        # Priority recommendations
        print(f"\n💡 PRIORITY ACTIONS")
        print("-" * 30)
        
        critical_items = []
        high_items = []
        
        for category, items in self.results.items():
            for item in items:
                if item["severity"] == "Critical":
                    critical_items.append(f"{category}: {item['item']}")
                elif item["severity"] == "High":
                    high_items.append(f"{category}: {item['item']}")
        
        if critical_items:
            print(f"\n🚨 CRITICAL (Immediate Action Required):")
            for item in critical_items[:5]:
                print(f"  • {item}")
        
        if high_items:
            print(f"\n⚠️ HIGH PRIORITY:")
            for item in high_items[:5]:
                print(f"  • {item}")
        
        # Detailed results by category
        print(f"\n📋 DETAILED RESULTS BY CATEGORY")
        print("-" * 50)
        
        for category, items in self.results.items():
            if items:
                print(f"\n{category.upper()} ({len(items)} items)")
                for item in items:
                    severity_icon = {"Critical": "🚨", "High": "⚠️", "Medium": "📝", "Low": "💡"}[item["severity"]]
                    print(f"  {severity_icon} [{item['severity']}] {item['item']}")
                    print(f"      {item['description']}")
                    print(f"      Recommendation: {item['recommendation']}")
                    if item["files"]:
                        print(f"      Files: {item['files'][:3]}{'...' if len(item['files']) > 3 else ''}")
        
        # Save detailed report
        report_data = {
            "analysis_date": start_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_debt_score": self.debt_score,
                "debt_level": debt_level,
                "total_items": total_items,
                "severity_breakdown": severity_counts
            },
            "results": self.results
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"technical_debt_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed technical debt report saved to: {report_file}")
        print("=" * 50)
        
        return report_data

if __name__ == "__main__":
    analyzer = TechnicalDebtAnalyzer()
    analyzer.run_comprehensive_analysis()