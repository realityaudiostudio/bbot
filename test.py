import streamlit as st
from PIL import Image
import google.generativeai as genai
from supabase import create_client, Client
import re
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
# Supabase credentials
# SUPABASE_URL = "https://klwbglknjadrgzrabckg.supabase.co"
# SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtsd2JnbGtuamFkcmd6cmFiY2tnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgxOTAxMjQsImV4cCI6MjA2Mzc2NjEyNH0.C84YObxDdxHMq32WHpTkCDpMXc_fFaNE1A-td4BCymU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Google Gemini setup
# GENAI_API_KEY = "AIzaSyA9b9YZBLkxBOhRd1wDahGYbZkUI4YU9Qk"
genai.configure(api_key=GENAI_API_KEY)

# Streamlit config
st.set_page_config(page_title="LLM Prompt Window", layout="centered")

# Styling
st.markdown("""
    <style>
    body {
        background-color: #111;
        color: #fff;
    }
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        background-color: #222;
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 10px;
        max-height: 200px;
    }
    .stFileUploader>div>button {
        background-color: #555;
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }
    .stButton>button {
        background-color: #2196F3;
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }
    .or-divider {
        text-align: center;
        margin: 20px 0;
        color: #666;
    }
    .stFileUploader>div>div {
        max-height: 200px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;font-size: 90px;'>BBot</h1>", unsafe_allow_html=True)

# Get question number from URL
question_id = st.query_params.get("qno", None)

# Default values
question_text = ""
initial_prompt = ""

# Fetch question from Supabase
if question_id:
    try:
        data = supabase.table("assignments").select("*").eq("id", int(question_id)).execute()
        if data.data:
            question_data = data.data[0]
            question_text = question_data.get("qn", "")
            initial_prompt = question_data.get("evaluation", "")
        else:
            st.warning("No question found with this ID.")
    except Exception as e:
        st.error(f"Error fetching question: {e}")

# Display question if available
if question_text:
    st.markdown(f"### Question\n{question_text}")

# Input: File or text
uploaded_file = st.file_uploader("Upload File", type=["jpg", "jpeg", "png"])
st.markdown('<div class="or-divider">OR</div>', unsafe_allow_html=True)
case_text = st.text_area("Paste case text here", height=200)

# Handle submit
if st.button("Generate Brief"):
    if not uploaded_file and not case_text:
        st.warning("Please upload a file or enter case text.")
    else:
        model = genai.GenerativeModel('gemini-2.0-flash')
        inputs = []

        if uploaded_file:
            img = Image.open(uploaded_file)
            inputs.append(img)
        if initial_prompt:
            inputs.append(initial_prompt)
        if case_text:
            inputs.append(case_text)

        # Add evaluation instructions
        # Custom evaluation based on Supabase question
        evaluation_prompt = (
            f"The question is: \"{question_text}\"\n"
            "Evaluate the provided input (image or text) based on whether it answers the question appropriately. "
            "Consider relevance, correctness, and clarity. "
            "Give a score in the format 'Score: X/10' and explain briefly why."
                        )

        inputs.append(evaluation_prompt)

        try:
            response = model.generate_content(inputs)
            result_text = response.text

            # Show full result
            st.markdown("**Evaluation Result:**")
            st.write(result_text)

            # Extract score
            match = re.search(r"Score:\s*(\d+)/10", result_text)
            if match:
                score = int(match.group(1))
                st.markdown(f"### 🔢 Score: **{score}/10**")
            else:
                st.warning("Could not extract score from the response.")

        except Exception as e:
            st.error(f"Error generating content: {e}")
