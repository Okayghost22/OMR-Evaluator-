import cv2
import numpy as np
import os
import pickle
from sklearn.linear_model import LogisticRegression

def get_features(bubble_roi):
    """
    Extracts features from a bubble image region (ROI).
    
    Args:
        bubble_roi (numpy.ndarray): The cropped image of a single bubble.
    
    Returns:
        list: A list containing the average pixel intensity.
    """
    # Check if the image is already grayscale
    if len(bubble_roi.shape) == 3:
        gray_roi = cv2.cvtColor(bubble_roi, cv2.COLOR_BGR2GRAY)
    else:
        gray_roi = bubble_roi
    
    # Calculate the average pixel intensity
    avg_intensity = np.mean(gray_roi)
    
    return [avg_intensity]

def train_and_save_model(dataset_path="dataset"):
    """
    Loads training data, trains a Logistic Regression model, and saves it.
    """
    X = [] # Features (avg pixel intensity)
    y = [] # Labels (0 for unfilled, 1 for filled)

    # --- Debugging check for filled folder ---
    filled_path = os.path.join(dataset_path, "filled")
    print(f"Checking for images in: {filled_path}")
    if not os.path.exists(filled_path):
        print(f"Error: The folder {filled_path} does not exist. Training aborted.")
        return

    # Load filled bubbles
    for filename in os.listdir(filled_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = cv2.imread(os.path.join(filled_path, filename))
            if img is not None:
                features = get_features(img)
                X.append(features)
                y.append(1) # Labeled as filled
    
    print(f"Found {len(X)} filled images.")

    # --- Debugging check for unfilled folder ---
    unfilled_path = os.path.join(dataset_path, "unfilled")
    print(f"Checking for images in: {unfilled_path}")
    if not os.path.exists(unfilled_path):
        print(f"Error: The folder {unfilled_path} does not exist. Training aborted.")
        return

    # Load unfilled bubbles
    for filename in os.listdir(unfilled_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = cv2.imread(os.path.join(unfilled_path, filename))
            if img is not None:
                features = get_features(img)
                X.append(features)
                y.append(0) # Labeled as unfilled
    
    print(f"Found {len(X) - y.count(1)} unfilled images.")

    if not X:
        print("No images found in either 'filled' or 'unfilled' folders. Training aborted.")
        return

    # Train the model
    model = LogisticRegression()
    model.fit(X, y)
    
    # Save the trained model
    with open("bubble_classifier.pkl", "wb") as f:
        pickle.dump(model, f)
        
    print("Model trained and saved as bubble_classifier.pkl")

if __name__ == '__main__':
    train_and_save_model()