import logging
import os
import shutil
import uuid
from typing import List, Optional, Tuple

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import (
    MIXTAPE_DIR, IMAGES_DIR, OUTPUT_DIR, TRANSITION_MS, 
    VIDEO_RESOLUTION, FPS, PRESET, DEFAULT_HASHTAGS
)
from app.utils import (
    list_audio_files, list_image_files, ensure_dir, 
    get_unique_filename, create_job, update_job, get_job
)
from app.audio import generate_mixtape
from app.description import generate_description, save_description
from app.video import generate_video

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title='YT Mixtape API', 
    version='1.0.0', 
    description='API for creating audio mixtapes and generating videos with descriptions for YouTube.'
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Ensure required directories exist on startup."""
    logger.info("Starting up YT Mixtape API. Ensuring directories exist...")
    ensure_dir(MIXTAPE_DIR)
    ensure_dir(IMAGES_DIR)
    ensure_dir(OUTPUT_DIR)


# --- Pydantic Models ---

class GenerateMixtapeRequest(BaseModel):
    transition_ms: Optional[int] = TRANSITION_MS

class GenerateDescriptionRequest(BaseModel):
    mixtape_name: str
    genre: str
    transition_ms: Optional[int] = TRANSITION_MS
    hashtags: Optional[List[str]] = DEFAULT_HASHTAGS

class GenerateVideoRequest(BaseModel):
    image_filename: Optional[str] = None
    audio_filename: Optional[str] = None
    resolution: Optional[Tuple[int, int]] = VIDEO_RESOLUTION
    fps: Optional[int] = FPS

class GenerateAllRequest(BaseModel):
    mixtape_name: str
    genre: str
    image_filename: Optional[str] = None
    transition_ms: Optional[int] = TRANSITION_MS


# --- Background Task Handlers ---

def task_generate_mixtape(job_id: str, transition_ms: int):
    """Background task to generate a mixtape."""
    try:
        logger.info(f"Starting mixtape generation for job {job_id}")
        output_filename = get_unique_filename("mixtape", ".mp3")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        result_path = generate_mixtape(
            input_folder=MIXTAPE_DIR, 
            output_path=output_path, 
            transition_ms=transition_ms
        )
        
        logger.info(f"Mixtape generation successful for job {job_id}: {result_path}")
        update_job(job_id, status="completed", result={"mixtape_path": result_path, "filename": output_filename})
    except Exception as e:
        logger.error(f"Error generating mixtape for job {job_id}: {e}")
        update_job(job_id, status="failed", error=str(e))

def task_generate_video(job_id: str, image_path: str, audio_path: str, resolution: tuple, fps: int):
    """Background task to generate a video."""
    try:
        logger.info(f"Starting video generation for job {job_id}")
        output_filename = get_unique_filename("video", ".mp4")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        result_path = generate_video(
            image_path=image_path,
            audio_path=audio_path,
            output_path=output_path,
            resolution=resolution,
            fps=fps,
            preset=PRESET
        )
        
        logger.info(f"Video generation successful for job {job_id}: {result_path}")
        update_job(job_id, status="completed", result={"video_path": result_path, "filename": output_filename})
    except Exception as e:
        logger.error(f"Error generating video for job {job_id}: {e}")
        update_job(job_id, status="failed", error=str(e))

def task_generate_all(job_id: str, request: GenerateAllRequest):
    """Background task to run the full pipeline."""
    try:
        logger.info(f"Starting full pipeline for job {job_id}")
        
        # 1. Generate Mixtape
        audio_filename = get_unique_filename("mixtape", ".mp3")
        audio_path = os.path.join(OUTPUT_DIR, audio_filename)
        logger.info(f"Step 1: Generating mixtape {audio_path}")
        
        generate_mixtape(
            input_folder=MIXTAPE_DIR, 
            output_path=audio_path, 
            transition_ms=request.transition_ms
        )
        
        # 2. Generate Description
        desc_filename = get_unique_filename("description", ".txt")
        desc_path = os.path.join(OUTPUT_DIR, desc_filename)
        logger.info(f"Step 2: Generating description {desc_path}")
        
        description_text = generate_description(
            input_folder=MIXTAPE_DIR,
            mixtape_name=request.mixtape_name,
            genre=request.genre,
            transition_ms=request.transition_ms
        )
        save_description(description_text, desc_path)
        
        # 3. Generate Video
        video_filename = get_unique_filename("video", ".mp4")
        video_path = os.path.join(OUTPUT_DIR, video_filename)
        
        # Determine image
        image_path = None
        if request.image_filename:
            image_path = os.path.join(IMAGES_DIR, request.image_filename)
        else:
            images = list_image_files(IMAGES_DIR)
            if images:
                image_path = os.path.join(IMAGES_DIR, images[0])
            else:
                raise ValueError("No images found in IMAGES_DIR to generate video.")
                
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        logger.info(f"Step 3: Generating video {video_path} using image {image_path}")
        
        generate_video(
            image_path=image_path,
            audio_path=audio_path,
            output_path=video_path,
            resolution=VIDEO_RESOLUTION,
            fps=FPS,
            preset=PRESET
        )
        
        logger.info(f"Full pipeline successful for job {job_id}")
        update_job(job_id, status="completed", result={
            "audio_filename": audio_filename,
            "description_filename": desc_filename,
            "video_filename": video_filename
        })
    except Exception as e:
        logger.error(f"Error in full pipeline for job {job_id}: {e}")
        update_job(job_id, status="failed", error=str(e))


# --- API Endpoints ---

@app.post("/api/upload-tracks")
async def upload_tracks(files: List[UploadFile] = File(...)):
    """Upload multiple audio files to the mixtape directory."""
    saved_files = []
    for file in files:
        file_path = os.path.join(MIXTAPE_DIR, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)
        except Exception as e:
            logger.error(f"Failed to save {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}")
    
    return {"message": "Files uploaded successfully", "filenames": saved_files}

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload a single image file for the video background."""
    file_path = os.path.join(IMAGES_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": "Image uploaded successfully", "filename": file.filename}
    except Exception as e:
        logger.error(f"Failed to save image {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save image {file.filename}")

@app.post("/api/generate-mixtape")
async def generate_mixtape_endpoint(request: GenerateMixtapeRequest, background_tasks: BackgroundTasks):
    """Start a background task to generate a mixtape from uploaded tracks."""
    tracks = list_audio_files(MIXTAPE_DIR)
    if not tracks:
        raise HTTPException(status_code=400, detail="No audio tracks found in the mixtape directory.")
        
    job_id = str(uuid.uuid4())
    create_job(job_id, "Generating Mixtape")
    
    background_tasks.add_task(task_generate_mixtape, job_id, request.transition_ms)
    
    return {"message": "Mixtape generation started", "job_id": job_id}

@app.post("/api/generate-description")
async def generate_description_endpoint(request: GenerateDescriptionRequest):
    """Generate a description for the mixtape (synchronous)."""
    try:
        desc_filename = get_unique_filename("description", ".txt")
        desc_path = os.path.join(OUTPUT_DIR, desc_filename)
        
        description_text = generate_description(
            input_folder=MIXTAPE_DIR,
            mixtape_name=request.mixtape_name,
            genre=request.genre,
            transition_ms=request.transition_ms,
            hashtags=request.hashtags
        )
        
        save_description(description_text, desc_path)
        
        return {
            "message": "Description generated successfully",
            "filename": desc_filename,
            "description": description_text
        }
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating description: {str(e)}")

@app.post("/api/generate-video")
async def generate_video_endpoint(request: GenerateVideoRequest, background_tasks: BackgroundTasks):
    """Start a background task to generate a video using an image and an audio file."""
    image_path = None
    if request.image_filename:
        image_path = os.path.join(IMAGES_DIR, request.image_filename)
    else:
        images = list_image_files(IMAGES_DIR)
        if images:
            image_path = os.path.join(IMAGES_DIR, images[0])
            
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found.")

    audio_path = None
    if request.audio_filename:
        audio_path = os.path.join(OUTPUT_DIR, request.audio_filename)
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found in output directory.")
    else:
        # Just grab the first audio in OUTPUT_DIR for convenience if not specified
        outputs = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp3')]
        if outputs:
            audio_path = os.path.join(OUTPUT_DIR, outputs[0])
        else:
            raise HTTPException(status_code=404, detail="No audio file provided and none found in output directory.")

    job_id = str(uuid.uuid4())
    create_job(job_id, "Generating Video")
    
    background_tasks.add_task(
        task_generate_video, 
        job_id, 
        image_path, 
        audio_path, 
        request.resolution, 
        request.fps
    )
    
    return {"message": "Video generation started", "job_id": job_id}

@app.post("/api/generate-all")
async def generate_all_endpoint(request: GenerateAllRequest, background_tasks: BackgroundTasks):
    """Start a background task to run the full pipeline: mixtape -> description -> video."""
    tracks = list_audio_files(MIXTAPE_DIR)
    if not tracks:
        raise HTTPException(status_code=400, detail="No audio tracks found.")
        
    job_id = str(uuid.uuid4())
    create_job(job_id, "Running Full Pipeline")
    
    background_tasks.add_task(task_generate_all, job_id, request)
    
    return {"message": "Full pipeline started", "job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def get_job_endpoint(job_id: str):
    """Get the status and result of a background job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Serve a file from the output directory."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename)

@app.get("/api/list-tracks")
async def list_tracks_endpoint():
    """List all audio tracks currently in the mixtape directory."""
    try:
        files = list_audio_files(MIXTAPE_DIR)
        return {"tracks": files}
    except (FileNotFoundError, ValueError):
        return {"tracks": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list-images")
async def list_images_endpoint():
    """List all images currently in the images directory."""
    try:
        files = list_image_files(IMAGES_DIR)
        return {"images": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clear-tracks")
async def clear_tracks_endpoint():
    """Remove all files from the mixtape directory."""
    try:
        count = 0
        for filename in os.listdir(MIXTAPE_DIR):
            file_path = os.path.join(MIXTAPE_DIR, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
                count += 1
        return {"message": "Tracks cleared", "deleted_count": count}
    except Exception as e:
        logger.error(f"Error clearing tracks: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing tracks: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
