import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Local development 
load_dotenv()


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") 
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Priority
key_to_use = SUPABASE_KEY if SUPABASE_KEY else SUPABASE_ANON_KEY

# Error check
if not SUPABASE_URL or not key_to_use:
    print("CRITICAL ERROR: SUPABASE_URL ya SUPABASE_KEY missing ")
    supabase = None
else:
    # Client initialize
    supabase: Client = create_client(SUPABASE_URL, key_to_use)
