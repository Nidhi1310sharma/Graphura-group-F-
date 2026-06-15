from supabase import create_client
from dotenv import load_dotenv
import os

# Get the absolute path of the directory where THIS file lives (the backend folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")

# Load the .env file using its absolute path
load_dotenv(dotenv_path=env_path)

# print("URL:", os.getenv("SUPABASE_URL"))
# print("KEY:", os.getenv("SUPABASE_ANON_KEY"))

SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# print("Current dir:", current_dir)
# print("Env path:", env_path)
# print("Env exists:", os.path.exists(env_path))

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables.")

supabase =create_client(SUPABASE_URL,SUPABASE_SERVICE_KEY)
# supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def ping():
    """Check if Supabase is reachable."""
    try:
        supabase.table("admin_users").select("id").limit(1).execute()
        return True
    except Exception:
        return False