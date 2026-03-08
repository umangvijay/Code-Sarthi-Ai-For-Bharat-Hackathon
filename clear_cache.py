#!/usr/bin/env python3
"""
Clear Python bytecode cache and verify rag_engine.py syntax
"""
import os
import shutil
import py_compile
import sys

def clear_pycache():
    """Remove all __pycache__ directories and .pyc files"""
    print("🧹 Clearing Python cache...")
    count = 0
    
    for root, dirs, files in os.walk('.'):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                print(f"   Removed: {cache_dir}")
                count += 1
            except Exception as e:
                print(f"   Error removing {cache_dir}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                try:
                    os.remove(pyc_file)
                    print(f"   Removed: {pyc_file}")
                    count += 1
                except Exception as e:
                    print(f"   Error removing {pyc_file}: {e}")
    
    print(f"✅ Cleared {count} cache files/directories\n")

def verify_syntax(filename):
    """Verify Python file syntax"""
    print(f"🔍 Verifying syntax of {filename}...")
    try:
        py_compile.compile(filename, doraise=True)
        print(f"✅ {filename} syntax is correct!\n")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in {filename}:")
        print(f"   {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Python Cache Cleaner & Syntax Verifier")
    print("=" * 60 + "\n")
    
    # Clear cache
    clear_cache()
    
    # Verify rag_engine.py
    if verify_syntax('rag_engine.py'):
        print("🎉 All checks passed! You can now restart Streamlit.")
        sys.exit(0)
    else:
        print("⚠️  Syntax errors found. Please fix them before restarting.")
        sys.exit(1)
