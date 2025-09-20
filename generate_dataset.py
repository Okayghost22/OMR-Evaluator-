import cv2
import os
import imutils
import numpy as np

# A simplified version of your bubble detection logic
def extract_bubbles(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image at {image_path}")
        return []

    # Convert to grayscale immediately after loading
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Do NOT apply thresholding here!
    # edged = cv2.Canny(blurred, 75, 200) # This might also be too aggressive
    # Instead, let's use the blurred grayscale image for contour finding if possible.
    
    # A simple threshold to find the contours
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    
    bubble_regions = []
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1], reverse=False)

    for c in contours:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if w >= 20 and h >= 20 and ar >= 0.9 and ar <= 1.1:
            # === Change this line! ===
            # Crop the bubble from the ORIGINAL GRAYSCALE image
            bubble_roi = gray[y:y+h, x:x+w]
            bubble_regions.append(bubble_roi)
            
    return bubble_regions

def create_training_data(input_image, output_dir="dataset"):
    # Process the provided OMR sheet to extract bubble regions
    bubbles = extract_bubbles(input_image)
    
    # Create the 'dataset' folder if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for i, bubble_img in enumerate(bubbles):
        # Save each bubble image
        filename = f"bubble_{i}.png"
        cv2.imwrite(os.path.join(output_dir, filename), bubble_img)
        
    print(f"Extracted {len(bubbles)} bubble images and saved them to the '{output_dir}' directory.")

if __name__ == '__main__':
    # Use the filename you provided
    create_training_data("WhatsApp Image 2025-09-20 at 13.13.35_716a2857.jpg")
    print("Now, manually sort the images in the 'dataset' folder into 'filled' and 'unfilled' subfolders.")