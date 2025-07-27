# Filename: 01_load_json_data.py
import pandas as pd
import os

# --- Configuration ---
INTERACTIONS_JSON_PATH = 'student_academic_records.json'
PREFERENCES_JSON_PATH = 'students_interests.json'
OUTPUT_DATA_DIR = 'data'

INTERACTIONS_OUTPUT_FILENAME = 'student_interactions_cleaned.csv'
PREFERENCES_OUTPUT_FILENAME = 'student_preferences_cleaned.csv'

GRADE_TO_RATING_MAPPING = {
    'A+': 10.0, 'A': 9.0, 'A-': 8.5, 'B+': 8.0, 'B': 7.0, 'B-': 6.5,
    'C+': 6.0, 'C': 5.0, 'C-': 4.5, 'D+': 4.0, 'D': 3.0,
    'P': 5.0, 'PASS': 5.0, 'F': 1.0, 'FAIL': 1.0, 'S': 7.0, 'U': 1.0,
}
DEFAULT_RATING_FOR_UNKNOWN_GRADE = 3.0

def process_interactions_from_json(file_path):
    print(f"--- 1. Processing Interactions from '{file_path}' ---")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at '{file_path}'.")
        return False
    
    df = pd.read_json(file_path)
    print(f"  - Loaded {len(df)} raw interaction records.")
    
    df.drop_duplicates(subset=['user_id', 'course_id'], keep='first', inplace=True)
    print(f"  - After deduplication, {len(df)} unique records remain.")
    
    df_completed = df[df['status'].str.lower() == 'complete'].copy()
    
    df_completed['rating'] = df_completed['grade'].str.strip().str.upper().map(GRADE_TO_RATING_MAPPING)
    df_completed['rating'].fillna(DEFAULT_RATING_FOR_UNKNOWN_GRADE, inplace=True)
    
    final_df = df_completed[['user_id', 'course_id', 'rating']]
    output_path = os.path.join(OUTPUT_DATA_DIR, INTERACTIONS_OUTPUT_FILENAME)
    final_df.to_csv(output_path, index=False)
    print(f"✅ Successfully processed {len(final_df)} interactions. Saved to '{output_path}'")
    return True

def process_preferences_from_json(file_path):
    print(f"\n--- 2. Processing Preferences from '{file_path}' ---")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at '{file_path}'.")
        return False
    
    df = pd.read_json(file_path)
    
    text_cols = ['career_goal', 'technical_skills', 'primary_interest', 'secondary_interest', 'improvement_areas', 'other_keywords']
    
    for col in text_cols:
        if col not in df.columns: df[col] = ''
        df[col] = df[col].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x) if pd.notna(x) else '')
            
    df['interests_combined'] = df[text_cols].agg(' '.join, axis=1)
    df['interests_combined'] = df['interests_combined'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    final_df = df[['user_id', 'interests_combined']]
    output_path = os.path.join(OUTPUT_DATA_DIR, PREFERENCES_OUTPUT_FILENAME)
    final_df.to_csv(output_path, index=False)
    print(f"✅ Successfully processed {len(final_df)} student preferences. Saved to '{output_path}'")
    return True

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DATA_DIR):
        os.makedirs(OUTPUT_DATA_DIR)
        
    process_interactions_from_json(INTERACTIONS_JSON_PATH)
    process_preferences_from_json(PREFERENCES_JSON_PATH)
    
    print("\n--- Data loading from JSON finished! ---")