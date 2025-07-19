# Filename: 01_load_local_data.py
import pandas as pd
import os

# --- Configuration ---
# Update these file paths if your Excel files are named differently or are in a subfolder.
INTERACTIONS_XLSX_PATH = 'courses_sem7.xlsx'
PREFERENCES_XLSX_PATH = 'students_interests.xlsx'
OUTPUT_DATA_DIR = 'data' # The script will save outputs to 'D:\projects -2\ML model coursewise\data'

# The number of student sheets to read from the interactions file
NUM_STUDENT_SHEETS = 40 # Adjust if you have more or fewer student sheets

# Grade to Rating Mapping (Based on your screenshots)
GRADE_TO_RATING_MAPPING = {
    'A+': 10.0, 'A': 9.0, 'A-': 8.5, 'B+': 8.0, 'B': 7.0, 'B-': 6.5,
    'C+': 6.0, 'C': 5.0, 'C-': 4.5, 'D+': 4.0, 'D': 3.0,
    'P': 5.0, 'PASS': 5.0, 'F': 1.0, 'FAIL': 1.0, 'S': 7.0, 'U': 1.0,
}
DEFAULT_RATING_FOR_UNKNOWN_GRADE = 3.0

def process_interactions(file_path):
    """Reads the multi-sheet Excel file for student interactions."""
    print(f"--- 1. Processing Student Interactions from '{file_path}' ---")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at '{file_path}'. Skipping.")
        return False
    
    all_interactions = []
    for i in range(1, NUM_STUDENT_SHEETS + 1):
        sheet_name = f'Student_{i}'
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=2)
            df['user_id'] = str(i) # Assign user_id based on sheet number
            df.columns = df.columns.str.strip().str.lower()
            df = df.rename(columns={'code': 'course_id'})
            
            df_completed = df[df['status'].str.strip().str.lower() == 'complete'].copy()
            if df_completed.empty: continue
            
            df_completed['rating'] = df_completed['grade'].str.strip().str.upper().map(GRADE_TO_RATING_MAPPING)
            df_completed['rating'].fillna(DEFAULT_RATING_FOR_UNKNOWN_GRADE, inplace=True)
            
            all_interactions.append(df_completed[['user_id', 'course_id', 'rating']])
        except Exception as e:
            print(f"  - Could not process sheet '{sheet_name}'. Error: {e}")

    if all_interactions:
        combined_df = pd.concat(all_interactions, ignore_index=True)
        combined_df.to_csv(os.path.join(OUTPUT_DATA_DIR, 'student_interactions.csv'), index=False)
        print(f"Successfully processed {len(combined_df)} interactions. Saved to 'data/student_interactions.csv'")
        return True
    return False

def process_preferences(file_path):
    """Reads the single-sheet Excel file for student preferences."""
    print(f"\n--- 2. Processing Student Preferences from '{file_path}' ---")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at '{file_path}'. Skipping.")
        return False

    try:
        df = pd.read_excel(file_path, sheet_name='students_interests')
        cols_to_combine = ['career_goal', 'technical_skills', 'primary_interest', 
                           'secondary_interest', 'improvement_areas', 'other_keywords']
        for col in cols_to_combine:
            df[col] = df[col].fillna('').astype(str)
        
        df['interests_combined'] = df[cols_to_combine].agg(' '.join, axis=1)
        df['interests_combined'] = df['interests_combined'].str.replace(r'\s+', ' ', regex=True).str.strip()
        df['user_id'] = df['user_id'].astype(str)
        
        final_df = df[['user_id', 'interests_combined']]
        final_df.to_csv(os.path.join(OUTPUT_DATA_DIR, 'student_preferences.csv'), index=False)
        print(f"Successfully processed {len(final_df)} student preferences. Saved to 'data/student_preferences.csv'")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DATA_DIR):
        os.makedirs(OUTPUT_DATA_DIR)
        print(f"Created output directory: {OUTPUT_DATA_DIR}")
        
    process_interactions(INTERACTIONS_XLSX_PATH)
    process_preferences(PREFERENCES_XLSX_PATH)
    
    print("\n--- Local Data Loading Finished ---")
    print("Your 'data' folder should now contain:")
    print(" - courses.csv (from Supabase)")
    print(" - student_interactions.csv (from XLSX)")
    print(" - student_preferences.csv (from XLSX)")