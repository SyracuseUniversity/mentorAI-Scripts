import requests
import os

# ================================================
# STEP 1: Load your API key from the text file
# ================================================
try:
    with open('api_credentials.txt', 'r') as f:
        api_key = f.readline().strip()
    print("✅ API key loaded")
except FileNotFoundError:
    print("❌ Error: api_credentials.txt not found")
    exit()

# ================================================
# STEP 2: Configure your settings
# ================================================
org_id = "syracuse"                                   # Your organization
user_id = "jasidel"                                   # YOUR NetID - change this!
mentor_id = "25223e76-fc94-4cc2-aec1-f9fb51f0c2bf"   # Your mentor ID from URL
file_path = "We Are All Confident Idiots.pdf"        # File to upload

# ================================================
# STEP 3: Build the API endpoint URL
# ================================================
url = f"https://base.manager.ai.syr.edu/api/ai-index/orgs/{org_id}/users/{user_id}/documents/train/"

# ================================================
# STEP 4: Set up authentication
# ================================================
headers = {
    'Authorization': f'Api-Token {api_key}'
}
# NOTE: We DON'T set Content-Type here - Python does it automatically

print(f"🔄 Uploading file: {file_path}")
print(f"To mentor: {mentor_id}")
print(f"URL: {url}\n")

# ================================================
# STEP 5: Check if file exists
# ================================================
if not os.path.exists(file_path):
    print(f"❌ Error: File not found: {file_path}")
    print(f"Current directory: {os.getcwd()}")
    exit()

# ================================================
# STEP 6: Upload the file
# ================================================
try:
    # Open file in binary read mode
    with open(file_path, 'rb') as f:
        
        # Prepare the file for upload (multipart format)
        files = {
            'file': (os.path.basename(file_path), f, 'application/pdf')
            # Format: (filename, file_object, mime_type)
        }
        
        # Prepare other form fields
        data = {
            'pathway': mentor_id,  # Which mentor to train
            'type': 'pdf',         # File type
            'access': 'private'    # Visibility setting
        }
        
        # Make the API request
        # files= sends the file as multipart
        # data= sends other fields along with it
        response = requests.post(url, headers=headers, files=files, data=data)
        
        # ================================================
        # STEP 7: Check what happened
        # ================================================
        
        if response.status_code in [200, 201]:
            # Success!
            result = response.json()
            print("✅ SUCCESS!")
            print("=" * 60)
            print(f"Message: {result.get('message', 'N/A')}")
            print(f"Task ID: {result.get('task_id', 'N/A')}")
            print(f"Document ID: {result.get('document_id', 'N/A')}")
            print("=" * 60)
            print("\nYour mentor is now learning from this PDF!")
        
        elif response.status_code == 400:
            # Bad request - something wrong with what we sent
            print("❌ ERROR: 400 Bad Request")
            print(f"Response: {response.text}")
            print("\nCheck: pathway ID, file type, or other parameters")
        
        elif response.status_code == 401:
            # Unauthorized - API key problem
            print("❌ ERROR: 401 Unauthorized")
            print(f"Response: {response.text}")
            print("\nCheck: Your API key in api_credentials.txt")
        
        elif response.status_code == 404:
            # Not found - wrong URL or IDs
            print("❌ ERROR: 404 Not Found")
            print(f"Response: {response.text}")
            print("\nCheck: org_id, user_id, or mentor_id")
        
        elif response.status_code == 413:
            # File too large
            print("❌ ERROR: 413 File Too Large")
            print(f"Response: {response.text}")
        
        else:
            # Some other error
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
except FileNotFoundError:
    print(f"❌ Error: Could not open file: {file_path}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
