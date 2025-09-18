from supabase import create_client, Client
from datetime import date

SUPABASE_URL = "https://gvwovsjkjeanyeyccyor.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2d292c2pramVhbnlleWNjeW9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5NjI2NjgsImV4cCI6MjA3MzUzODY2OH0.SzBKMxWfby2UNmVnSgvSjHwPISiXCFR3aQiRYBaZNgI"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2d292c2pramVhbnlleWNjeW9yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Nzk2MjY2OCwiZXhwIjoyMDczNTM4NjY4fQ.mPP7irVvx3TWjdLkw5O_0IpWd6FYHOcUvciqYkNzpQw"  # Из Settings → API
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def all_users() -> list:
    response = supabase.table('users').select('user_id').execute()
    users = [item['user_id'] for item in response.data]
    return users

def create_user(id, role = "user", refer_id = 0):
    if id in all_users():
        print("User already exists")
    else:
        new_user = {
            "user_id": id,
            "role": role,
            "refer_id":refer_id,
        }
        response = supabase.table('users').insert(new_user).execute()
        if response:
            print("User added")

def get_user_stats(id):
    if id not in all_users():
        print("No such user")
    else:
        role_response = supabase.table('users').select('role').eq('user_id',id).execute()
        role = role_response.data[0]['role']
        refer_id_response = supabase.table('users').select('refer_id').eq('user_id',id).execute()
        refer_id = refer_id_response.data[0]['refer_id']
        surveys_count_reponse = supabase.table('users').select('surveys_count').eq('user_id',id).execute()
        surveys_count = surveys_count_reponse.data[0]['surveys_count']
    res = {"role": role, "refer_id": refer_id, "surveys_count": surveys_count}
    return res
