import requests
import os
from dotenv import load_dotenv
import sys

load_dotenv()

BASE_URL = "http://localhost:8000"

print(f"API Key loaded: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

def test_medical_image_analysis(image_path: str):
    """Test the medical image analysis endpoint"""
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: Image file '{image_path}' not found")
            return
            
        # Get file details
        file_size = os.path.getsize(image_path)
        print(f"Image file: {image_path}")
        print(f"File size: {file_size} bytes")
        
        with open(image_path, "rb") as image_file:
            files = {"file": (os.path.basename(image_path), image_file, "image/jpeg")}
            print(f"Sending request to {BASE_URL}/analyze-medical-image")
            response = requests.post(
                f"{BASE_URL}/analyze-medical-image",
                files=files
            )
            
        if response.status_code == 200:
            print("Test successful!")
            print("\nAnalysis Results:")
            print(response.json()["report"])
        else:
            print(f"Test failed with status {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    # Test with a sample medical image
    image_path = "images.jpg"  # Replace with your test image
    test_medical_image_analysis(image_path)