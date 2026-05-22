# scratch/verify_views.py
import sys
import os
sys.path.append(os.getcwd())

try:
    import pandas as pd
    import streamlit as st
    print("Dependencies are okay.")
except ImportError as e:
    print(f"Dependency missing: {e}")

try:
    # Attempt to compile and check for syntax errors in page_operaciones.py
    import vistas.page_operaciones as po
    print("vistas/page_operaciones.py compiled successfully with no syntax errors!")
except Exception as e:
    print(f"Compilation/Syntax Error in page_operaciones.py: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
