import sys
import os
import subprocess

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"CWD: {os.getcwd()}")
print("Path:")
for p in sys.path:
    print(f"  - {p}")

try:
    import xlsxwriter
    print("SUCCESS: xlsxwriter imported!")
    print(f"Location: {xlsxwriter.__file__}")
except ImportError:
    print("FAILURE: xlsxwriter not found in this environment.")
    print("Attempting to install into this specific environment...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])
    try:
        import xlsxwriter
        print("SUCCESS: xlsxwriter installed and imported now!")
    except:
        print("CRITICAL: Failed to install/import even after attempt.")
