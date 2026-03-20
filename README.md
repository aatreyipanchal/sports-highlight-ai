# Sports Highlight AI Pipeline 🏆

An automated sports highlight generation system that uses a **Weighted Multi-factor Engine** to identify and describe key moments in any sports video.

## Features
- **Extreme Accuracy Detection**: Combines Contrastive CLIP margins, Audio Explosiveness, and Visual Motion.
- **Semantic Event Splitting**: Automatically separates scoring events from celebrations.
- **Sport-Agnostic**: Works for Soccer, Basketball, Football, Cricket, and more.
- **Intelligent Captioning**: Uses BLIP (Vision-Language Model) for context-aware descriptions.
- **Premium Dashboard**: Built with Next.js 15 and Tailwind CSS.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- FFmpeg (for video processing)

### Installation
1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Frontend dependencies:
   ```bash
   cd web
   npm install
   ```

### Running the App
Use the orchestrator script to start both the backend and frontend:
```bash
python run.py
```

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000

## Tech Stack
- **Backend**: FastAPI, MoviePy, Librosa, Transformers (CLIP, BLIP)
- **Frontend**: Next.js, React, Tailwind CSS, Framer Motion
- **Models**: OpenAI CLIP, Salesforce BLIP

---
*Developed by aatreyipanchal*
