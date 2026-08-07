import os
import subprocess
import logging
from PIL import Image
from app.config import VIDEO_RESOLUTION, FPS, PRESET, AUDIO_BITRATE, VIDEO_CODEC, AUDIO_CODEC, OUTPUT_DIR
from app.utils import get_unique_filename

logger = logging.getLogger(__name__)

def generate_video(image_path: str, audio_path: str, output_path: str, resolution: tuple = None, fps: int = None, preset: str = None) -> str:
    """
    Generates a static image video with background audio using FFmpeg.

    Args:
        image_path (str): Path to the input image file.
        audio_path (str): Path to the input audio (mixtape) file.
        output_path (str): File path for the output video.
        resolution (tuple, optional): Video resolution (width, height). Defaults to config.VIDEO_RESOLUTION.
        fps (int, optional): Frames per second. Defaults to config.FPS.
        preset (str, optional): FFmpeg preset for encoding speed/quality. Defaults to config.PRESET.

    Returns:
        str: The path to the generated video file.
    
    Raises:
        FileNotFoundError: If the input image or audio file doesn't exist.
        subprocess.CalledProcessError: If FFmpeg execution fails.
    """
    if resolution is None:
        resolution = VIDEO_RESOLUTION
    if fps is None:
        fps = FPS
    if preset is None:
        preset = PRESET

    if not os.path.isfile(image_path):
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    if not os.path.isfile(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    temp_image_path = os.path.join(OUTPUT_DIR, "temp_resized_image.jpg")
    
    try:
        logger.info(f"Resizing image to {resolution}...")
        img = Image.open(image_path)
        img = img.resize(resolution)
        img.save(temp_image_path)
        
        logger.info(f"Starting video generation at {output_path}...")
        cmd = [
            'ffmpeg', '-y', '-loop', '1',
            '-i', temp_image_path,
            '-i', audio_path,
            '-c:v', VIDEO_CODEC, '-preset', preset,
            '-tune', 'stillimage',
            '-r', str(fps),
            '-c:a', AUDIO_CODEC, '-b:a', AUDIO_BITRATE,
            '-shortest', output_path
        ]
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Video generation complete.")
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed with error: {e.stderr.decode('utf-8', errors='ignore')}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate video: {e}")
        raise
    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            logger.debug(f"Cleaned up temp image: {temp_image_path}")
