import re
import os
import argparse
from moviepy import VideoFileClip, concatenate_videoclips

def timestamp_to_seconds(ts):
    """Converts HH:MM:SS, MM:SS or SSS to seconds."""
    parts = list(map(float, ts.split(':')))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]

def parse_highlight_text(text, default_window=5):
    """
    Parses text for timestamps and descriptions.
    Formats supported:
    - START-END: Description
    - TIMESTAMP: Description (uses default_window around timestamp)
    """
    segments = []
    lines = text.strip().split('\n')
    
    # regex for HH:MM:SS or MM:SS or SS.SS
    ts_pattern = r'(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,2}:\d{1,2}|\d+(\.\d+)?)'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try range format: START-END: Description
        range_match = re.search(f'^{ts_pattern}\\s*-\\s*{ts_pattern}', line)
        if range_match:
            start = timestamp_to_seconds(range_match.group(1))
            end = timestamp_to_seconds(range_match.group(3))
            desc = line[range_match.end():].strip(' :')
            segments.append({'start': start, 'end': end, 'description': desc})
            continue
            
        # Try single timestamp: TIMESTAMP: Description
        single_match = re.search(f'^{ts_pattern}', line)
        if single_match:
            center = timestamp_to_seconds(single_match.group(1))
            desc = line[single_match.end():].strip(' :')
            segments.append({
                'start': max(0, center - default_window),
                'end': center + default_window,
                'description': desc
            })
            
    return segments

def generate_highlights(video_path, segments, output_path="outputs/highlights.mp4"):
    """Extracts segments and concatenates them into a single video."""
    if not segments:
        print("No segments found to process.")
        return
        
    print(f"Loading video: {video_path}")
    video = VideoFileClip(video_path)
    clips = []
    
    for seg in segments:
        print(f"Extracting segment: {seg['start']}s to {seg['end']}s ({seg['description']})")
        # Ensure end doesn't exceed video duration
        end = min(seg['end'], video.duration)
        if seg['start'] >= video.duration:
            print(f"Skipping segment starting at {seg['start']}s (video duration: {video.duration}s)")
            continue
            
        clip = video.subclipped(seg['start'], end)
        clips.append(clip)
        
    if not clips:
        print("No valid clips extracted.")
        return
        
    print(f"Concatenating {len(clips)} highlights...")
    final_clip = concatenate_videoclips(clips)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    video.close()
    for clip in clips:
        clip.close()
    final_clip.close()
    print(f"Highlight video saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate sports highlights from video and text descriptions.")
    
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--text", type=str, help="Text description of highlights")
    parser.add_argument("--file", type=str, help="Path to text file with highlight descriptions")
    parser.add_argument("--output", type=str, default="outputs/highlights.mp4", help="Path to save output video")
    parser.add_argument("--window", type=int, default=5, help="Default secondary window for single timestamps")
    
    args = parser.parse_args()
    
    highlight_text = ""
    if args.file:
        with open(args.file, 'r') as f:
            highlight_text = f.read()
    elif args.text:
        highlight_text = args.text
    else:
        print("Error: Either --text or --file must be provided.")
        return
        
    segments = parse_highlight_text(highlight_text, default_window=args.window)
    generate_highlights(args.video, segments, args.output)

if __name__ == "__main__":
    main()
