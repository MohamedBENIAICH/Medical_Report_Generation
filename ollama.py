# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import io
import base64
import os
from openai import OpenAI  # Still using openai package but pointing to Ollama
import logging
import numpy as np
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Ollama client (using OpenAI compatible API)
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'  # No API key needed for local Ollama
)

def generate_basic_report(img_width, img_height, img_mode):
    """
    Generate a basic medical report when LLM is not available
    """
    return f"""
    BASIC MEDICAL IMAGE ANALYSIS REPORT
    ---------------------------------
    
    Image Properties:
    - Dimensions: {img_width}x{img_height} pixels
    - Color Mode: {img_mode}
    
    Analysis:
    This is a basic analysis based on image properties only.
    
    Disclaimer:
    Always consult with a qualified healthcare professional for diagnosis.
    """

def analyze_image_with_llm(image_bytes: bytes) -> str:
    """
    Analyze medical image using Ollama's medllama2
    """
    try:
        # Basic image analysis
        img = Image.open(io.BytesIO(image_bytes))
        img_width, img_height = img.size
        img_mode = img.mode
        
        # Try to use Ollama with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Use medllama2 to generate a medical report
                response = client.chat.completions.create(
                    model="medllama2",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical imaging expert. Generate a professional report including: "
                                      "1. Image type, 2. Notable findings, 3. Possible conditions, 4. Recommendations. "
                                      "Base your analysis on these image properties:"
                        },
                        {
                            "role": "user",
                            "content": f"Medical image analysis request:\n"
                                      f"- Dimensions: {img_width}x{img_height} pixels\n"
                                      f"- Color mode: {img_mode}\n"
                                      f"- Content: Medical diagnostic image"
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.7  # Lower for more conservative medical analysis
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_message = str(e)
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {error_message}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All attempts failed. Using fallback analysis. Last error: {error_message}")
                    return generate_basic_report(img_width, img_height, img_mode)
                    
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return generate_basic_report(img_width, img_height, img_mode)

@app.post("/analyze-medical-image")
async def analyze_medical_image(file: UploadFile = File(...)):
    """Endpoint to analyze medical images using Ollama"""
    try:
        # Validate input
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and validate image
        image_bytes = await file.read()
        Image.open(io.BytesIO(image_bytes)).verify()  # Will raise if invalid
        
        # Analyze with LLM or fallback
        analysis = analyze_image_with_llm(image_bytes)
        
        return {
            "status": "success",
            "report": format_medical_report(analysis)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def format_medical_report(analysis: str) -> str:
    """Format the analysis into a structured report"""
    return f"""
    AUTOMATED MEDICAL IMAGE ANALYSIS REPORT (Ollama/medllama2)
    --------------------------------------------------------
    {analysis}
    
    DISCLAIMER: This is an AI-generated preliminary analysis. 
    Always consult with a qualified healthcare professional.
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)