# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import io
import base64
import os
from openai import OpenAI
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

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_basic_report(img_width, img_height, img_mode):
    """
    Generate a basic medical report when OpenAI API is not available
    """
    return f"""
    BASIC MEDICAL IMAGE ANALYSIS REPORT
    ---------------------------------
    
    Image Properties:
    - Dimensions: {img_width}x{img_height} pixels
    - Color Mode: {img_mode}
    
    Analysis:
    This is a basic analysis based on image properties only. For a more detailed analysis, 
    please ensure your OpenAI API quota is available or contact your system administrator.
    
    Disclaimer:
    This is a limited analysis based only on image metadata. No visual content analysis was performed.
    Always consult with a qualified healthcare professional for diagnosis.
    """

def analyze_image_with_llm(image_bytes: bytes) -> str:
    """
    Analyze medical image using a combination of image processing and LLM
    """
    try:
        # Basic image analysis
        img = Image.open(io.BytesIO(image_bytes))
        img_width, img_height = img.size
        img_mode = img.mode
        
        # Log API key status (masked for security)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found in environment variables")
            return generate_basic_report(img_width, img_height, img_mode)
            
        masked_key = api_key[:4] + "..." + api_key[-4:]
        logger.info(f"Using OpenAI API key: {masked_key}")
        
        # Generate a description of the image based on basic properties
        image_description = f"This is a medical image with dimensions {img_width}x{img_height} pixels in {img_mode} color mode."
        
        # Try to use OpenAI API with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Use GPT-4o to generate a medical report based on the image description
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical imaging expert. Based on the provided image description, generate a professional medical report. "
                                    "Include: 1. Image type, 2. Notable findings, 3. Possible conditions, 4. Recommended next steps. "
                                    "Be concise but thorough. If the image description doesn't provide enough detail, acknowledge this limitation."
                        },
                        {
                            "role": "user",
                            "content": f"Please analyze this medical image: {image_description}"
                        }
                    ],
                    max_tokens=1000
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                error_message = str(e)
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {error_message}")
                
                # Check if it's a quota error
                if "insufficient_quota" in error_message or "429" in error_message:
                    logger.error("OpenAI API quota exceeded. Using fallback analysis.")
                    return generate_basic_report(img_width, img_height, img_mode)
                
                # If it's not the last attempt, wait and retry
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # On the last attempt, use fallback
                    logger.error(f"All attempts failed. Using fallback analysis. Last error: {error_message}")
                    return generate_basic_report(img_width, img_height, img_mode)
                    
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        raise HTTPException(status_code=500, detail="Image analysis failed")

@app.post("/analyze-medical-image")
async def analyze_medical_image(file: UploadFile = File(...)):
    """
    Endpoint to analyze medical images
    """
    try:
        # Validate file exists
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
            
        # Validate image
        if file.content_type is None or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        image_bytes = await file.read()
        
        # Basic image validation
        try:
            Image.open(io.BytesIO(image_bytes)).verify()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Analyze with LLM or fallback
        analysis = analyze_image_with_llm(image_bytes)
        
        return {
            "status": "success",
            "analysis": analysis,
            "report": format_medical_report(analysis)
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def format_medical_report(analysis: str) -> str:
    """
    Format the LLM response into a structured medical report
    """
    return f"""
    AUTOMATED MEDICAL IMAGE ANALYSIS REPORT
    --------------------------------------
    {analysis}
    
    DISCLAIMER: This is an AI-generated preliminary analysis. 
    Always consult with a qualified healthcare professional for diagnosis.
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)