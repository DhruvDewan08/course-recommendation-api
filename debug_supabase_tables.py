# Filename: debug_supabase_tables.py
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def test_environment_variables():
    """Test different environment variable names to see which ones exist."""
    print("=== Testing Environment Variables ===")
    
    # Test different possible environment variable names
    env_vars_to_test = [
        "SUPABASE_URL", "VITE_SUPABASE_URL",
        "SUPABASE_SERVICE_KEY", "VITE_SUPABASE_SERVICE_KEY",
        "SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY"
    ]
    
    for var_name in env_vars_to_test:
        value = os.environ.get(var_name)
        if value:
            print(f"✅ {var_name}: {value[:20]}..." if len(value) > 20 else f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: Not found")

def test_supabase_connection():
    """Test Supabase connection with different environment variable combinations."""
    print("\n=== Testing Supabase Connection ===")
    
    # Try different combinations
    combinations = [
        ("SUPABASE_URL", "SUPABASE_SERVICE_KEY"),
        ("VITE_SUPABASE_URL", "VITE_SUPABASE_SERVICE_KEY"),
        ("SUPABASE_URL", "VITE_SUPABASE_SERVICE_KEY"),
        ("VITE_SUPABASE_URL", "SUPABASE_SERVICE_KEY")
    ]
    
    for url_var, key_var in combinations:
        url = os.environ.get(url_var)
        key = os.environ.get(key_var)
        
        if url and key:
            print(f"\nTrying combination: {url_var} + {key_var}")
            try:
                supabase = create_client(url, key)
                print("✅ Connection successful!")
                return supabase
            except Exception as e:
                print(f"❌ Connection failed: {e}")
        else:
            print(f"\n❌ Missing variables: {url_var} or {key_var}")
    
    return None

def list_available_tables(supabase):
    """List all available tables in the database."""
    print("\n=== Listing Available Tables ===")
    
    # Try to query information_schema to get table names
    try:
        response = supabase.rpc('get_tables').execute()
        if response.data:
            print("Tables found via RPC:")
            for table in response.data:
                print(f"  - {table}")
    except:
        print("Could not get tables via RPC, trying direct queries...")
    
    # Try common table names that might exist
    common_tables = [
        'courses', 'course', 'course_info',
        'student_completed_courses', 'user_semester_courses', 'student_courses',
        'student_profiles', 'user_course_preferences', 'user_preferences',
        'users', 'students'
    ]
    
    existing_tables = []
    for table_name in common_tables:
        try:
            response = supabase.table(table_name).select('*').limit(1).execute()
            if response.data is not None:
                print(f"✅ Table '{table_name}' exists")
                existing_tables.append(table_name)
            else:
                print(f"❌ Table '{table_name}' does not exist")
        except Exception as e:
            print(f"❌ Table '{table_name}' error: {e}")
    
    return existing_tables

def inspect_table_structure(supabase, table_name):
    """Inspect the structure of a specific table."""
    print(f"\n=== Inspecting Table: {table_name} ===")
    try:
        response = supabase.table(table_name).select('*').limit(5).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            print(f"Columns: {list(df.columns)}")
            print(f"Sample data:")
            print(df.head())
            return df.columns.tolist()
        else:
            print("No data found in table")
            return []
    except Exception as e:
        print(f"Error inspecting table: {e}")
        return []

if __name__ == "__main__":
    test_environment_variables()
    supabase = test_supabase_connection()
    
    if supabase:
        existing_tables = list_available_tables(supabase)
        
        if existing_tables:
            print(f"\n=== Found {len(existing_tables)} existing tables ===")
            for table in existing_tables:
                inspect_table_structure(supabase, table)
        else:
            print("\nNo existing tables found with common names.")
    else:
        print("\nCould not establish Supabase connection. Please check your environment variables.") 