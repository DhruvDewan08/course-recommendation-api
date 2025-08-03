# Filename: 02_preprocess_and_vectorize.py (Upgraded to Sentence-BERT)
import pandas as pd
import joblib
import os
from sentence_transformers import SentenceTransformer

def process_course_content():
    """Processes course content from the local CSV file."""
    print("--- 1. Processing Course Content from local CSV ---")
    
    df = pd.read_csv('data/courses_iiitd.csv')
    
    # --- THIS IS THE CORRECTED LOGIC ---
    # Define the actual column names from your Excel/CSV file
    tag_column_name = 'suitable tags'
    name_column_name = 'course_name'
    description_column_name = 'description'
    id_column_name = 'course_code' # This will be our course_id

    # Check if the tag column exists.
    if tag_column_name in df.columns:
        print(f"  - '{tag_column_name}' column found. Processing...")
        df['tags_str'] = df[tag_column_name].fillna('').astype(str)
    else:
        print(f"  - WARNING: '{tag_column_name}' column not found. Proceeding without tags.")
        df['tags_str'] = ''
    
    # Combine the name, description, and tags using the correct column names
    df['content_full'] = df[name_column_name].fillna('') + ' . ' + df[description_column_name].fillna('') + ' . ' + df['tags_str']
    
    # Also, we need to update the id_column_name for the vectorize function
    # Let's rename it now for consistency in the returned dataframe
    df.rename(columns={id_column_name: 'course_id'}, inplace=True)

    print("Course content prepared.")
    return df

def process_student_preferences():
    """Processes student preferences from the cleaned CSV."""
    print("--- 2. Processing Student Preferences ---")
    df = pd.read_csv('data/student_preferences_cleaned.csv', dtype={'user_id': str})
    print("Student preferences processed.")
    return df

def vectorize_data_with_bert(courses_df, preferences_df):
    """Creates Semantic Embeddings for courses and students using Sentence-BERT."""
    print("\n--- 3. Vectorizing Data with Sentence-BERT ---")
    
    # Load a powerful, pre-trained Sentence Transformer model.
    # This will be downloaded and cached automatically the first time.
    print("Loading Sentence-BERT model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Create the course-feature matrix. This is the most time-consuming step.
    course_corpus = courses_df['content_full'].tolist()
    print("Encoding course data... (This may take a few minutes)")
    course_embeddings = model.encode(course_corpus, show_progress_bar=True)
    print(f"Course embedding matrix created with shape: {course_embeddings.shape}")
    
    # Create the student-feature matrix
    student_corpus = preferences_df['interests_combined'].tolist()
    print("Encoding student preference data...")
    student_embeddings = model.encode(student_corpus, show_progress_bar=True)
    print(f"Student embedding matrix created with shape: {student_embeddings.shape}")
    
    # Save the new artifacts to the models folder.
    model_dir = 'models/content_based'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    # We save the results (the embeddings), not the model itself.
    joblib.dump(course_embeddings, f'{model_dir}/course_embeddings.joblib')
    joblib.dump(student_embeddings, f'{model_dir}/student_embeddings.joblib')
    
    # The ID mappings are still essential
    joblib.dump(courses_df['course_id'].tolist(), f'{model_dir}/course_ids.joblib')# Use 'code' or 'id' from your Excel
    joblib.dump(preferences_df['user_id'].astype(str).tolist(), f'{model_dir}/user_ids.joblib')
    
    print(f"\nSemantic embeddings and ID mappings saved to '{model_dir}' directory.")

if __name__ == "__main__":
    courses_df = process_course_content()
    preferences_df = process_student_preferences()
    vectorize_data_with_bert(courses_df, preferences_df)
    print("\n--- Semantic Preprocessing and Vectorization Finished ---")