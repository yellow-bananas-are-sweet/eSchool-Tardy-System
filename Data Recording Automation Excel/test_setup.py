#!/usr/bin/env python3
"""
Test script to verify all required libraries are available
Run this before running the main application
"""

def test_imports():
    """Test all required imports"""
    try:
        import requests
        print("✓ requests library available")
    except ImportError as e:
        print(f"✗ requests library missing: {e}")
        return False

    try:
        import pandas as pd
        print("✓ pandas library available")
    except ImportError as e:
        print(f"✗ pandas library missing: {e}")
        return False

    try:
        import openpyxl
        print("✓ openpyxl library available")
    except ImportError as e:
        print(f"✗ openpyxl library missing: {e}")
        return False

    try:
        import tkinter as tk
        print("✓ tkinter library available")
        
        # Test basic tkinter functionality
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("✓ tkinter GUI functionality working")
        
    except ImportError as e:
        print(f"✗ tkinter library missing: {e}")
        return False
    except Exception as e:
        print(f"✗ tkinter GUI test failed: {e}")
        return False

    try:
        import json
        import base64
        import logging
        import threading
        import queue
        from datetime import datetime, timedelta
        from pathlib import Path
        print("✓ All standard library modules available")
    except ImportError as e:
        print(f"✗ Standard library module missing: {e}")
        return False

    return True

def test_file_operations():
    """Test file system operations"""
    try:
        from pathlib import Path
        
        # Test creating directory
        test_dir = Path("test_tardy_data")
        test_dir.mkdir(exist_ok=True)
        print("✓ Directory creation working")
        
        # Test Excel file creation
        import pandas as pd
        test_file = test_dir / "test_file.xlsx"
        df = pd.DataFrame({"Test": ["Data"]})
        df.to_excel(test_file, index=False)
        print("✓ Excel file creation working")
        
        # Clean up
        test_file.unlink()
        test_dir.rmdir()
        print("✓ File cleanup working")
        
        return True
        
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False

def main():
    print("Testing setup for Tardy Data Recording Automation...")
    print("=" * 50)
    
    imports_ok = test_imports()
    print()
    
    files_ok = test_file_operations()
    print()
    
    if imports_ok and files_ok:
        print("All tests passed! Your system is ready to run the tardy automation.")
        print("\nNext steps:")
        print("1. Save the main application code as 'tardy_monitor.py'")
        print("2. Get your Client ID and Client Secret from eSchoolData")
        print("3. Run: python3 tardy_monitor.py")
    else:
        print("Some tests failed. Please resolve the issues above before running the main application.")
    
    print("\nSystem Information:")
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")

if __name__ == "__main__":
    main()