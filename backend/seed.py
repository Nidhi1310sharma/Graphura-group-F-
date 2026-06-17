"""
Run once to insert demo credentials into Supabase.
  python -m backend.seed
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.supabase_client import supabase
from backend.auth import hash_password
from datetime import datetime, timezone

DEMO_ACCOUNTS = [
    {
        "email": "admin@scamshield.in",
        "password": "Admin@2026",
        "name": "ScamShield Admin",
        "role": "admin",
    },
    {
        "email": "demo@scamshield.in",
        "password": "Demo@2026",
        "name": "Demo User",
        "role": "user",
    },
]

def seed():
    for acc in DEMO_ACCOUNTS:
        existing = supabase.table("admin_users").select("id").eq("email", acc["email"]).execute()
        if existing.data:
            print(f"✓ Already exists: {acc['email']}")
            continue
        resp = supabase.table("admin_users").insert({
            "name": acc["name"],
            "email": acc["email"],
            "password_hash": hash_password(acc["password"]),
            "role": acc["role"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        if resp.data:
            print(f"✅ Created: {acc['email']} (role={acc['role']})")
        else:
            print(f"❌ Failed to create: {acc['email']}")

if __name__ == "__main__":
    seed()
