# Filename: 03_train_collaborative_filtering.py
import pandas as pd
import os
import joblib
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split, cross_validate

def train_cf_model():
    """Trains and saves a Collaborative Filtering model using the Surprise library."""
    print("--- 1. Loading Student Interaction Data ---")
    try:
        interactions_df = pd.read_csv('data/student_interactions_cleaned.csv', dtype={'user_id': str})
    except FileNotFoundError:
        print("ERROR: 'data/student_interactions.csv' not found. Please run previous scripts first.")
        return

    if interactions_df.empty:
        print("ERROR: Interaction data is empty. Cannot train model.")
        return

    # The Surprise Reader needs to know the rating scale.
    # Our mapping is from 1.0 to 10.0.
    reader = Reader(rating_scale=(1, 10))

    # Load the data from the pandas dataframe
    data = Dataset.load_from_df(interactions_df[['user_id', 'course_id', 'rating']], reader)
    print("Data loaded successfully into Surprise dataset format.")

    # --- Optional: Evaluate the model (good practice) ---
    # We can use cross-validation to get a sense of the model's performance.
    # SVD is a powerful matrix factorization algorithm.
    print("\n--- 2. Evaluating SVD Model with Cross-Validation ---")
    algo = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.04, random_state=42)
    
    # Run 5-fold cross-validation and print results (RMSE, MAE)
    # This gives an estimate of how well the model predicts ratings.
    # Lower RMSE/MAE is better.
    cv_results = cross_validate(algo, data, measures=['RMSE', 'MAE'], cv=5, verbose=True)
    
    # --- 3. Training the Full Model and Saving It ---
    print("\n--- 3. Training on the Full Dataset ---")
    # We build a training set from the entire dataset to train the final model
    trainset = data.build_full_trainset()
    algo.fit(trainset)
    print("Model training complete.")

    # Save the trained model
    model_dir = 'models/collaborative_filtering'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    model_path = os.path.join(model_dir, 'cf_svd_model.joblib')
    joblib.dump(algo, model_path)

    print(f"\nCollaborative Filtering model saved to: {model_path}")
    print("\n--- Collaborative Filtering Training Finished ---")

if __name__ == "__main__":
    train_cf_model()