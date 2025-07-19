# Filename: 01_fetch_data.py
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# --- Supabase Connection ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Use service key for backend scripts

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key not found in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Fetch Courses Data ---
def fetch_courses_data():
    print("Fetching courses data...")
    response = supabase.table('courses').select('id, code, name, credits, stream_id, semester,description,department , status ,prerequisites  ').execute()
    if response.data:
        courses_df = pd.DataFrame(response.data)
        print(f"Fetched {len(courses_df)} courses.")
        courses_df.to_csv('data/courses.csv', index=False) # Save to CSV
        return courses_df
    else:
        print("No courses data found or error fetching courses.")
        return pd.DataFrame()

# --- Fetch Student Completed Courses Data (Interactions) ---
def fetch_student_completed_courses_data():
    print("Fetching student completed courses data...")
    # Adjust 'student_id_column' to your actual student identifier column name
    response = supabase.table('student_completed_courses').select('student_id, course_id, grade').execute()
    if response.data:
        interactions_df = pd.DataFrame(response.data)
        # Convert grade to a numerical scale if it's not already (e.g., A=4, B=3, etc.)
        # This is crucial for collaborative filtering.
        # Example:
        grade_mapping = {'A': 10, 'A-': 9,  'B': 8, 'B-': 7, 'C': 6, 'C-': 5,'D': 4, 'F': 2, 'I': 0 ,'S': 10} # 'S' for Satisfactory, 'U' for Unsatisfactory
        interactions_df['rating'] = interactions_df['grade'].map(grade_mapping).fillna(3) # Default to neutral if grade not in map

        print(f"Fetched {len(interactions_df)} student-course interactions.")
        interactions_df.to_csv('data/student_interactions.csv', index=False) # Save
        return interactions_df
    else:
        print("No student interactions data found or error fetching.")
        return pd.DataFrame()

# --- Fetch Student Interests Data ---
def fetch_student_interests_data():
    print("Fetching student interests data...")
    # Adjust table and column names as per your schema
    response = supabase.table('student_profiles').select('user_id, interests').execute() # Assuming 'interests' is a list/array of strings
    if response.data:
        interests_df = pd.DataFrame(response.data)
        interests_df.rename(columns={'user_id': 'student_id'}, inplace=True) # Match column name
        print(f"Fetched interests for {len(interests_df)} students.")
        interests_df.to_csv('data/student_interests.csv', index=False) # Save
        return interests_df
    else:
        print("No student interests data found or error fetching.")
        return pd.DataFrame()

if __name__ == "__main__":
    # Create a 'data' directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    courses_df = fetch_courses_data()
    interactions_df = fetch_student_completed_courses_data()
    interests_df = fetch_student_interests_data()

    print("\nSample Courses Data:")
    print(courses_df.head())
    print("\nSample Interactions Data:")
    print(interactions_df.head())
    print("\nSample Interests Data:")
    print(interests_df.head())
    print("\nData fetching complete. CSV files saved in 'data/' directory.")