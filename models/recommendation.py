

WEAK_SUBJECT_THRESHOLD = 50
ADVANCED_THRESHOLD = 80

DEFAULT_BEGINNER_DIFFICULTY = "Beginner"
DEFAULT_BEGINNER_DURATION = "6 weeks"

DEFAULT_INTERMEDIATE_DIFFICULTY = "Intermediate"
DEFAULT_INTERMEDIATE_DURATION = "4 weeks"

DEFAULT_ADVANCED_DIFFICULTY = "Advanced"
DEFAULT_ADVANCED_DURATION = "3 weeks"



def train_model():
    """
    Dummy ML model placeholder.
    Returns None so system doesn't crash.
    """
    return None, None, None, None



def generate_recommendation(profile):
    recommendations = []

    
    class_level = profile.get("class_level", "Class")
    subject = profile.get("subject", "Subject")
    performance = profile.get("performance", 50)
    intent = profile.get("intent", "General Learning")
    content_type = profile.get("content_type", "video")

    if performance < WEAK_SUBJECT_THRESHOLD:
        recommendations.append({
            "course": f"{class_level} {subject} Foundation (Video Series)",
            "difficulty": DEFAULT_BEGINNER_DIFFICULTY,
            "duration": DEFAULT_BEGINNER_DURATION,
            "priority": "High",
            "videos": 2,
            "quizzes" : 1
        })

    if intent == "Exam Preparation":
        recommendations.append({
            "course": f"{class_level} {subject} Exam Mastery",
            "difficulty": DEFAULT_INTERMEDIATE_DIFFICULTY,
            "duration": DEFAULT_INTERMEDIATE_DURATION,
            "priority": "Medium",
            "videos": 2,
            "quizzes" : 1
        })

    if performance > ADVANCED_THRESHOLD:
        recommendations.append({
            "course": f"Advanced {subject} Problem Solving",
            "difficulty": DEFAULT_ADVANCED_DIFFICULTY,
            "duration": DEFAULT_ADVANCED_DURATION,
            "priority": "High",
            "videos": 2,
            "quizzes" : 1
        })

    if not recommendations:
        recommendations.append({
            "course": f"Core Concepts in {subject}",
            "difficulty": DEFAULT_INTERMEDIATE_DIFFICULTY,
            "duration": DEFAULT_INTERMEDIATE_DURATION,
            "priority": "Normal",
            "videos": 2,
            "quizzes" : 1
        })

    

    model, le_intent, le_subject, le_type = train_model()

    if model is not None:
        try:
            encoded_intent = le_intent.transform([intent])[0]
            encoded_subject = le_subject.transform([subject])[0]
            encoded_type = le_type.transform([content_type])[0]

            prediction = model.predict([[encoded_intent, encoded_subject, encoded_type]])

            # If model predicts positive preference → boost priority
            if prediction[0] == 1:
                recommendations[0]["priority"] = "High (AI Boosted)"
            else:
                recommendations[0]["priority"] = "Low (Based on Feedback)"

        except Exception:
            # If new label not seen before
            pass

    return recommendations

