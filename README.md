# OMR-Evaluator-
Overview
The OMR Evaluator is a web application built with Flask and Python that automates the process of evaluating Optical Mark Recognition (OMR) sheets. Users can upload an image of a filled-out OMR sheet, and the application will automatically detect the marked answers, calculate the score, and provide a detailed breakdown of the results. It also includes an admin dashboard for viewing and managing all evaluated sheets.

Features
Automated OMR Processing: Upload an image of an OMR sheet, and the application will automatically detect and score the answers.

Real-time Feedback: A loading indicator provides a real-time progress update while the sheet is being processed.

Detailed Results: View a breakdown of the total score and subject-wise scores.

Annotated Image Output: The application generates and displays an annotated image showing the marked answers and corrections.

Admin Dashboard: A password-protected dashboard allows administrators to view a history of all evaluated sheets.

Data Export: Export all evaluation results to a CSV file for further analysis.

Database Storage: Results are stored in a local SQLite database for persistent storage.

Setup and Installation
Prerequisites
Python 3.9 or higher

Git

Installation Steps
Clone the Repository:

git clone https://[your-huggingface-space-url]
cd [your-project-directory]

Create a Virtual Environment:
It's recommended to work in a virtual environment to manage project dependencies.

python -m venv venv

Activate the Virtual Environment:

On macOS and Linux:

source venv/bin/activate

On Windows:

venv\Scripts\activate

Install Dependencies:
Install all required libraries from the requirements.txt file.

pip install -r requirements.txt

Run the Application:
Launch the Flask application.

python app.py

The application will now be running locally. You can access it by opening your web browser and navigating to http://127.0.0.1:5000.

File Structure
.
├── app.py                     # The main Flask application file
├── omr_processor.py           # Core logic for OMR sheet processing
├── requirements.txt           # List of Python dependencies
├── Procfile                   # Command for deploying the app on Hugging Face Spaces
├── templates/
│   ├── dashboard.html         # Admin dashboard page
│   ├── index.html             # The main upload page
│   ├── login.html             # Admin login page
│   └── results.html           # Page to display individual results
├── static/
│   ├── css/
│   │   └── style.css          # Custom CSS styles
├── uploads/                   # Directory to store uploaded and annotated images
└── README.md                  # This file
