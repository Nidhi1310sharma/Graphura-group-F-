import os
from supabase import create_client, Client
from dotenv import load_dotenv

# For Local development 
load_dotenv()

# Enviroment variable values of render 
SUPABASE_URL = os.environ.get("SUPABASE_URL")
#SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY")
# priority check
key_to_use = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_ANON_KEY

# Error check 
if not SUPABASE_URL or not key_to_use:
    print("CRITICAL ERROR: SUPABASE_URL or SUPABASE_KEY/ANON_KEY is missing!")
    supabase = None
else:
    # Client initialize
    supabase: Client = create_client(SUPABASE_URL, key_to_use)
