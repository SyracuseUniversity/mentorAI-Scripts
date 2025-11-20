import requests
import os

# Load API key
with open('api_credentials.txt', 'r') as f:
    api_key = f.readline().strip()

# Configuration
org_id = "syracuse"
user_id = "jasidel"  # Change to YOUR NetID
mentor_id = "25223e76-fc94-4cc2-aec1-f9fb51f0c2bf" # Change to YOUR mentor_id
file_path = "We Are All Confident Idiots.pdf" # Change to file_path

# Build request
url = f"https://base.manager.ai.syr.edu/api/ai-index/orgs/{org_id}/users/{user_id}/documents/train/"
headers = {'Authorization': f'Api-Token {api_key}'}

# Upload file
with open(file_path, 'rb') as f:
    files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
    data = {'pathway': mentor_id, 'type': 'pdf', 'access': 'private'}
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Success! Doc ID: {result.get('document_id')}")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
