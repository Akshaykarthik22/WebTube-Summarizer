import streamlit as st  # type: ignore
from dotenv import load_dotenv  # type: ignore
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai  # type: ignore
from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Ensure API Key is set
if not API_KEY:
    st.error("⚠️ API Key is missing! Set GOOGLE_API_KEY in your .env file.")
    st.stop()

# Configure Google Generative AI
genai.configure(api_key=API_KEY)

# Navigation Logic
def navigate_to(page):
    st.session_state["current_page"] = page

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"

# Global Prompt for YouTube Summarizer
YOUTUBE_PROMPT = """You are a YouTube video summarizer. You will take the transcript text and summarize the entire video in points within 250 words.
Start with the title in **bold and capitalized (center aligned)**, followed by a summary and important points.
Use **emojis** to make it engaging and suggest image sources for better understanding."""

# YouTube Transcript Extraction
def extract_transcript_details(youtube_video_url):
    """Extracts transcript from YouTube video."""
    try:
        video_id = youtube_video_url.split("v=")[-1].split("&")[0]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([i["text"] for i in transcript_text])
        return transcript, video_id
    except Exception as e:
        return None, str(e)

# Gemini AI Content Generation
def generate_gemini_content(transcript_text, prompt):
    """Generates summary using Gemini AI."""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")  # Updated to latest model
        response = model.generate_content(prompt + transcript_text)
        return response.text if response else "⚠️ No response from AI."
    except Exception as e:
        return f"⚠️ Error in AI generation: {e}"

# Home Page
if st.session_state["current_page"] == "home":
    st.title("📜 AI Summarizer App")

    st.markdown("""
    🔹 **Features:**
    - 🎥 *YouTube Summarizer*: Extract and summarize video transcripts.
    - 🌍 *Website Summarizer*: Summarize any webpage content.

    Select an option below:
    """)

    if st.button("Go to YouTube Summarizer"):
        navigate_to("youtube")

    if st.button("Go to Website Summarizer"):
        navigate_to("website")

# YouTube Summarizer Page
elif st.session_state["current_page"] == "youtube":
    st.title("🎥 YouTube Video Summarizer")

    youtube_link = st.text_input("🔗 Enter YouTube video link:")
    
    if st.button("🔙 Back to Home"):
        navigate_to("home")

    if youtube_link:
        transcript_text, video_id = extract_transcript_details(youtube_link)

        if transcript_text:
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", caption="Thumbnail")
            
            if st.button("✨ Generate Summary"):
                summary = generate_gemini_content(transcript_text, YOUTUBE_PROMPT)
                st.markdown("### 📌 Summary:")
                st.markdown(summary, unsafe_allow_html=True)  # ✅ FIXED HERE
        else:
            st.error(f"⚠️ Error extracting transcript: {video_id}")

# Website Summarizer Page
elif st.session_state["current_page"] == "website":
    def fetch_website_content(url):
        """Fetches and extracts main text from a webpage."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text() for p in paragraphs if p.get_text())
            return text if text else "⚠️ No content found."
        except Exception as e:
            return f"⚠️ Error fetching content: {e}"

    def summarize_text(text):
        """Summarizes text using Gemini AI."""
        try:
            if len(text) > 10000:  # Limit text size
                text = text[:10000]
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(
                f"Summarize this in an easy-to-understand format:\n{text}"
            )
            return response.text if response else "⚠️ No summary generated."
        except Exception as e:
            return f"⚠️ Error in summarization: {e}"

    st.title("🌍 Website Summarizer")
    url = st.text_input("🔗 Enter Website URL:")

    if st.button("🔙 Back to Home"):
        navigate_to("home")

    if url:
        with st.spinner("⏳ Fetching and summarizing..."):
            content = fetch_website_content(url)
            if "⚠️" not in content:
                summary = summarize_text(content)
                st.subheader("📌 Summary:")
                st.markdown(summary, unsafe_allow_html=True)  # ✅ FIXED HERE
            else:
                st.error(content)
