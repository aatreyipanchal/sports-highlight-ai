import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
import uuid
from .processor import process_video_pipeline, generate_description

app = FastAPI(title="Sports Highlight API")

# Mount uploads directory for video playback
app.mount("/videos", StaticFiles(directory="uploads"), name="videos")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class TimeRangeRequest(BaseModel):
    video_path: str
    start: float
    end: float

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
