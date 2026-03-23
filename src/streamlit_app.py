import streamlit as st
import os
import tempfile
import sys
from pathlib import Path

# Add src to path if needed
sys.path.append(str(Path(__file__).parent.parent))

from src.processor import detect_highlights_extreme, generate_description, get_models
from src.highlights import generate_highlights, timestamp_to_seconds, parse_highlight_text

st.set_page_config(page_title="Sports Highlight AI", page_icon="⚽", layout="wide")

st.title("⚽ Sports Highlight AI")
st.markdown("### Generate professional highlight reels using AI-powered detection.")

# Pre-load models in background to avoid delay later
with st.sidebar:
    st.header("Configuration")
    if st.checkbox("Pre-load AI Models", value=True):
        with st.spinner("Loading AI Models..."):
            get_models()
            st.success("Models Ready!")

    uploaded_file = st.file_uploader("Upload a sports match video", type=["mp4", "avi", "mov", "mkv"])
    mode = st.radio("Extraction Mode", ["Auto (AI Powered)", "Manual Selection"])

if uploaded_file is not None:
    # Save uploaded file to temp
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix)
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.video(video_path)
        
    with col2:
        if mode == "Auto (AI Powered)":
            st.subheader("Auto-Highlight Detection")
            
            if st.button("Start AI Analysis"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_cb(percent, text):
                    progress_bar.progress(percent)
                    status_text.text(text)
                
                with st.spinner("AI is hunting for highlights..."):
                    try:
                        highlights = detect_highlights_extreme(video_path, progress_callback=progress_cb)
                        
                        if highlights:
                            st.session_state['detected_highlights'] = highlights
                            st.success(f"Found {len(highlights)} great moments!")
                        else:
                            st.warning("No clear highlights found in this footage.")
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
            
            if 'detected_highlights' in st.session_state:
                st.write("---")
                st.write("### Review Detected Highlights")
                
                selected_highlights = []
                for i, h in enumerate(st.session_state['detected_highlights']):
                    # Lazy generate descriptions only for detected highlights
                    if 'description' not in h:
                        with st.spinner(f"Describing highlight {i+1}..."):
                             h['description'] = generate_description(video_path, h['start'], h['end'], h.get('label'))
                    
                    is_selected = st.checkbox(f"#{i+1}: {h['start']:.1f}s - {h['end']:.1f}s ({h['description']})", 
                                            value=True, key=f"auto_check_{i}")
                    if is_selected:
                        selected_highlights.append(h)

                if st.button("Create Highlight Reel"):
                    if selected_highlights:
                        with st.spinner("Stitching your highlights together..."):
                            output_filename = "auto_highlights.mp4"
                            os.makedirs("outputs", exist_ok=True)
                            output_path = os.path.join("outputs", output_filename)
                            
                            generate_highlights(video_path, selected_highlights, output_path)
                            
                            st.success("Your highlight reel is ready!")
                            st.video(output_path)
                            with open(output_path, "rb") as f:
                                st.download_button("Download Reel", f, file_name="sports_highlights.mp4")
                    else:
                        st.warning("Please select at least one highlight.")

        else:  # Manual Mode
            st.subheader("Manual Highlight Selection")
            st.write("Enter time ranges below.")
            
            manual_text = st.text_area("Highlight Segments (Format: START-END: Description)", 
                                     placeholder="00:01:20-00:01:45: Stunning Goal\n00:05:10-00:05:30: Midfield Action",
                                     height=150)
            
            if st.button("Generate Custom Highlights"):
                if manual_text.strip():
                    segments = parse_highlight_text(manual_text)
                    if segments:
                        with st.spinner("Cutting and joining segments..."):
                            output_path = "outputs/manual_highlights.mp4"
                            os.makedirs("outputs", exist_ok=True)
                            generate_highlights(video_path, segments, output_path)
                            
                            st.success("Custom highlight reel created!")
                            st.video(output_path)
                            with open(output_path, "rb") as f:
                                st.download_button("Download Manual Reel", f, file_name="manual_highlights.mp4")
                    else:
                        st.error("Invalid format. Use 'START-END: Description' (e.g., 01:20-01:45: Goal)")
                else:
                    st.warning("Please provide at least one segment.")

    # Cleanup temp file button
    if st.sidebar.button("Clear Temp Video"):
        try:
            os.unlink(video_path)
            st.sidebar.info("Temporary files cleaned.")
            st.rerun()
        except:
            pass

else:
    st.info("Upload a video file from the sidebar to start extracting highlights.")
    
st.write("---")
st.caption("Developed for Advanced Sports Analytics")
