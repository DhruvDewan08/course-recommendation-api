# Filename: debug_env.py
import os
from dotenv import load_dotenv

print("--- Starting Environment Debug ---")

# 1. Print the Current Working Directory (where the script is running from)
cwd = os.getcwd()
print(f"Current Working Directory (CWD): {cwd}")

# 2. Construct the expected path to the .env file
env_path = os.path.join(cwd, '.env')
print(f"Expected .env file path: {env_path}")

# 3. Check if the .env file actually exists at that path
file_exists = os.path.exists(env_path)
print(f"Does the .env file exist at this path? -> {file_exists}")

if not file_exists:
    print("\nERROR: The .env file was NOT found in the current directory.")
    print("Please check the file's location and name (make sure it's not .env.txt).")
else:
    print("\n.env file was found! Attempting to load variables...")
    # 4. Load the .env file
    load_dotenv()

    # 5. Check for the specific variables
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")

    print(f"Value for SUPABASE_URL: {url}")
    print(f"Value for SUPABASE_SERVICE_KEY (first 10 chars): {key[:10] if key else None}...")
    
    if not url or not key:
        print("\nERROR: Variables not loaded. Please check the variable names inside your .env file.")
    else:
        print("\n✅ SUCCESS: Variables were loaded correctly!")

print("\n--- Debug Finished ---")