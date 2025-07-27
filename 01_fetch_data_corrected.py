# Filename: 01_fetch_data_corrected.py
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Configuration ---
OUTPUT_DATA_DIR = 'data'
GRADE_TO_RATING_MAPPING = {
    'A+': 10.0, 'A': 9.0, 'A-': 8.5, 'B+': 8.0, 'B': 7.0, 'B-': 6.5,
    'C+': 6.0, 'C': 5.0, 'C-': 4.5, 'D+': 4.0, 'D': 3.0,
    'P': 5.0, 'PASS': 5.0, 'F': 1.0, 'FAIL': 1.0, 'S': 7.0, 'U': 1.0,
}
DEFAULT_RATING_FOR_UNKNOWN_GRADE = 3.0

def init_supabase_client():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("ERROR: Supabase URL or Service Key not found.")
        return None
    return create_client(url, key)

def fetch_courses_data(supabase: Client):
    print("--- 1. Fetching Master Course List from Supabase ---")
    try:
        # <<< CHANGE 1: Corrected table name to 'courses_iiitd'
        response = supabase.table('courses_iiitd').select('id, code, name, description, prerequisites, department, semester, credits').execute()
        if response.data:
            df = pd.DataFrame(response.data).rename(columns={'id': 'course_id'})
            df.to_csv(os.path.join(OUTPUT_DATA_DIR, 'courses.csv'), index=False)
            print(f"✅ Successfully fetched {len(df)} courses.")
        else:
            print("⚠️ No data found in 'courses_iiitd' table.")
    except Exception as e:
        print(f"An error occurred while fetching courses: {e}")

def fetch_student_interactions(supabase: Client):
    print("\n--- 2. Fetching Student Interactions from Supabase ---")
    try:
        # <<< CHANGE 2: Corrected table name to 'user_semester_courses'
        response = supabase.table('user_semester_courses').select('user_id, course_id, grade, status').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df_completed = df[df['status'].str.lower().isin(['complete', 'completed', 'failed'])].copy()
            if df_completed.empty:
                 print("⚠️ No interactions with 'complete' or 'failed' status found.")
                 return
            df_completed['rating'] = df_completed['grade'].str.strip().str.upper().map(GRADE_TO_RATING_MAPPING)
            df_completed.fillna({'rating': DEFAULT_RATING_FOR_UNKNOWN_GRADE}, inplace=True)
            final_df = df_completed[['user_id', 'course_id', 'rating']]
            final_df.to_csv(os.path.join(OUTPUT_DATA_DIR, 'student_interactions.csv'), index=False)
            print(f"✅ Successfully processed {len(final_df)} student interactions.")
        else:
            print("⚠️ No data found in 'user_semester_courses' table.")
    except Exception as e:
        print(f"An error occurred while fetching interactions: {e}")

def fetch_student_preferences(supabase: Client):
    print("\n--- 3. Fetching Student Preferences from Supabase ---")
    try:
        # <<< CHANGE 3: Corrected table name to 'user_course_preferences'
        cols_to_select = 'user_id, career_goal, technical_skills, primary_interest, secondary_interest, improvement_areas'
        response = supabase.table('user_course_preferences').select(cols_to_select).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            text_cols = [col for col in cols_to_select.split(', ') if col != 'user_id']
            for col in text_cols:
                df[col] = df[col].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x) if pd.notna(x) else '')
            df['interests_combined'] = df[text_cols].agg(' '.join, axis=1)
            df['interests_combined'] = df['interests_combined'].str.replace(r'\s+', ' ', regex=True).str.strip()
            final_df = df[['user_id', 'interests_combined']]
            final_df.to_csv(os.path.join(OUTPUT_DATA_DIR, 'student_preferences.csv'), index=False)
            print(f"✅ Successfully processed {len(final_df)} student preferences.")
        else:
            print("⚠️ No data found in 'user_course_preferences' table.")
    except Exception as e:
        print(f"An error occurred while fetching preferences: {e}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DATA_DIR):
        os.makedirs(OUTPUT_DATA_DIR)
    
    supabase_client = init_supabase_client()
    if supabase_client:
        fetch_courses_data(supabase_client)
        fetch_student_interactions(supabase_client)
        fetch_student_preferences(supabase_client)
        print("\n--- Data fetching pipeline finished! ---")
    else:
        print("\nCould not initialize Supabase client.")