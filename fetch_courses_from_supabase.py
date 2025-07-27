# Filename: fetch_courses_from_supabase.py
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Configuration ---
OUTPUT_DATA_DIR = 'data'
OUTPUT_FILE_NAME = 'courses.csv'

def init_supabase_client():
    """Initializes and returns the Supabase client."""
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("ERROR: Supabase URL or Service Key not found in .env file.")
        print("Please ensure your .env file is in the project root and contains the correct variables.")
        return None
        
    try:
        print("Connecting to Supabase...")
        return create_client(url, key)
    except Exception as e:
        print(f"Error creating Supabase client: {e}")
        return None

def fetch_courses_data(supabase: Client):
    """Fetches the master course list from the 'courses' table in Supabase."""
    print("--- Fetching Master Course List from Supabase ---")
    try:
        # Select all the columns relevant for our models and logic
        response = supabase.table('courses').select(
            'id, code, name, description, prerequisites, department, semester, credits'
        ).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename the 'id' column to 'course_id' for consistency across all our scripts
            df = df.rename(columns={'id': 'course_id'})
            
            output_path = os.path.join(OUTPUT_DATA_DIR, OUTPUT_FILE_NAME)
            df.to_csv(output_path, index=False)
            
            print(f"✅ Successfully fetched {len(df)} courses.")
            print(f"Data saved to: {output_path}")
        else:
            print("⚠️ No courses data found or an error occurred while fetching.")
            if hasattr(response, 'error'):
                print(f"Error details: {response.error}")

    except Exception as e:
        print(f"An unexpected error occurred during the fetch operation: {e}")

if __name__ == "__main__":
    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DATA_DIR):
        os.makedirs(OUTPUT_DATA_DIR)
        print(f"Created output directory: {OUTPUT_DATA_DIR}")
        
    supabase_client = init_supabase_client()
    
    if supabase_client:
        fetch_courses_data(supabase_client)
    else:
        print("\nCould not proceed with data fetching due to client initialization failure.")