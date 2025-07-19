# Filename: 04_recommendation_api.py (Corrected)
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from sklearn.metrics.pairwise import cosine_similarity

# --- 1. SETUP & APP INITIALIZATION ---

# DEFINE APP AT THE TOP to avoid the "app not found" error.
app = FastAPI(
    title="Course Recommendation API",
    description="Provides personalized course recommendations based on student data.",
    version="0.1.0",
)

# Define a state object to hold our models and data
# This is a cleaner way to manage application state.
app.state.models_loaded = False
app.state.tfidf_vectorizer = None

# --- 2. MODEL LOADING ---

@app.on_event("startup")
def load_models():
    """Load all model artifacts once on API startup."""
    print("--- Loading models and data artifacts... ---")
    
    # Define file paths
    MODEL_DIR = 'models'
    CONTENT_MODEL_DIR = os.path.join(MODEL_DIR, 'content_based')
    CF_MODEL_DIR = os.path.join(MODEL_DIR, 'collaborative_filtering')
    DATA_DIR = 'data'

    try:
        # Content-Based artifacts
        app.state.tfidf_vectorizer = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'tfidf_vectorizer.joblib'))
        app.state.course_tfidf_matrix = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'course_tfidf_matrix.joblib'))
        course_ids = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'course_ids.joblib'))
        user_ids_content = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'user_ids.joblib'))
        app.state.student_tfidf_matrix = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'student_tfidf_matrix.joblib'))

        # Collaborative Filtering artifact
        app.state.cf_model = joblib.load(os.path.join(CF_MODEL_DIR, 'cf_svd_model.joblib'))
        
        # Load interaction data, ENSURING user_id is a string for consistency
        app.state.interactions_df = pd.read_csv(os.path.join(DATA_DIR, 'student_interactions.csv'), dtype={'user_id': str})
        
        # Helper mappings for quick lookups
        app.state.course_id_to_idx = {course_id: i for i, course_id in enumerate(course_ids)}
        # Ensure user IDs in the mapping are strings
        app.state.user_id_to_idx = {str(user_id): i for i, user_id in enumerate(user_ids_content)}

        app.state.all_course_ids = course_ids
        
        app.state.models_loaded = True
        print("--- All models and data artifacts loaded successfully! ---")

    except FileNotFoundError as e:
        print(f"FATAL ERROR: A required model or data file was not found.")
        print(f"Missing file detail: {e}")
        print("Please ensure you have run all training scripts (01, 02, 03) successfully.")
    except Exception as e:
        print(f"An unexpected error occurred during model loading: {e}")


# --- 3. DEFINE API INPUT & OUTPUT MODELS ---

class RecommendationRequest(BaseModel):
    user_id: str
    top_n: int = 10

class CourseRecommendation(BaseModel):
    course_id: str
    score: float

class RecommendationResponse(BaseModel):
    recommendations: list[CourseRecommendation]


# --- 4. THE RECOMMENDATION API ENDPOINT ---

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Generates course recommendations for a given user_id.
    """
    if not app.state.models_loaded:
        raise HTTPException(
            status_code=503, 
            detail="Models are not loaded. The API is not operational."
        )

    user_id = str(request.user_id)
    top_n = request.top_n
    
    print(f"\nGenerating recommendations for user_id: {user_id}")
    
    # --- Filter out courses the user has already taken ---
    courses_taken_by_user = set(app.state.interactions_df[app.state.interactions_df['user_id'] == user_id]['course_id'])
    candidate_courses = [cid for cid in app.state.all_course_ids if cid not in courses_taken_by_user]
    print(f"User has taken {len(courses_taken_by_user)} courses. Evaluating {len(candidate_courses)} candidate courses.")

    # --- Content-Based Scoring ---
    content_scores = {}
    if user_id in app.state.user_id_to_idx:
        student_idx = app.state.user_id_to_idx[user_id]
        student_profile_vector = app.state.student_tfidf_matrix[student_idx]
        
        for course_id in candidate_courses:
            course_idx = app.state.course_id_to_idx.get(course_id)
            if course_idx is not None:
                course_vector = app.state.course_tfidf_matrix[course_idx]
                similarity = cosine_similarity(student_profile_vector, course_vector)[0][0]
                content_scores[course_id] = similarity
    else:
        print(f"Warning: User ID '{user_id}' not found in content-based profiles. No content scores will be generated.")

    # --- Collaborative Filtering Scoring ---
    cf_scores = {}
    for course_id in candidate_courses:
        prediction = app.state.cf_model.predict(uid=user_id, iid=course_id)
        cf_scores[course_id] = prediction.est

    # --- Hybrid Scoring ---
    hybrid_scores = {}
    for course_id in candidate_courses:
        content_score = content_scores.get(course_id, 0.0)
        cf_score = cf_scores.get(course_id, 2.5) # Default to a low rating
        normalized_cf_score = (cf_score - 1) / 9.0 # Normalize 1-10 scale to 0-1
        
        hybrid_score = (0.5 * content_score) + (0.5 * normalized_cf_score)
        hybrid_scores[course_id] = hybrid_score

    # --- Rank and Return Top N ---
    sorted_recommendations = sorted(hybrid_scores.items(), key=lambda item: item[1], reverse=True)
    
    top_recommendations = []
    for course_id, score in sorted_recommendations[:top_n]:
        top_recommendations.append(CourseRecommendation(course_id=course_id, score=score))

    return RecommendationResponse(recommendations=top_recommendations)

@app.get("/", summary="Root endpoint for health check")
async def root():
    return {"status": "ok", "models_loaded": app.state.models_loaded}