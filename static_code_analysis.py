#!/usr/bin/env python3
"""
Static Code Analysis for ERP Backend
Analyzes the backend code structure without requiring runtime dependencies.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

def analyze_python_file(file_path):
    """Analyze a Python file for structure and imports"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract imports
    import_pattern = r'from\s+([^\s]+)\s+import|import\s+([^\s]+)'
    imports = []
    for match in re.finditer(import_pattern, content):
        if match.group(1):
            imports.append(f"from {match.group(1)} import")
        else:
            imports.append(f"import {match.group(2)}")
    
    # Extract class definitions
    class_pattern = r'class\s+(\w+).*?:'
    classes = re.findall(class_pattern, content)
    
    # Extract function definitions
    func_pattern = r'def\s+(\w+)\s*\('
    functions = re.findall(func_pattern, content)
    
    # Extract routes/endpoints
    route_pattern = r'@\w*\.route\s*\(\s*[\'"]([^\'"]+)'
    routes = re.findall(route_pattern, content)
    
    # Extract database models
    model_pattern = r'class\s+(\w+)\s*\(\s*db\.Model'
    models = re.findall(model_pattern, content)
    
    return {
        'file': str(file_path),
        'lines': len(content.splitlines()),
        'imports': imports,
        'classes': classes,
        'functions': functions,
        'routes': routes,
        'models': models
    }

def analyze_backend_structure():
    """Analyze the entire backend structure"""
    backend_path = Path(__file__).parent / 'backend'
    analysis = {
        'overview': {},
        'models': {},
        'routes': {},
        'files': []
    }
    
    # Find all Python files
    python_files = list(backend_path.rglob('*.py'))
    
    total_lines = 0
    total_classes = 0
    total_functions = 0
    total_routes = 0
    total_models = 0
    
    for py_file in python_files:
        file_analysis = analyze_python_file(py_file)
        analysis['files'].append(file_analysis)
        
        total_lines += file_analysis['lines']
        total_classes += len(file_analysis['classes'])
        total_functions += len(file_analysis['functions'])
        total_routes += len(file_analysis['routes'])
        total_models += len(file_analysis['models'])
        
        # Categorize by type
        relative_path = py_file.relative_to(backend_path)
        if 'models' in str(relative_path):
            analysis['models'][py_file.stem] = file_analysis
        elif 'routes' in str(relative_path):
            analysis['routes'][py_file.stem] = file_analysis
    
    analysis['overview'] = {
        'total_files': len(python_files),
        'total_lines': total_lines,
        'total_classes': total_classes,
        'total_functions': total_functions,
        'total_routes': total_routes,
        'total_models': total_models
    }
    
    return analysis

def analyze_frontend_structure():
    """Analyze the frontend structure"""
    frontend_path = Path(__file__).parent / 'frontend'
    analysis = {
        'overview': {},
        'components': {},
        'files': []
    }
    
    # Check package.json
    package_json_path = frontend_path / 'package.json'
    if package_json_path.exists():
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        analysis['package'] = package_data
    
    # Find Vue and JS files
    js_files = list(frontend_path.rglob('*.js')) + list(frontend_path.rglob('*.vue')) + list(frontend_path.rglob('*.ts'))
    
    total_lines = 0
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_analysis = {
                'file': str(js_file.relative_to(frontend_path)),
                'lines': len(content.splitlines()),
                'type': js_file.suffix
            }
            
            # Extract Vue component info
            if js_file.suffix == '.vue':
                # Look for component name
                name_match = re.search(r'name:\s*[\'"]([^\'"]+)', content)
                if name_match:
                    file_analysis['component_name'] = name_match.group(1)
                
                # Count template, script, style blocks
                file_analysis['has_template'] = '<template>' in content
                file_analysis['has_script'] = '<script>' in content or '<script setup>' in content
                file_analysis['has_style'] = '<style>' in content
            
            analysis['files'].append(file_analysis)
            total_lines += file_analysis['lines']
            
        except Exception as e:
            analysis['files'].append({
                'file': str(js_file.relative_to(frontend_path)),
                'error': str(e)
            })
    
    analysis['overview'] = {
        'total_files': len(js_files),
        'total_lines': total_lines
    }
    
    return analysis

def check_project_completeness():
    """Check if the project appears complete"""
    issues = []
    recommendations = []
    
    backend_path = Path(__file__).parent / 'backend'
    frontend_path = Path(__file__).parent / 'frontend'
    
    # Backend checks
    required_backend_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        'app/__init__.py',
        'app/models/__init__.py',
        'app/routes/__init__.py'
    ]
    
    for required_file in required_backend_files:
        file_path = backend_path / required_file
        if not file_path.exists():
            issues.append(f"Missing required backend file: {required_file}")
    
    # Frontend checks
    required_frontend_files = [
        'package.json',
        'index.html',
        'src/main.js',
        'src/App.vue'
    ]
    
    for required_file in required_frontend_files:
        file_path = frontend_path / required_file
        if not file_path.exists():
            issues.append(f"Missing required frontend file: {required_file}")
    
    # Check for key models
    models_path = backend_path / 'app' / 'models'
    key_models = ['user.py', 'supplier.py', 'request_order.py', 'purchase_order.py']
    for model in key_models:
        if not (models_path / model).exists():
            issues.append(f"Missing key model: {model}")
    
    # Check for key routes
    routes_path = backend_path / 'app' / 'routes'
    key_routes = ['auth.py', 'requisitions.py', 'purchase_orders.py']
    for route in key_routes:
        if not (routes_path / route).exists():
            issues.append(f"Missing key route: {route}")
    
    return {
        'issues': issues,
        'recommendations': recommendations,
        'completeness_score': max(0, 100 - len(issues) * 10)
    }

def main():
    """Run static analysis"""
    print("=" * 60)
    print("ERP PROJECT STATIC CODE ANALYSIS")
    print("=" * 60)
    
    results = {}
    
    print("\n1. Analyzing Backend Structure...")
    backend_analysis = analyze_backend_structure()
    results['backend'] = backend_analysis
    
    print(f"   Backend Overview:")
    print(f"   - Files: {backend_analysis['overview']['total_files']}")
    print(f"   - Lines of Code: {backend_analysis['overview']['total_lines']}")
    print(f"   - Models: {backend_analysis['overview']['total_models']}")
    print(f"   - Routes: {backend_analysis['overview']['total_routes']}")
    print(f"   - Functions: {backend_analysis['overview']['total_functions']}")
    
    print("\n2. Analyzing Frontend Structure...")
    frontend_analysis = analyze_frontend_structure()
    results['frontend'] = frontend_analysis
    
    print(f"   Frontend Overview:")
    print(f"   - Files: {frontend_analysis['overview']['total_files']}")
    print(f"   - Lines of Code: {frontend_analysis['overview']['total_lines']}")
    
    if 'package' in frontend_analysis:
        deps = len(frontend_analysis['package'].get('dependencies', {}))
        dev_deps = len(frontend_analysis['package'].get('devDependencies', {}))
        print(f"   - Dependencies: {deps} runtime, {dev_deps} development")
    
    print("\n3. Checking Project Completeness...")
    completeness = check_project_completeness()
    results['completeness'] = completeness
    
    print(f"   Completeness Score: {completeness['completeness_score']}%")
    if completeness['issues']:
        print("   Issues Found:")
        for issue in completeness['issues'][:5]:  # Show first 5
            print(f"   - {issue}")
        if len(completeness['issues']) > 5:
            print(f"   - ... and {len(completeness['issues']) - 5} more issues")
    
    # Save results
    results_file = Path(__file__).parent / 'artifacts' / 'static_analysis_results.json'
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return results

if __name__ == '__main__':
    main()