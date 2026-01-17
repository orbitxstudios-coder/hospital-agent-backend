import os
import sys
import json
import requests
from supabase import create_client, Client

# 1. SETUP & AUTH
# We fetch these secrets from GitHub Environment Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
VAPI_API_KEY = os.environ.get("VAPI_API_KEY")
VAPI_PHONE_ID = os.environ.get("VAPI_PHONE_ID")  # The Vapi number ID you bought
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")    # Your Vapi Agent ID

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. GET DATA FROM GOOGLE FORM (Passed via GitHub Action)
# The data comes in as a JSON string argument
try:
    payload = json.loads(sys.argv[1])
    patient_name = payload.get("name")
    phone_number = payload.get("phone")
except IndexError:
    print("Error: No data received.")
    sys.exit(1)

print(f"Processing: {patient_name} - {phone_number}")

# 3. SAVE TO SUPABASE (Initial Entry)
# We save it as 'pending' first.
data_to_insert = {
    "patient_name": patient_name,
    "phone": phone_number,
    "status": "pending_call",
    "source": "google_form"
}

try:
    response = supabase.table("appointments").insert(data_to_insert).execute()
    # Get the ID of the row we just created so we can track it later
    record_id = response.data[0]['id']
    print(f"Saved to Supabase. ID: {record_id}")
except Exception as e:
    print(f"Supabase Error: {e}")
    sys.exit(1)

# 4. TRIGGER VAPI CALL
# We pass the 'record_id' in metadata so the Agent knows which row to update later!
vapi_url = "https://api.vapi.ai/call"
vapi_headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}
vapi_payload = {
    "assistantId": ASSISTANT_ID,
    "phoneNumberId": VAPI_PHONE_ID,
    "customer": {
        "number": phone,
        "name": name
    },
    # THIS SECTION IS MISSING OR INCORRECT IN YOUR CURRENT SETUP
    "metadata": {
        "supabase_record_id": str(supabase_id) # The ID you got from inserting the row
    }
}

try:
    call_response = requests.post(vapi_url, json=vapi_payload, headers=vapi_headers)
    print(f"Vapi Call Status: {call_response.status_code}")
    print(call_response.text)
except Exception as e:
    print(f"Vapi Error: {e}")