import os
import logging
from pydub import AudioSegment
from app.config import TRANSITION_MS, CHANNELS, FRAME_RATE, LOW_PASS_FREQ
from app.utils import list_audio_files

logger = logging.getLogger(__name__)

def generate_mixtape(input_folder: str, output_path: str, transition_ms: int = None) -> str:
    """
    Generates a mixtape by concatenating audio files in a folder with smooth transitions.

    Args:
        input_folder (str): Path to the directory containing audio files.
        output_path (str): File path where the output mixtape will be saved.
        transition_ms (int, optional): Duration of the crossfade transition in milliseconds. Defaults to config.TRANSITION_MS.

    Returns:
        str: The path to the generated mixtape file.

    Raises:
        FileNotFoundError: If the input folder does not exist or contains no valid audio files.
    """
    if transition_ms is None:
        transition_ms = TRANSITION_MS

    if not os.path.isdir(input_folder):
        logger.error(f"Input folder not found: {input_folder}")
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    files = list_audio_files(input_folder)
    if not files:
        logger.error(f"No audio files found in: {input_folder}")
        raise FileNotFoundError(f"No audio files found in: {input_folder}")

    logger.info(f"Found {len(files)} audio files. Starting mixtape generation...")
    mixtape = None

    for i, file in enumerate(files):
        file_path = os.path.join(input_folder, file)
        logger.debug(f"Processing track {i+1}/{len(files)}: {file}")
        
        try:
            song = AudioSegment.from_file(file_path)
            song = song.set_channels(CHANNELS).set_frame_rate(FRAME_RATE)
            
            if mixtape is None:
                mixtape = song
            else:
                overlap = min(transition_ms, len(song), len(mixtape))
                outgoing = mixtape[-overlap:].fade_out(overlap).low_pass_filter(LOW_PASS_FREQ)
                incoming = song[:overlap].fade_in(overlap).low_pass_filter(LOW_PASS_FREQ)
                transition = outgoing.overlay(incoming)
                mixtape = mixtape[:-overlap] + transition + song[overlap:]
        except Exception as e:
            logger.warning(f"Failed to process track {file}: {e}. Skipping.")
            continue

    if mixtape is None:
        logger.error("Failed to process any audio files.")
        raise RuntimeError("Could not generate mixtape from provided files.")

    logger.info(f"Exporting mixtape to {output_path}...")
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        mixtape.export(output_path, format='mp3')
        logger.info("Mixtape generation complete.")
        return output_path
    except Exception as e:
        logger.error(f"Failed to export mixtape: {e}")
        raise
