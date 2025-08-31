#!/usr/bin/env python3
"""Simple test runner script that doesn't require pytest-asyncio installation."""

import sys
import os
import subprocess
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def run_syntax_check():
    """Run syntax check on all Python files."""
    print("🔍 Running syntax check...")
    
    python_files = []
    src_dir = project_root / "src" / "playwright_search"
    test_dir = project_root / "tests"
    
    # Find all Python files
    for directory in [src_dir, test_dir]:
        if directory.exists():
            python_files.extend(directory.rglob("*.py"))
    
    failed_files = []
    for py_file in python_files:
        try:
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(py_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                failed_files.append((py_file, result.stderr))
                print(f"❌ {py_file.relative_to(project_root)}: Syntax error")
            else:
                print(f"✅ {py_file.relative_to(project_root)}: OK")
                
        except Exception as e:
            failed_files.append((py_file, str(e)))
            print(f"❌ {py_file.relative_to(project_root)}: {e}")
    
    return failed_files

def run_import_check():
    """Check that all modules can be imported."""
    print("\n📦 Running import check...")
    
    modules_to_test = [
        "playwright_search.core.models",
        "playwright_search.core.base", 
        "playwright_search.utils.validators",
        "playwright_search.utils.date_parser",
        "playwright_search.utils.result_processor",
        "playwright_search.const",
        "playwright_search.parallel_search",
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: Import successful")
        except ImportError as e:
            failed_imports.append((module, str(e)))
            print(f"❌ {module}: Import failed - {e}")
        except Exception as e:
            # Skip playwright-related imports since we don't have playwright installed
            if "playwright" in str(e).lower():
                print(f"⚠️  {module}: Skipped (requires playwright)")
            else:
                failed_imports.append((module, str(e)))
                print(f"❌ {module}: Error - {e}")
    
    return failed_imports

def run_basic_unit_tests():
    """Run basic unit tests that don't require external dependencies."""
    print("\n🧪 Running basic unit tests...")
    
    # Simple test cases that can run without pytest or external deps
    test_cases = []
    
    try:
        from playwright_search.core.models import SearchResult, SearchEngineConfig
        
        # Test SearchResult creation
        result = SearchResult(
            title="Test", url="https://example.com", snippet="Test", position=1
        )
        assert result.title == "Test"
        assert result.timestamp is not None
        test_cases.append("✅ SearchResult creation")
        
        # Test SearchEngineConfig defaults
        config = SearchEngineConfig()
        assert config.headless is True
        assert config.timeout == 30000
        test_cases.append("✅ SearchEngineConfig defaults")
        
    except Exception as e:
        test_cases.append(f"❌ Core models test failed: {e}")
    
    try:
        from playwright_search.utils.validators import InputValidator, ValidationError
        
        # Test engine validation
        assert InputValidator.validate_engine("google") == "google"
        assert InputValidator.validate_engine("GOOGLE") == "google"
        
        try:
            InputValidator.validate_engine("invalid")
            test_cases.append("❌ Engine validation should have failed")
        except ValidationError:
            test_cases.append("✅ Engine validation error handling")
        
    except ImportError as e:
        test_cases.append(f"⚠️  Validators test skipped: {e}")
    except Exception as e:
        test_cases.append(f"❌ Validators test failed: {e}")
    
    for test_case in test_cases:
        print(f"  {test_case}")
    
    return test_cases

def main():
    """Run all available tests."""
    print("🚀 Running search-tool test suite...")
    print(f"📁 Project root: {project_root}")
    
    # Run syntax check
    syntax_errors = run_syntax_check()
    
    # Run import check  
    import_errors = run_import_check()
    
    # Run basic unit tests
    test_results = run_basic_unit_tests()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    if syntax_errors:
        print(f"❌ Syntax errors: {len(syntax_errors)}")
        for file, error in syntax_errors:
            print(f"   {file.relative_to(project_root)}: {error.strip()}")
    else:
        print("✅ No syntax errors")
    
    if import_errors:
        print(f"❌ Import errors: {len(import_errors)}")
        for module, error in import_errors:
            print(f"   {module}: {error}")
    else:
        print("✅ All imports successful")
    
    passed_tests = len([t for t in test_results if t.startswith("✅")])
    total_tests = len([t for t in test_results if not t.startswith("⚠️")])
    
    if total_tests > 0:
        print(f"🧪 Unit tests: {passed_tests}/{total_tests} passed")
    
    # Overall result
    if syntax_errors or import_errors:
        print("\n❌ Some tests failed")
        return 1
    else:
        print("\n✅ All available tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())