# Filename: 02_preprocess_and_vectorize.py
import pandas as pd
import nltk
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# --- Download NLTK resources (only needs to run once) ---
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading NLTK data...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt_tab')
    print("NLTK data downloaded.")

def preprocess_text(text):
    """A helper function to clean up text."""
    if pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    tokens = nltk.word_tokenize(text)
    stop_words = set(nltk.corpus.stopwords.words('english'))
    lemmatizer = nltk.stem.WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words and w.isalpha()]
    return " ".join(tokens)

def process_course_content():
    """Processes course descriptions for content-based filtering."""
    print("--- 1. Processing Course Content ---")
    df = pd.read_csv('data/courses.csv')
    df['content_full'] = df['name'].fillna('') + ' ' + df['description'].fillna('') + ' ' + df['prerequisites'].fillna('')
    df['processed_content'] = df['content_full'].apply(preprocess_text)
    print("Course content processed.")
    return df

def process_student_preferences():
    """Processes student preferences for content-based profiling."""
    print("--- 2. Processing Student Preferences ---")
    df = pd.read_csv('data/student_preferences_cleaned.csv')
    df['processed_interests'] = df['interests_combined'].apply(preprocess_text)
    print("Student preferences processed.")
    return df

def vectorize_data(courses_df, preferences_df):
    """Creates TF-IDF vectors for courses and student profiles."""
    print("\n--- 3. Vectorizing Data with TF-IDF ---")
    
    # Initialize the vectorizer using the course content
    vectorizer = TfidfVectorizer(max_features=5000, min_df=2, stop_words='english')
    
    # Create the course-feature matrix
    course_corpus = courses_df['processed_content']
    course_tfidf_matrix = vectorizer.fit_transform(course_corpus)
    print(f"Course TF-IDF matrix created with shape: {course_tfidf_matrix.shape}")
    
    # Create the student-feature matrix using the *same* vectorizer
    student_corpus = preferences_df['processed_interests']
    student_tfidf_matrix = vectorizer.transform(student_corpus)
    print(f"Student TF-IDF matrix created with shape: {student_tfidf_matrix.shape}")
    
    # Save the vectorizer and matrices for later use in the API
    model_dir = 'models/content_based'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    joblib.dump(vectorizer, f'{model_dir}/tfidf_vectorizer.joblib')
    joblib.dump(course_tfidf_matrix, f'{model_dir}/course_tfidf_matrix.joblib')
    joblib.dump(student_tfidf_matrix, f'{model_dir}/student_tfidf_matrix.joblib')
    
    # Save the mappings from matrix row to actual ID
    joblib.dump(courses_df['course_id'].tolist(), f'{model_dir}/course_ids.joblib')
    joblib.dump(preferences_df['user_id'].astype(str).tolist(), f'{model_dir}/user_ids.joblib')
    
    print("\nVectorizer, matrices, and ID mappings saved to 'models/content_based/' directory.")

if __name__ == "__main__":
    courses_df = process_course_content()
    preferences_df = process_student_preferences()
    vectorize_data(courses_df, preferences_df)
    print("\n--- Preprocessing and Vectorization Finished ---")