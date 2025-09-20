import os
import cv2
import numpy as np

# A copy of your get_features function from ml_model.py
def get_features(bubble_roi):
    """
    Extracts features from a single bubble image.
    In this case, it's the average pixel intensity.
    """
    # Ensure the image is in grayscale
    if len(bubble_roi.shape) == 3:
        gray_roi = cv2.cvtColor(bubble_roi, cv2.COLOR_BGR2GRAY)
    else:
        gray_roi = bubble_roi
    
    # Calculate the average pixel intensity
    avg_intensity = np.mean(gray_roi)
    return [avg_intensity]

def analyze_dataset(dataset_path="dataset"):
    """
    Analyzes the images in the dataset folder and prints their status.
    """
    bubble_files = sorted(os.listdir(dataset_path))
    
    # Create the 'filled' and 'unfilled' folders if they don't exist
    filled_path = os.path.join(dataset_path, "filled")
    unfilled_path = os.path.join(dataset_path, "unfilled")
    if not os.path.exists(filled_path):
        os.makedirs(filled_path)
    if not os.path.exists(unfilled_path):
        os.makedirs(unfilled_path)

    for filename in bubble_files:
        # We only want to process image files
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(dataset_path, filename)
            img = cv2.imread(image_path)
            
            if img is not None:
                features = get_features(img)
                avg_intensity = features[0]
                
                status = "unfilled"
                # Use a threshold to guess the status. Adjust this value if needed.
                if avg_intensity < 150:  
                    status = "filled"
                
                print(f"File: {filename} | Avg Intensity: {avg_intensity:.2f} | Status: {status}")

if __name__ == '__main__':
    analyze_dataset()