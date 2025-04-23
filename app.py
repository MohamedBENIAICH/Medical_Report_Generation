import streamlit as st
import os
from PIL import Image
import base64
import requests
import json
from database import create_user, verify_user

# Set page config
st.set_page_config(
    page_title="Medical Report Generator",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state for authentication and language
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'language' not in st.session_state:
    st.session_state.language = 'English'

# Available languages
LANGUAGES = {
    'English': 'en',
    'Français': 'fr',
    'Español': 'es',
    'Deutsch': 'de',
    'Italiano': 'it',
    'Português': 'pt',
    'Nederlands': 'nl',
    'Polski': 'pl',
    'Русский': 'ru',
    '日本語': 'ja',
    '中文': 'zh',
    '한국어': 'ko',
    'العربية': 'ar'
}

# Language-specific prompts
LANGUAGE_PROMPTS = {
    'en': "Analyze this medical image in detail. Provide a comprehensive medical report including any visible conditions, abnormalities, or relevant medical observations. Format the response in a clear, professional manner suitable for medical documentation.",
    'fr': "Analysez cette image médicale en détail. Fournissez un rapport médical complet incluant toutes les conditions visibles, anomalies ou observations médicales pertinentes. Formatez la réponse de manière claire et professionnelle, adaptée à la documentation médicale.",
    'es': "Analice esta imagen médica en detalle. Proporcione un informe médico completo que incluya cualquier condición visible, anomalías u observaciones médicas relevantes. Formatee la respuesta de manera clara y profesional, adecuada para la documentación médica.",
    'de': "Analysieren Sie dieses medizinische Bild im Detail. Erstellen Sie einen umfassenden medizinischen Bericht, der alle sichtbaren Erkrankungen, Abnormalitäten oder relevanten medizinischen Beobachtungen enthält. Formatieren Sie die Antwort klar und professionell, geeignet für die medizinische Dokumentation.",
    'it': "Analizzare questa immagine medica in dettaglio. Fornire un rapporto medico completo che includa eventuali condizioni visibili, anomalie o osservazioni mediche rilevanti. Formattare la risposta in modo chiaro e professionale, adatto alla documentazione medica.",
    'pt': "Analise esta imagem médica em detalhes. Forneça um relatório médico abrangente incluindo quaisquer condições visíveis, anomalias ou observações médicas relevantes. Formate a resposta de maneira clara e profissional, adequada para documentação médica.",
    'nl': "Analyseer dit medische beeld in detail. Geef een uitgebreid medisch rapport met alle zichtbare aandoeningen, afwijkingen of relevante medische observaties. Formatteer het antwoord op een duidelijke, professionele manier die geschikt is voor medische documentatie.",
    'pl': "Przeanalizuj szczegółowo ten obraz medyczny. Przedstaw kompleksowy raport medyczny zawierający wszystkie widoczne schorzenia, nieprawidłowości lub istotne obserwacje medyczne. Sformatuj odpowiedź w jasny, profesjonalny sposób odpowiedni do dokumentacji medycznej.",
    'ru': "Проанализируйте это медицинское изображение подробно. Предоставьте комплексный медицинский отчет, включающий все видимые состояния, аномалии или соответствующие медицинские наблюдения. Отформатируйте ответ четко и профессионально, подходяще для медицинской документации.",
    'ja': "この医療画像を詳細に分析してください。見られる症状、異常、または関連する医療観察を含む包括的な医療報告書を提供してください。医療文書に適した明確で専門的な形式で回答を構成してください。",
    'zh': "详细分析这张医疗图像。提供一份全面的医疗报告，包括任何可见的病症、异常或相关医疗观察。以清晰、专业的方式格式化回答，适合医疗文档。",
    'ko': "이 의료 이미지를 자세히 분석하세요. 보이는 모든 상태, 이상 또는 관련 의료 관찰을 포함하는 포괄적인 의료 보고서를 제공하세요. 의료 문서에 적합한 명확하고 전문적인 방식으로 응답을 구성하세요.",
    'ar': "قم بتحليل هذه الصورة الطبية بالتفصيل. قدم تقريراً طبياً شاملاً يتضمن أي حالات مرئية أو تشوهات أو ملاحظات طبية ذات صلة. قم بتنسيق الرد بطريقة واضحة ومهنية مناسبة للتوثيق الطبي."
}

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .tab-content {
        padding: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

def login(username, password):
    user = verify_user(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.username = username
        return True
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.username = None

# Authentication UI
if not st.session_state.authenticated:
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        st.title("🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        st.title("📝 Sign Up")
        
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input("Email")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long!")
                else:
                    if create_user(new_username, new_password, email):
                        st.success("Account created successfully! Please login.")
                        st.rerun()
                    else:
                        st.error("Username or email already exists!")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Main application (only shown after authentication)
st.title("🏥 Medical Report Generator")
st.markdown(f"Welcome, {st.session_state.username}!")

# Language selection
selected_language = st.selectbox(
    "Select Report Language",
    options=list(LANGUAGES.keys()),
    index=list(LANGUAGES.keys()).index(st.session_state.language)
)
st.session_state.language = selected_language

# Add logout button
if st.button("Logout"):
    logout()
    st.rerun()

st.markdown("""
    Upload a medical image and get an AI-generated analysis report.
    This tool uses Google's Gemini AI to analyze medical images and provide detailed descriptions.
""")

# File uploader
uploaded_file = st.file_uploader("Choose a medical image...", type=['jpg', 'jpeg', 'png'])

# API Key input (you might want to store this securely in environment variables)
api_key = st.text_input("Enter your Google AI Studio API Key:", type="password")

if uploaded_file is not None and api_key:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # Convert image to base64
    image_bytes = uploaded_file.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode()
    
    # Analysis button
    if st.button("Generate Report"):
        with st.spinner("Analyzing image..."):
            try:
                # Prepare the request
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                
                headers = {
                    "Content-Type": "application/json"
                }
                
                # Get the appropriate prompt for the selected language
                language_code = LANGUAGES[selected_language]
                prompt = LANGUAGE_PROMPTS[language_code]
                
                data = {
                    "contents": [{
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": uploaded_file.type,
                                    "data": image_base64
                                }
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }]
                }
                
                # Make the API request
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                # Extract and display the analysis
                result = response.json()
                analysis = result['candidates'][0]['content']['parts'][0]['text']
                
                # Display the report in a nice format
                st.markdown("### 📋 Medical Analysis Report")
                st.markdown(analysis)
                
                # Add download button for the report
                report_data = f"Medical Analysis Report\n\n{analysis}"
                st.download_button(
                    label="Download Report",
                    data=report_data,
                    file_name=f"medical_report_{language_code}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Please check your API key and try again.")

elif uploaded_file is None:
    st.info("Please upload a medical image to begin analysis.")
elif not api_key:
    st.warning("Please enter your Google AI Studio API key to proceed.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Built with ❤️ using Streamlit and Google's Gemini AI</p>
    </div>
""", unsafe_allow_html=True) 