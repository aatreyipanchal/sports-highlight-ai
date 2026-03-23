import os
import numpy as np
import librosa
import cv2
from moviepy import VideoFileClip
from transformers import BlipProcessor, BlipForConditionalGeneration, CLIPProcessor, CLIPModel
import torch
from PIL import Image

# Streamlit Caching Wrapper
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

def st_cache_resource(func):
    if HAS_STREAMLIT:
        return st.cache_resource(func)
    return func

@st_cache_resource
def get_models():
    """Load and cache all models."""
    print("Loading AI Models (Advanced Captions)...")
    blip_p = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    blip_m = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    clip_m = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    clip_p = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return blip_p, blip_m, clip_m, clip_p

# Sports Event Specific Prompts for Contextual AI
EVENT_PROMPTS = [
    "a goal being scored in a soccer match",
    "a goalkeeper making a spectacular save",
    "players celebrating a point or victory",
    "a tense moment near the goal line",
    "a player dribbling or running with the ball",
    "a foul or a tackle occurring",
    "fans cheering wildly in the stands"
]

# Pre-load or rely on lazy loading
# blip_processor, blip_model, clip_model, clip_processor = get_models()

# Contrastive Prompts
EXCITEMENT_PROMPTS = [
    "a spectacular goal or point in a sports match", # 0
    "players celebrating a major victory or score", # 1
    "an incredible action move in sports", # 2
    "a crowd explosion of cheering", # 3
    "a boring static view of a sports field", # 4 (Boring)
    "nothing special happening in the game", # 5 (Boring)
    "a person standing around doing nothing", # 6 (Boring)
    "an uninteresting background shot" # 7 (Boring)
]

def get_clip_margin(frame, clip_model, clip_processor):
    """
    Returns (Margin, is_score_likely)
    Margin = Total Excitement Probs - Total Boring Probs
    """
    img = Image.fromarray(frame).convert("RGB")
    inputs = clip_processor(text=EXCITEMENT_PROMPTS, images=img, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = clip_model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1).flatten()
    
    excitement_sum = float(torch.sum(probs[:4]))
    boring_sum = float(torch.sum(probs[4:]))
    
    margin = excitement_sum - boring_sum
    is_score = margin > 0.4 and float(torch.sum(probs[:2])) > 0.25
    
    return margin, is_score

def get_audio_explosiveness(video_path):
    """Analyzes audio for sudden 'explosive' energy growth."""
    temp_wav = "temp_explosive.wav"
    video_clip = VideoFileClip(video_path)
    if not video_clip.audio: return {}, {}
    
    video_clip.audio.write_audiofile(temp_wav, fps=22050, logger=None)
    y, sr = librosa.load(temp_wav, sr=None)
    os.remove(temp_wav)
    
    hop_length = 512
    energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    energy = (energy - np.min(energy)) / (np.max(energy) - np.min(energy) + 1e-6)
    
    explosiveness = np.diff(energy, prepend=0)
    explosiveness = np.maximum(0, explosiveness)
    
    times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
    audio_profile = {round(t, 1): float(e) for t, e in zip(times, energy)}
    explosive_profile = {round(t, 1): float(ex) for t, ex in zip(times, explosiveness)}
    
    return audio_profile, explosive_profile

def get_motion_score(frame, prev_gray):
    """Calculates motion intensity relative to previous frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    if prev_gray is None:
        return 0, gray
    
    delta = cv2.absdiff(prev_gray, gray)
    thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
    motion_energy = np.sum(thresh) / float(frame.shape[0] * frame.shape[1] * 255)
    return motion_energy, gray

def detect_highlights_extreme(video_path, window_step=0.5, progress_callback=None):
    """Weighted Multi-factor Engine with optional progress reporting."""
    blip_p, blip_m, clip_m, clip_p = get_models()
    
    print(f"--- Extreme Accuracy Analysis: {video_path} ---")
    video_clip = VideoFileClip(video_path)
    duration = video_clip.duration
    
    # 1. Pre-analyze Audio
    audio_norm, audio_explosiveness = get_audio_explosiveness(video_path)
    
    candidates = []
    prev_gray = None
    
    # 2. Main High-Res Scan
    time_points = np.arange(0, duration, window_step)
    total_steps = len(time_points)
    
    for i, t in enumerate(time_points):
        frame = video_clip.get_frame(t)
        
        # Factor A: CLIP Margin
        margin, is_score = get_clip_margin(frame, clip_m, clip_p)
        
        # Factor B: Audio Energy
        t_key = round(t, 1)
        audio_val = audio_norm.get(t_key, 0)
        explosive_val = audio_explosiveness.get(t_key, 0)
        
        # Factor C: Motion Intensity
        motion_val, prev_gray = get_motion_score(frame, prev_gray)
        
        composite_score = (0.6 * margin) + (0.2 * audio_val) + (0.2 * motion_val)
        if explosive_val > 0.05: composite_score += 0.15
        
        if composite_score > 0.45:
            candidates.append({'time': t, 'score': composite_score, 'is_score': is_score})
            
        if progress_callback:
            progress_callback(i / total_steps, f"Analyzing {t:.1f}s / {duration:.1f}s...")

    # 3. Segment Formation
    segments = []
    if not candidates: return []
    
    current_seg = {
        'start': candidates[0]['time'], 
        'end': candidates[0]['time'] + window_step, 
        'max_score': candidates[0]['score'],
        'has_score': candidates[0]['is_score']
    }
    
    for i in range(1, len(candidates)):
        c = candidates[i]
        if (c['time'] - current_seg['end'] < 0.6) and (c['is_score'] == current_seg['has_score']):
            current_seg['end'] = c['time'] + window_step
            current_seg['max_score'] = max(current_seg['max_score'], c['score'])
        else:
            segments.append(current_seg)
            current_seg = {
                'start': c['time'], 
                'end': c['time'] + window_step, 
                'max_score': c['score'],
                'has_score': c['is_score']
            }
    segments.append(current_seg)
    video_clip.close()
    
    final_segments = []
    for s in segments:
        if (s['end'] - s['start']) >= 1.0:
            label = "POINT/SCORE!" if s['has_score'] else "HIGHLIGHT"
            final_segments.append({**s, 'score': s['max_score'], 'label': label})
            
    final_segments.sort(key=lambda x: (x['label'] == "POINT/SCORE!", x['score']), reverse=True)
    return final_segments[:10]

def generate_description(video_path, start_time, end_time, label=None):
    """Elite AI Description Logic using BLIP-Large and CLIP-Context."""
    blip_p, blip_m, clip_m, clip_p = get_models()
    
    clip = VideoFileClip(video_path)
    # Check 3 points across the segment for best representation
    test_points = [start_time + 0.5, (start_time + end_time) / 2, end_time - 0.5]
    best_frame = None
    best_conf = -1
    best_event = "an exciting sports moment"
    
    # 1. Identify the best frame and specific event context using CLIP
    for tp in test_points:
        if 0 <= tp <= clip.duration:
            f = clip.get_frame(tp)
            img = Image.fromarray(f).convert("RGB")
            
            # Use specific Event Prompts for better context
            inputs = clip_p(text=EVENT_PROMPTS, images=img, return_tensors="pt", padding=True)
            with torch.no_grad():
                out = clip_m(**inputs)
            probs = out.logits_per_image.softmax(dim=1).flatten()
            
            conf = float(torch.max(probs))
            if conf > best_conf:
                best_conf = conf
                best_frame = f
                # Map back to event text
                best_event = EVENT_PROMPTS[int(torch.argmax(probs))]

    # 2. Use BLIP-Large with a "Guided Prefix" based on the detected event
    prompt = f"a sports match highlight reel showing {best_event} and"
    img = Image.fromarray(best_frame).convert("RGB")
    inputs = blip_p(img, prompt, return_tensors="pt")
    
    with torch.no_grad():
        out = blip_m.generate(**inputs, max_new_tokens=30, do_sample=True, top_k=50)
    
    description = blip_p.decode(out[0], skip_special_tokens=True).strip()
    
    # clean up prefix if it duplicated
    if description.startswith(prompt):
        description = description[len(prompt):].strip()
        description = f"{best_event.capitalize()}, {description}"
    
    clip.close()
    if label == "POINT/SCORE!" and "goal" not in description.lower():
         return f"GOAL! {description}"
    return description

def process_video_pipeline(video_path, progress_callback=None):
    """Full detection and description pipeline."""
    segments = detect_highlights_extreme(video_path, progress_callback=progress_callback)
    results = []
    for i, seg in enumerate(segments):
        description = generate_description(video_path, seg['start'], seg['end'], seg['label'])
        results.append({
            'id': i + 1,
            'start': round(seg['start'], 2),
            'end': round(seg['end'], 2),
            'description': description,
            'score': round(seg['score'], 4),
            'label': seg['label']
        })
    return results
