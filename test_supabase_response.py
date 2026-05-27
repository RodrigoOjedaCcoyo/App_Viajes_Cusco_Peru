"""
Test script to verify Supabase SDK response handling
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test simple data insertion and check response
def test_supabase_response():
    """Test what Supabase SDK returns on insert/update"""
    from supabase import create_client, Client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    URL = os.getenv("SUPABASE_URL")
    KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if not URL or not KEY:
        print("❌ Supabase credentials not found in .env")
        return
    
    client = create_client(URL, KEY)
    
    print("Testing Supabase INSERT response...\n")
    
    # 1. Try a simple insert with test data
    test_data = {
        "nombre": "TEST_ITEM",
        "valor": 123.45,
        "activo": True
    }
    
    print(f"Attempting INSERT with data: {test_data}\n")
    
    try:
        # Try inserting into a simple table if it exists
        res = client.table('test_table').insert(test_data).execute()
        
        print(f"Response type: {type(res)}")
        print(f"Response dir: {[x for x in dir(res) if not x.startswith('_')]}")
        print(f"Has .data: {hasattr(res, 'data')}")
        print(f"res.data = {res.data}")
        print(f"res.data type = {type(res.data)}")
        print(f"bool(res.data) = {bool(res.data) if res.data is not None else 'None'}")
        
        # Also check for other attributes
        if hasattr(res, 'count'):
            print(f"res.count = {res.count}")
        if hasattr(res, 'status_code'):
            print(f"res.status_code = {res.status_code}")
        
    except Exception as e:
        print(f"Exception during test: {type(e).__name__}: {e}")
        # If table doesn't exist, that's okay - we're just testing response format

if __name__ == "__main__":
    test_supabase_response()
