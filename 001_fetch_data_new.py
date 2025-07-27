# Filename: 01_fetch_data.py
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import ast # For safely evaluating string representations of lists

load_dotenv() # Load environment variables from .env file

# --- Supabase Connection ---
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_SERVICE_KEY") # Use service key for backend scripts

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key not found in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Define Grade to Rating Mapping ---
# Adjust this mapping based on your actual grade values and desired numerical scale
# Ensure a consistent numerical scale, e.g., 1 (worst) to 5 (best) or 0-10.
# The 'surprise' library typically expects a min/max rating scale.
GRADE_TO_RATING_MAPPING = {
    'A+': 10.0, 'A': 9.0, 'A-': 8.5,
    'B+': 8.0, 'B': 7.0, 'B-': 6.5,
    'C+': 6.0, 'C': 5.0, 'C-': 4.5,
    'D+': 4.0, 'D': 3.0,
    'P': 5.0,  # Pass
    'S': 7.0,  # Satisfactory (often used for non-graded courses)
    'F': 1.0,  # Fail
    'U': 1.0,  # Unsatisfactory
    # Add any other grades present in your 'user_semester_courses' table
}
DEFAULT_RATING_FOR_UNKNOWN_GRADE = 3.0 # A neutral rating for unmapped grades

# --- Fetch Courses Data ---
def fetch_courses_data():
    print("Fetching courses data...")
    # Since there's no dedicated courses table, we'll extract unique course information
    # from the user_semester_courses table
    try:
        response = supabase.table('user_semester_courses').select('course_uuid, course_acronym').execute()
        if response.data:
            courses_df = pd.DataFrame(response.data)
            # Remove duplicates and create a proper courses dataframe
            courses_df = courses_df.drop_duplicates(subset=['course_uuid'])
            courses_df.rename(columns={'course_uuid': 'course_id', 'course_acronym': 'code'}, inplace=True)
            
            # Add placeholder columns for missing data (you can populate these later)
            courses_df['name'] = courses_df['code']  # Use code as name for now
            courses_df['description'] = ''  # Empty for now
            courses_df['prerequisites'] = ''  # Empty for now
            courses_df['department'] = ''  # Empty for now
            courses_df['semester'] = ''  # Empty for now
            courses_df['credits'] = 0  # Default to 0 for now
            
            print(f"Fetched {len(courses_df)} unique courses from user_semester_courses.")
            courses_df.to_csv('data/courses.csv', index=False)
            return courses_df
        else:
            print("No courses data found in user_semester_courses.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching courses data: {e}")
        return pd.DataFrame()

# --- Fetch Student Completed Courses Data (Interactions for CF) ---
def fetch_student_interactions_data():
    print("Fetching student completed courses data (interactions)...")
    try:
        response = supabase.table('user_semester_courses') \
                           .select('user_id, course_uuid, grade, status') \
                           .eq('status', 'completed') \
                           .execute()

        print(f"DEBUG: Supabase raw response object type: {type(response)}")
        # The 'execute()' method typically returns a ModelResponse or APIResponse object
        # from postgrest-py (used by supabase-py)
        # Let's inspect its attributes

        if hasattr(response, 'data'):
            print(f"DEBUG: response.data type: {type(response.data)}")
            print(f"DEBUG: response.data content (first 500 chars): {str(response.data)[:500]}")
            if isinstance(response.data, list):
                print(f"DEBUG: Number of records in response.data: {len(response.data)}")
            else:
                print("DEBUG: response.data is not a list.")
        else:
            print("DEBUG: response object does not have a 'data' attribute.")

        if hasattr(response, 'error'):
            print(f"DEBUG: response.error type: {type(response.error)}")
            print(f"DEBUG: response.error content: {response.error}")
        else:
            print("DEBUG: response object does not have an 'error' attribute.")

        if hasattr(response, 'count'):
             print(f"DEBUG: response.count: {response.count}")
        else:
             print("DEBUG: response object does not have a 'count' attribute.")


        # Proceed only if data is present and is a list
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            interactions_df = pd.DataFrame(response.data)
            if interactions_df.empty:
                print("DataFrame is empty after creation, though response.data was not.")
                interactions_df.to_csv('data/student_interactions.csv', index=False)
                return interactions_df # Return empty df

            print("DEBUG: Raw interactions_df before grade mapping:")
            print(interactions_df.head())

            # Rename course_uuid to course_id for consistency
            interactions_df.rename(columns={'course_uuid': 'course_id'}, inplace=True)

            interactions_df['rating'] = interactions_df['grade'].str.upper().map(GRADE_TO_RATING_MAPPING)
            interactions_df['rating'] = interactions_df['rating'].fillna(DEFAULT_RATING_FOR_UNKNOWN_GRADE)

            print(f"Fetched and processed {len(interactions_df)} 'completed' student-course interactions.")
            interactions_df[['user_id', 'course_id', 'rating']].to_csv('data/student_interactions.csv', index=False)
            return interactions_df[['user_id', 'course_id', 'rating']]
        else:
            print("No 'completed' student-course interactions found in response.data or response.data was not a list.")
            # Create an empty DataFrame with expected columns if none found
            empty_df = pd.DataFrame(columns=['user_id', 'course_id', 'rating'])
            empty_df.to_csv('data/student_interactions.csv', index=False)
            return empty_df

    except Exception as e:
        print(f"ERROR during Supabase call or processing in fetch_student_interactions_data: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
        empty_df = pd.DataFrame(columns=['user_id', 'course_id', 'rating'])
        empty_df.to_csv('data/student_interactions.csv', index=False)
        return empty_df

# --- Fetch Student Preferences/Interests Data ---
def fetch_student_preferences_data():
    print("Fetching student preferences/interests data...")
    response = supabase.table('user_course_preferences') \
                       .select('user_id, career_goal, technical_skills, improvement_areas, primary_interest, secondary_interest') \
                       .execute()
    if response.data:
        preferences_df = pd.DataFrame(response.data)
        # preferences_df.rename(columns={'user_id': 'student_id'}, inplace=True)

        # Combine relevant text fields into a single 'interests_text' field
        # Handle TEXT[] arrays: join them into space-separated strings
        def process_text_array(arr):
            if arr is None:
                return ""
            if isinstance(arr, str): # If it's already a string (e.g. from CSV load)
                try:
                    # Try to evaluate if it's a string representation of a list
                    evaluated_arr = ast.literal_eval(arr)
                    if isinstance(evaluated_arr, list):
                        return " ".join(str(item) for item in evaluated_arr if item)
                except (ValueError, SyntaxError):
                    # If not a list string, just return the string itself
                    return arr
            if isinstance(arr, list):
                return " ".join(str(item) for item in arr if item)
            return str(arr) # Fallback for other types

        preferences_df['technical_skills_str'] = preferences_df['technical_skills'].apply(process_text_array)
        preferences_df['improvement_areas_str'] = preferences_df['improvement_areas'].apply(process_text_array)

        # Concatenate interest fields
        interest_columns = ['career_goal', 'technical_skills_str', 'improvement_areas_str', 'primary_interest', 'secondary_interest']
        for col in interest_columns:
            if col not in preferences_df.columns: # Handle if a column is missing
                 preferences_df[col] = ""
            preferences_df[col] = preferences_df[col].fillna('') # Fill NaN with empty string

        preferences_df['interests_combined'] = preferences_df[interest_columns].agg(' '.join, axis=1)

        print(f"Fetched preferences for {len(preferences_df)} students.")
        # Save only relevant columns
        preferences_df[['user_id', 'interests_combined']].to_csv('data/student_preferences.csv', index=False)
        return preferences_df[['user_id', 'interests_combined']]
    else:
        print("No student preferences data found or error fetching.")
        return pd.DataFrame()

if __name__ == "__main__":
    # Create a 'data' directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    print("--- Starting Data Fetching ---")
    courses_df = fetch_courses_data()
    interactions_df = fetch_student_interactions_data()
    preferences_df = fetch_student_preferences_data()

    print("\n--- Data Fetching Summary ---")
    if not courses_df.empty:
        print("\nSample Courses Data (courses.csv):")
        print(courses_df.head())
    if not interactions_df.empty:
        print("\nSample Interactions Data (student_interactions.csv - for CF):")
        print(interactions_df.head())
    if not preferences_df.empty:
        print("\nSample Student Preferences Data (student_preferences.csv - for content profile):")
        print(preferences_df.head())

    print("\nData fetching complete. CSV files saved in 'data/' directory (if data was found).")