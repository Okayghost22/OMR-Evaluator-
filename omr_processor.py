import cv2
import numpy as np
import os
from imutils.contours import sort_contours
import pickle
import imutils
import json  # New import
from ml_model import get_features

# === Load the ML Model ===
try:
    with open("bubble_classifier.pkl", "rb") as f:
        BUBBLE_MODEL = pickle.load(f)
    print("ML model loaded successfully.")
except FileNotFoundError:
    print("ML model file 'bubble_classifier.pkl' not found. Please train the model first.")
    BUBBLE_MODEL = None

# === REMOVED: Old hardcoded ANSWER_KEY dictionaries are gone ===

def process_omr_sheet(image_path, exam_set):
    # === NEW CODE: Load the answer keys from JSON file ===
    try:
        with open("answer_keys.json", "r") as f:
            answer_keys_data = json.load(f)
    except FileNotFoundError:
        return {"status": "error", "message": "Answer key file 'answer_keys.json' not found."}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Error decoding 'answer_keys.json'. Please check for syntax errors."}

    # Select the correct answer key based on the user's choice
    if exam_set in answer_keys_data:
        answer_key = answer_keys_data[exam_set]
        # It's good practice to convert keys from string to integer if they represent numbers
        answer_key = {int(k): v for k, v in answer_keys_data[exam_set].items()}
    else:
        return {"status": "error", "message": f"Answer key for '{exam_set}' not found in the JSON file."}

    # Image preprocessing
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Find and filter contours (bubbles)
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    
    question_contours = []
    for c in contours:
        (x, y, w, h) = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        if w >= 15 and h >= 15 and 0.9 <= aspect_ratio <= 1.1:
            question_contours.append(c)

    # Sort contours by their Y-coordinate to group them into rows
    question_contours = sorted(question_contours, key=lambda c: cv2.boundingRect(c)[1])

    # Group the bubbles into questions (4 options per question)
    questions = []
    if len(question_contours) > 0:
        for i in range(0, len(question_contours), 4):
            if i + 4 <= len(question_contours):
                questions.append(sort_contours(question_contours[i:i + 4])[0])
    
    # === Add Safeguard: Check if 'questions' list is empty ===
    if not questions:
        return {"status": "error", "message": "Could not detect any questions. Please check the image quality."}

    answers = {}
    total_correct = 0
    
    # Define the question ranges for each subject
    subject_ranges = {
        "Python": range(0, 20),
        "Data Analysis": range(20, 40),
        "MySQL": range(40, 60),
        "Power BI": range(60, 80),
        "Adv Stats": range(80, 100)
    }
    
    subject_scores = {subject: 0 for subject in subject_ranges.keys()}

    # Loop through the questions and evaluate the answers
    for i, q in enumerate(questions):
        bubbled = None
        for j, bubble in enumerate(q):
            # === NEW CODE: Crop the bubble image region for the ML model ===
            (x, y, w, h) = cv2.boundingRect(bubble)
            bubble_roi = gray[y:y+h, x:x+w]
            
            # === NEW CODE: Check the bubble with the ML model ===
            is_marked = False
            if BUBBLE_MODEL is not None:
                features = get_features(bubble_roi)
                prediction = BUBBLE_MODEL.predict([features])
                if prediction[0] == 1:
                    is_marked = True
            else:
                # Fallback to old thresholding logic if model is not available
                mask = np.zeros(gray.shape, dtype="uint8")
                cv2.drawContours(mask, [bubble], -1, 255, -1)
                total_pixels = cv2.countNonZero(mask)
                filled_pixels = cv2.countNonZero(cv2.bitwise_and(thresh, thresh, mask=mask))
                if filled_pixels > (total_pixels * 0.5):
                    is_marked = True

            if is_marked:
                bubbled = j

        # Check for the existence of the question in the answer key
        correct = False
        key_answer = None
        color = (0, 0, 255) # Default to red for incorrect/unanswered
        if i in answer_key:
            key_answer_index = answer_key.get(i)
            key_answer = ["A", "B", "C", "D"][key_answer_index]
            if bubbled is not None and bubbled == key_answer_index:
                correct = True
                color = (0, 255, 0) # Green for correct
                total_correct += 1
                for subject, r in subject_ranges.items():
                    if i in r:
                        subject_scores[subject] += 1
                        break
            
        # === NEW CODE: Draw the annotation on the image ===
        # Get the bounding box of the bubbled answer
        if bubbled is not None:
            (x, y, w, h) = cv2.boundingRect(q[bubbled])
            center_x = x + int(w / 2)
            center_y = y + int(h / 2)
            # Draw a circle around the detected bubble
            cv2.circle(image, (center_x, center_y), 15, color, 3)

        answers[f"Question_{i+1}"] = {
            "marked_answer": ["A", "B", "C", "D"][bubbled] if bubbled is not None else None,
            "is_correct": correct,
            "key_answer": key_answer
        }

    # === NEW CODE: Save the annotated image and return the path ===
    # This code needs to be outside the for loop
    annotated_image_path = os.path.join(
        os.path.dirname(image_path), 
        "annotated_" + os.path.basename(image_path)
    )
    cv2.imwrite(annotated_image_path, image)

    return {
        "status": "success", 
        "answers": answers, 
        "total_score": total_correct, 
        "subject_scores": subject_scores,
        "annotated_image_path": annotated_image_path
    }