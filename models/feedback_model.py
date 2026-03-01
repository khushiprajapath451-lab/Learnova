import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
import joblib
import os

DATA_PATH = "data/user_feedback.csv"
MODEL_PATH = "models/level_model.pkl"

def ensure_directories():
    """Create required directories"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)

def train_model():
    """Train ML model on feedback data"""
    ensure_directories()
    
    if not os.path.exists(DATA_PATH):
        return None, None, None, None, None

    try:
        df = pd.read_csv(DATA_PATH)
        if len(df) < 3:  # Need minimum data
            return None, None, None, None, None

        le_intent = LabelEncoder()
        le_subject = LabelEncoder()
        le_type = LabelEncoder()
        le_level = LabelEncoder()

        # Encode categorical features
        df["intent"] = le_intent.fit_transform(df["intent"])
        df["subject"] = le_subject.fit_transform(df["subject"])
        df["content_type"] = le_type.fit_transform(df["content_type"])
        df["level"] = le_level.fit_transform(df["level"])

        # Features: intent, subject, content_type, rating, quiz_score
        X = df[["intent", "subject", "content_type", "rating", "quiz_score"]]
        y = df["level"]

        model = LogisticRegression(max_iter=200)
        model.fit(X, y)

        # Save everything
        joblib.dump({
            'model': model, 
            'le_intent': le_intent,
            'le_subject': le_subject, 
            'le_type': le_type,
            'le_level': le_level
        }, MODEL_PATH)

        return model, le_intent, le_subject, le_type, le_level
    except:
        return None, None, None, None, None

def load_model():
    """Load trained model"""
    if os.path.exists(MODEL_PATH):
        try:
            data = joblib.load(MODEL_PATH)
            return data['model'], data['le_intent'], data['le_subject'], data['le_type'], data['le_level']
        except:
            return None, None, None, None, None
    return None, None, None, None, None

def predict_level(intent, subject, content_type, rating, quiz_score):
    """Predict optimal level using ML"""
    model, le_intent, le_subject, le_type, le_level = load_model()
    
    if model is None:
        return None
    
    try:
        encoded_intent = le_intent.transform([intent])[0]
        encoded_subject = le_subject.transform([subject])[0]
        encoded_type = le_type.transform([content_type])[0]
        
        prediction = model.predict([[encoded_intent, encoded_subject, encoded_type, rating, quiz_score]])[0]
        level = le_level.inverse_transform([prediction])[0]
        
        return level.lower()
    except:
        return None
