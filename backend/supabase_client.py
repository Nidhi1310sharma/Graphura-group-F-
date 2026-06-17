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



# Environment variables fetching
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# checikng variable match
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing in environment variables!")
if not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_ANON_KEY is missing in environment variables!")
if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY is missing in environment variables!")

# Client initialization
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
