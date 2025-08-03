# Filename: 04_recommendation_api.py (Corrected with Absolute Paths)
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from sklearn.metrics.pairwise import cosine_similarity
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer

# Get the absolute path to the directory where this script is located.
# This makes our file paths reliable, no matter where the script is run from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all model artifacts once on API startup using the new lifespan manager."""
    print("--- Loading models and data artifacts for SEMANTIC model... ---")
    
    # Construct absolute paths to our models and data folders
    MODEL_DIR = os.path.join(BASE_DIR, 'models')
    CONTENT_MODEL_DIR = os.path.join(MODEL_DIR, 'content_based')
    CF_MODEL_DIR = os.path.join(MODEL_DIR, 'collaborative_filtering')
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    try:
        # Load the Sentence Transformer neural network model itself
        print("Loading Sentence-BERT model (this may take a moment)...")
        app.state.st_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Sentence-BERT model loaded.")

        # Load all our artifacts using the new absolute paths
        app.state.course_embeddings = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'course_embeddings.joblib'))
        app.state.student_embeddings = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'student_embeddings.joblib'))
        course_ids = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'course_ids.joblib'))
        user_ids_content = joblib.load(os.path.join(CONTENT_MODEL_DIR, 'user_ids.joblib'))
        app.state.cf_model = joblib.load(os.path.join(CF_MODEL_DIR, 'cf_svd_model.joblib'))
        app.state.interactions_df = pd.read_csv(os.path.join(DATA_DIR, 'student_interactions_cleaned.csv'), dtype={'user_id': str})
        
        # Helper mappings for quick lookups
        app.state.course_id_to_idx = {course_id: i for i, course_id in enumerate(course_ids)}
        app.state.user_id_to_idx = {str(user_id): i for i, user_id in enumerate(user_ids_content)}
        app.state.all_course_ids = course_ids
        
        app.state.models_loaded = True
        print("--- All models and data artifacts loaded successfully! ---")

    except Exception as e:
        print(f"FATAL ERROR during model loading: {e}")
        app.state.models_loaded = False
    
    yield
    print("--- Server is shutting down. ---")

app = FastAPI(
    title="Course Recommendation API (v2 - Semantic)",
    lifespan=lifespan
)

class RecommendationRequest(BaseModel):
    user_id: str
    top_n: int = 10

class CourseRecommendation(BaseModel):
    course_id: str
    score: float

class RecommendationResponse(BaseModel):
    recommendations: list[CourseRecommendation]

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    if not app.state.models_loaded:
        raise HTTPException(status_code=503, detail="Models are not loaded.")

    user_id = str(request.user_id)
    
    courses_taken_by_user = set(app.state.interactions_df[app.state.interactions_df['user_id'] == user_id]['course_id'])
    candidate_courses = [cid for cid in app.state.all_course_ids if cid not in courses_taken_by_user]

    content_scores = {}
    if user_id in app.state.user_id_to_idx:
        student_idx = app.state.user_id_to_idx[user_id]
        student_profile_vector = app.state.student_embeddings[student_idx].reshape(1, -1)
        
        for course_id in candidate_courses:
            course_idx = app.state.course_id_to_idx.get(course_id)
            if course_idx is not None:
                course_vector = app.state.course_embeddings[course_idx].reshape(1, -1)
                similarity = cosine_similarity(student_profile_vector, course_vector)[0][0]
                content_scores[course_id] = similarity
    else:
        print(f"Warning: User ID '{user_id}' not found in pre-computed profiles. Content score will be 0.")

    cf_scores = {}
    for course_id in candidate_courses:
        prediction = app.state.cf_model.predict(uid=user_id, iid=course_id)
        cf_scores[course_id] = prediction.est

    hybrid_scores = {}
    for course_id in candidate_courses:
        content_score = content_scores.get(course_id, 0.0)
        cf_score = cf_scores.get(course_id, 2.5)
        normalized_cf_score = (cf_score - 1) / 9.0
        
        hybrid_score = (0.7 * content_score) + (0.3 * normalized_cf_score)
        hybrid_scores[course_id] = hybrid_score

    sorted_recommendations = sorted(hybrid_scores.items(), key=lambda item: item[1], reverse=True)
    top_recommendations = [CourseRecommendation(course_id=cid, score=s) for cid, s in sorted_recommendations[:request.top_n]]

    return RecommendationResponse(recommendations=top_recommendations)

@app.get("/")
async def root():
    return {"status": "ok", "models_loaded": app.state.models_loaded}