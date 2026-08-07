import os
import logging
from pydub import AudioSegment
from app.config import TRANSITION_MS, DEFAULT_HASHTAGS
from app.utils import list_audio_files

logger = logging.getLogger(__name__)

def generate_description(input_folder: str, mixtape_name: str, genre: str, transition_ms: int = None, hashtags: list = None) -> str:
    """
    Generates a YouTube description with tracklist and timestamps for the mixtape.

    Args:
        input_folder (str): Path to the directory containing audio files.
        mixtape_name (str): The name/title of the mixtape.
        genre (str): The genre of the mixtape.
        transition_ms (int, optional): Transition duration in ms, used for timestamp calculation. Defaults to config.TRANSITION_MS.
        hashtags (list, optional): List of hashtags. Defaults to config.DEFAULT_HASHTAGS.

    Returns:
        str: The generated description.
    """
    if transition_ms is None:
        transition_ms = TRANSITION_MS
    if hashtags is None:
        hashtags = DEFAULT_HASHTAGS

    if not os.path.isdir(input_folder):
        logger.error(f"Input folder not found: {input_folder}")
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    files = list_audio_files(input_folder)
    if not files:
        logger.error(f"No audio files found in: {input_folder}")
        raise FileNotFoundError(f"No audio files found in: {input_folder}")

    current_time = 0.0
    tracklist = []
    
    logger.info("Generating description tracklist...")
    for file in files:
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        track_name = os.path.splitext(file)[0]
        tracklist.append(f"{minutes:02d}:{seconds:02d} {track_name}")
        
        file_path = os.path.join(input_folder, file)
        try:
            song = AudioSegment.from_file(file_path)
            duration = len(song) / 1000.0
            current_time += duration - (transition_ms / 1000.0)
        except Exception as e:
            logger.warning(f"Could not read {file} for duration calculation: {e}")

    description = f"🔥 {mixtape_name} 🔥\n\n"
    description += f"🎵 Genre: {genre}\n\n"
    description += "🎵 Tracklist\n"
    description += "\n".join(tracklist)
    description += "\n\n💽 Download / Listen Links\n"
    description += "Find these tracks on Spotify, Apple Music or your favorite streaming platform.\n\n"
    description += "🎧 Follow for more DJ mixes!\n\n"
    description += " ".join(hashtags)
    
    logger.info("Description generation complete.")
    return description

def save_description(description: str, output_path: str) -> str:
    """
    Saves the generated description to a text file.

    Args:
        description (str): The description string.
        output_path (str): File path to save the description.

    Returns:
        str: The path to the saved description file.
    """
    logger.info(f"Saving description to {output_path}")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(description)
        return output_path
    except Exception as e:
        logger.error(f"Failed to save description: {e}")
        raise
