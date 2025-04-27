const fs = require("fs");
const axios = require("axios");

// TODO: Replace this with your valid API key from Google AI Studio
// Get your API key from: https://makersuite.google.com/app/apikey
const API_KEY = "AIzaSyCwZPLUliJQXuZrrFW-0t0kYJCzcnYteLk";

// Load image as base64
const imagePath = "maladie_.jpeg";
const imageBase64 = fs.readFileSync(imagePath, { encoding: "base64" });

// Gemini API URL
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`;

async function analyzeImage() {
  const requestData = {
    contents: [
      {
        parts: [
          {
            inline_data: {
              mime_type: "image/jpeg",
              data: imageBase64,
            },
          },
          {
            text: "Describe the image in detail.",
          },
        ],
      },
    ],
  };

  try {
    const response = await axios.post(GEMINI_URL, requestData, {
      headers: {
        "Content-Type": "application/json",
      },
    });

    const text = response.data.candidates[0].content.parts[0].text;
    console.log("Image Analysis:\n", text);
  } catch (error) {
    console.error("Error:", error.response?.data || error.message);
  }
}

analyzeImage();
