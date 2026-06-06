from supabase_client import supabase
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
 
from dotenv import load_dotenv
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)
 
try:
    # Query your database table
    response = supabase.table('admin_users').select('*').execute()
    print("Database connection successful!")
    print("Data retrieved:", response.data)
except Exception as e:
    print("An error occurred during the query:", e)
