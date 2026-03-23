import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
import uuid
from .processor import process_video_pipeline, generate_description
from .highlights import generate_highlights, timestamp_to_seconds

app = FastAPI(title="Sports Highlight AI Engine")

# Load configuration from environment
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Mount uploads directory for video playback
app.mount("/videos", StaticFiles(directory="uploads"), name="videos")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class TimeRangeRequest(BaseModel):
    video_path: str
    start: float
    end: float

class HighlightSegment(BaseModel):
    start: str  # Can be HH:MM:SS or seconds
    end: str
    description: str = "Highlight"

class ManualHighlightRequest(BaseModel):
    file_id: str
    segments: list[HighlightSegment]

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"file_id": file_id, "file_path": file_path}

@app.get("/highlights/{file_id}")
async def get_highlights(file_id: str):
    # Find the file in uploads
    file_path = None
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(file_id):
            file_path = os.path.join(UPLOAD_DIR, f)
            break
            
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        highlights = process_video_pipeline(file_path)
        return {"highlights": highlights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/describe")
async def describe_segment(req: TimeRangeRequest):
    if not os.path.exists(req.video_path):
         raise HTTPException(status_code=404, detail="File not found")
    
    try:
        desc = generate_description(req.video_path, req.start, req.end)
        return {"description": desc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manual-highlights")
async def extract_manual_highlights(req: ManualHighlightRequest):
    # Find the file in uploads
    file_path = None
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(req.file_id):
            file_path = os.path.join(UPLOAD_DIR, f)
            break
            
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        # Convert segments to the format expected by generate_highlights
        processed_segments = []
        for seg in req.segments:
            processed_segments.append({
                'start': timestamp_to_seconds(seg.start),
                'end': timestamp_to_seconds(seg.end),
                'description': seg.description
            })
            
        output_filename = f"manual_{req.file_id}.mp4"
        output_path = os.path.join("outputs", output_filename)
        
        generate_highlights(file_path, processed_segments, output_path)
        
        return {
            "status": "success",
            "video_url": f"/outputs/{output_filename}",
            "segments": processed_segments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-highlights/{file_id}")
async def extract_auto_highlights(file_id: str):
    # Find the file in uploads
    file_path = None
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(file_id):
            file_path = os.path.join(UPLOAD_DIR, f)
            break
            
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        # 1. Detect highlights
        highlights = process_video_pipeline(file_path)
        
        # 2. Generate video
        if highlights:
            output_filename = f"auto_{file_id}.mp4"
            output_path = os.path.join("outputs", output_filename)
            
            # format highlights for generate_highlights
            segments = []
            for h in highlights:
                segments.append({
                    'start': h['start'],
                    'end': h['end'],
                    'description': h['description']
                })
            
            generate_highlights(file_path, segments, output_path)
            
            return {
                "status": "success",
                "video_url": f"/outputs/{output_filename}",
                "highlights": highlights
            }
        else:
            return {"status": "no_highlights_found", "highlights": []}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount outputs directory for video playback
os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
