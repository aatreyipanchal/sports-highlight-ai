import streamlit as st
import os
import tempfile
import sys
from pathlib import Path

# Add src to path if needed
sys.path.append(str(Path(__file__).parent.parent))

from src.processor import detect_highlights_extreme, generate_description
from src.highlights import generate_highlights, timestamp_to_seconds

st.set_page_config(page_title="Elite Sports Highlight AI", page_icon="⚽", layout="wide")

st.title("⚽ Elite Sports Highlight AI")
st.markdown("### Generate professional highlight reels using AI-powered detection.")

# Sidebar for configuration
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader("Upload a sports match video", type=["mp4", "avi", "mov", "mkv"])

mode = st.sidebar.radio("Extraction Mode", ["Auto (AI Powered)", "Manual Selection"])

if uploaded_file is not None:
    # Save uploaded file to temp
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix)
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.sidebar.success("Video uploaded successfully!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.video(video_path)
        
    with col2:
        if mode == "Auto (AI Powered)":
            st.subheader("Auto-Highlight Detection")
            if st.button("Start AI Analysis"):
                with st.spinner("Analyzing video for exciting moments... This may take a while."):
                    try:
                        highlights = detect_highlights_extreme(video_path)
                        
                        if highlights:
                            st.session_state['detected_highlights'] = highlights
                            st.success(f"Detected {len(highlights)} highlights!")
                        else:
                            st.warning("No clear highlights detected.")
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
            
            if 'detected_highlights' in st.session_state:
                st.write("---")
                st.write("### Detected Highlights")
                for i, h in enumerate(st.session_state['detected_highlights']):
                    desc = generate_description(video_path, h['start'], h['end'], h.get('label'))
                    st.checkbox(f"Highlight {i+1}: {h['start']:.1f}s - {h['end']:.1f}s ({desc})", value=True, key=f"auto_check_{i}")
                    # Store desc for video gen
                    st.session_state['detected_highlights'][i]['description'] = desc

                if st.button("Generate Highlight Video"):
                    selected_highlights = []
                    for i, h in enumerate(st.session_state['detected_highlights']):
                        if st.session_state.get(f"auto_check_{i}"):
                            selected_highlights.append(h)
                    
                    if selected_highlights:
                        with st.spinner("Stitching highlights together..."):
                            output_path = "outputs/auto_streamlit_highlights.mp4"
                            os.makedirs("outputs", exist_ok=True)
                            generate_highlights(video_path, selected_highlights, output_path)
                            st.success("Highlight video generated!")
                            st.video(output_path)
                            with open(output_path, "rb") as f:
                                st.download_button("Download Highlights", f, file_name="highlights.mp4")
                    else:
                        st.warning("Please select at least one highlight.")

        else:  # Manual Mode
            st.subheader("Manual Highlight Selection")
            st.write("Enter time ranges (e.g. 00:01:20-00:01:45) below.")
            
            manual_text = st.text_area("Highlight Segments (Format: START-END: Description)", 
                                     placeholder="00:01:20-00:01:45: Amazing Goal\n00:02:10-00:02:30: Great Save")
            
            if st.button("Generate Manual Highlights"):
                if manual_text.strip():
                    from src.highlights import parse_highlight_text
                    segments = parse_highlight_text(manual_text)
                    if segments:
                        with st.spinner("Generating custom highlights..."):
                            output_path = "outputs/manual_streamlit_highlights.mp4"
                            os.makedirs("outputs", exist_ok=True)
                            generate_highlights(video_path, segments, output_path)
                            st.success("Video generated!")
                            st.video(output_path)
                            with open(output_path, "rb") as f:
                                st.download_button("Download Highlights", f, file_name="manual_highlights.mp4")
                    else:
                        st.error("Could not parse any segments. Please check the format.")
                else:
                    st.warning("Please enter at least one segment.")

else:
    st.info("Please upload a video file from the sidebar to begin.")
    
st.write("---")
st.caption("Powered by Elite AI Engine | Developed for Advanced Sports Analytics")
