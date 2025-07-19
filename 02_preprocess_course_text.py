# Filename: 02_preprocess_course_text.py
import pandas as pd
import nltk
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# --- Download NLTK resources (run once) ---
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')
try:
    word_tokenize("test")
except LookupError:
    nltk.download('punkt')
try:
    WordNetLemmatizer().lemmatize('cars')
except LookupError:
    nltk.download('wordnet')
try:
    nltk.pos_tag(["test"])
except LookupError:
    nltk.download('averaged_perceptron_tagger')


# --- Text Preprocessing Function ---
def preprocess_text(text):
    if pd.isna(text): # Handle missing descriptions or tags
        return ""
    text = str(text).lower()  # Lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    tokens = word_tokenize(text)  # Tokenize
    # Remove stopwords
    stop_words_set = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words_set and word.isalpha() and len(word) > 2] # Also remove non-alpha and short words
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(tokens)

# --- Main Preprocessing Logic ---
def preprocess_course_content():
    print("Loading courses data...")
    try:
        courses_df = pd.read_csv('data/courses.csv')
    except FileNotFoundError:
        print("Error: 'data/courses.csv' not found. Run '01_fetch_data.py' first.")
        return

    print("Preprocessing course text (description and tags)...")
    # Ensure 'tags' is treated as a string if it's a list/array in the CSV
    # If tags are like "['tag1', 'tag2']", convert to "tag1 tag2"
    courses_df['tags_str'] = courses_df['tags'].apply(lambda x: ' '.join(eval(x)) if pd.notna(x) and isinstance(x, str) and x.startswith('[') else ( ' '.join(x) if pd.notna(x) and isinstance(x, list) else str(x) if pd.notna(x) else ''))

    # Combine description and tags for a richer content source
    # Fill NaN with empty string to avoid errors with string operations
    courses_df['content_full'] = courses_df['description'].fillna('') + " " + courses_df['tags_str'].fillna('')

    courses_df['processed_content'] = courses_df['content_full'].apply(preprocess_text)

    # Save the processed data
    courses_df[['id', 'course_code', 'name', 'processed_content']].to_csv('data/courses_processed_content.csv', index=False)
    print("Processed course content saved to 'data/courses_processed_content.csv'")
    print("\nSample Processed Content:")
    print(courses_df[['id', 'name', 'processed_content']].head())

if __name__ == "__main__":
    preprocess_course_content()