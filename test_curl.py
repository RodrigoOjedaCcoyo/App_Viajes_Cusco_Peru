import os
import re
import urllib.request
import json

def test_pago():
    try:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        with open(secrets_path, "r") as f:
            content = f.read()
            
        supa_url = re.search(r'URL\s*=\s*"([^"]+)"', content).group(1)
        supa_key = re.search(r'ANON_KEY\s*=\s*"([^"]+)"', content).group(1)
        
        url = f"{supa_url}/rest/v1/pago?select=*"
        headers = {
            "apikey": supa_key,
            "Authorization": f"Bearer {supa_key}",
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"PAGO ROWS COUNT: {len(data)}")
            if data:
                print("SAMPLE ROW:", data[0])
            
    except Exception as e:
        print("GENERAL ERROR:", repr(e))

if __name__ == "__main__":
    test_pago()
