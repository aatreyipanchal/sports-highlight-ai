from src.processor import process_video_pipeline
import os

def test_pipeline():
    video_path = "soccer_match.mp4"
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found.")
        return
        
    print("Starting pipeline test...")
    results = process_video_pipeline(video_path)
    
    print("\n--- Highlight Results ---")
    for res in results:
        print(f"ID: {res['id']} | {res['start']}s - {res['end']}s | Score: {res['score']}")
        print(f"Description: {res['description']}\n")

if __name__ == "__main__":
    test_pipeline()
