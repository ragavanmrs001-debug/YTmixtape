import streamlit as st
import requests
import time
import os
import re
from datetime import datetime

# --- API Configuration ---
API_BASE = 'http://localhost:8000/api'

# --- Page Config ---
st.set_page_config(page_title='YT Mixtape Studio', page_icon='🎵', layout='wide')

# --- Premium Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

/* Base Styles */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #e2e8f0;
}
.stApp {
    background-color: #0e1117;
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(108, 99, 255, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 85% 30%, rgba(233, 30, 99, 0.08) 0%, transparent 50%);
    background-attachment: fixed;
}

/* Gradient Text */
.gradient-text {
    background: linear-gradient(135deg, #6c63ff 0%, #e91e63 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 3rem;
    margin-bottom: 0;
    padding-bottom: 5px;
}
.sub-text {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: rgba(26, 26, 46, 0.7);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6c63ff, #e91e63);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(233, 30, 99, 0.2);
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(233, 30, 99, 0.4);
    border-color: transparent;
    color: white;
}
.stButton > button:active {
    transform: translateY(0);
}

/* Secondary Button (Clear tracks etc) */
div[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: none;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.5);
    color: #ff5252;
}

/* Inputs and Text Areas */
.stTextInput > div > div > input, 
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: white;
    transition: all 0.3s ease;
}
.stTextInput > div > div > input:focus, 
.stTextArea > div > div > textarea:focus {
    border-color: #6c63ff;
    box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2);
}

/* File Uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(255, 255, 255, 0.02);
    border: 2px dashed rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    transition: all 0.3s ease;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: #6c63ff;
    background-color: rgba(108, 99, 255, 0.05);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    gap: 2rem;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(255, 255, 255, 0.6);
    background-color: transparent;
    border: none;
    font-size: 1.1rem;
    font-weight: 600;
    padding: 10px 0;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: white;
    border-bottom: 2px solid #e91e63;
}

/* Status Indicators */
.status-connected {
    color: #4caf50;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px;
    background: rgba(76, 175, 80, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(76, 175, 80, 0.2);
}
.status-connected::before {
    content: '';
    display: inline-block;
    width: 10px;
    height: 10px;
    background-color: #4caf50;
    border-radius: 50%;
    box-shadow: 0 0 10px #4caf50;
}
.status-disconnected {
    color: #f44336;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px;
    background: rgba(244, 67, 54, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(244, 67, 54, 0.2);
}
.status-disconnected::before {
    content: '';
    display: inline-block;
    width: 10px;
    height: 10px;
    background-color: #f44336;
    border-radius: 50%;
    box-shadow: 0 0 10px #f44336;
}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def check_health():
    try:
        response = requests.get(f"{API_BASE}/health", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False

def poll_job(job_id, success_msg="Job completed successfully!"):
    while True:
        try:
            res = requests.get(f"{API_BASE}/jobs/{job_id}").json()
            status = res.get("status")
            if status == "completed":
                st.success(success_msg)
                return res.get("result")
            elif status == "failed":
                st.error(f"Job failed: {res.get('error', 'Unknown error')}")
                return None
            time.sleep(1)
        except Exception as e:
            st.error(f"Error checking job status: {str(e)}")
            return None

def fetch_list(endpoint):
    try:
        res = requests.get(f"{API_BASE}/{endpoint}")
        if res.status_code == 200:
            return res.json()
        return {}
    except:
        return {}

def download_file_bytes(filename):
    try:
        res = requests.get(f"{API_BASE}/download/{filename}")
        if res.status_code == 200:
            return res.content
        return None
    except:
        return None


def auto_generate_mixtape_info(track_names):
    """Parse track filenames to suggest a mixtape name and genre."""
    if not track_names:
        return "My Mixtape", "House"

    # Clean up track names: remove extensions and common junk
    clean = []
    for t in track_names:
        name = os.path.splitext(t)[0]
        # Remove common patterns like (Official Video), [HD], etc.
        name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
        clean.append(name.strip())

    # Collect all words across tracks for genre detection
    all_words = ' '.join(clean).lower()

    # Genre detection from keywords in filenames
    genre_map = {
        'afro': 'Afro House', 'afrohouse': 'Afro House',
        'deep': 'Deep House', 'deephouse': 'Deep House',
        'tech': 'Tech House', 'techno': 'Techno',
        'progressive': 'Progressive House',
        'melodic': 'Melodic Techno',
        'minimal': 'Minimal',
        'trance': 'Trance',
        'lofi': 'Lo-Fi', 'lo-fi': 'Lo-Fi', 'chill': 'Chill',
        'synthwave': 'Synthwave', 'retro': 'Synthwave',
        'edm': 'EDM', 'dance': 'Dance',
        'house': 'House', 'remix': 'House',
        'hip hop': 'Hip Hop', 'hiphop': 'Hip Hop', 'rap': 'Hip Hop',
        'r&b': 'R&B', 'rnb': 'R&B', 'soul': 'R&B',
        'pop': 'Pop', 'indie': 'Indie',
        'rock': 'Rock', 'punk': 'Punk',
        'jazz': 'Jazz', 'blues': 'Blues',
        'classical': 'Classical',
        'ambient': 'Ambient',
        'drum': 'Drum & Bass', 'dnb': 'Drum & Bass',
        'dubstep': 'Dubstep', 'bass': 'Bass Music',
        'trap': 'Trap',
    }

    detected_genre = 'House'  # default
    for keyword, genre in genre_map.items():
        if keyword in all_words:
            detected_genre = genre
            break

    # Generate mixtape name from month + genre
    month_name = datetime.now().strftime('%B')
    year = datetime.now().strftime('%Y')
    mixtape_name = f"{detected_genre} {month_name} Mix {year}"

    return mixtape_name, detected_genre


# --- Session State ---
if 'tracks' not in st.session_state:
    st.session_state.tracks = []
if 'images' not in st.session_state:
    st.session_state.images = []
if 'auto_name' not in st.session_state:
    st.session_state.auto_name = ''
if 'auto_genre' not in st.session_state:
    st.session_state.auto_genre = ''

# --- Header Section ---
st.markdown('<h1 class="gradient-text">🎵 YT Mixtape Studio</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Create premium lo-fi, synthwave, and chill mixes with AI-generated visuals and descriptions.</p>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🔌 API Connection")
    is_connected = check_health()
    if is_connected:
        st.markdown('<div class="status-connected">Connected to Backend</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-disconnected">Disconnected from Backend</div>', unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 🎧 Upload Tracks")
    audio_files = st.file_uploader(
        "Drag & drop or browse .mp3 / .wav files",
        type=['mp3', 'wav'],
        accept_multiple_files=True,
        key="audio_uploader"
    )
    if audio_files:
        st.caption(f"{len(audio_files)} file(s) selected")
        if st.button("⬆️ Upload Tracks"):
            with st.spinner("Uploading tracks..."):
                files_to_upload = [
                    ("files", (f.name, f.getvalue(), "audio/mpeg"))
                    for f in audio_files
                ]
                try:
                    res = requests.post(f"{API_BASE}/upload-tracks", files=files_to_upload)
                    if res.status_code == 200:
                        uploaded = res.json().get("filenames", [])
                        # Auto-generate mixtape name & genre from uploaded tracks
                        auto_name, auto_genre = auto_generate_mixtape_info(uploaded)
                        st.session_state['auto_name'] = auto_name
                        st.session_state['auto_genre'] = auto_genre
                        st.success(f"✅ {len(uploaded)} track(s) uploaded!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Show current tracks
    tracks_data = fetch_list("list-tracks")
    current_tracks = tracks_data.get("tracks", [])
    if current_tracks:
        st.markdown("**Available Tracks:**")
        for t in current_tracks:
            st.caption(f"🎵 {t}")

        # Auto-generate name/genre if not set yet
        if not st.session_state.get('auto_name'):
            auto_name, auto_genre = auto_generate_mixtape_info(current_tracks)
            st.session_state['auto_name'] = auto_name
            st.session_state['auto_genre'] = auto_genre

        if st.button("🗑️ Clear All Tracks"):
            try:
                requests.delete(f"{API_BASE}/clear-tracks")
                st.session_state['auto_name'] = ''
                st.session_state['auto_genre'] = ''
                st.rerun()
            except Exception as e:
                st.error("Failed to clear tracks")
    else:
        st.caption("No tracks uploaded yet.")

    st.divider()
    
    st.markdown("### 🖼️ Upload Background")
    image_file = st.file_uploader(
        "Select background image",
        type=['jpg', 'jpeg', 'png'],
        key="image_uploader"
    )
    if image_file:
        st.image(image_file, caption=image_file.name, use_container_width=True)
        if st.button("⬆️ Upload Image"):
            with st.spinner("Uploading image..."):
                mime = image_file.type or "image/jpeg"
                try:
                    res = requests.post(
                        f"{API_BASE}/upload-image",
                        files={"file": (image_file.name, image_file.getvalue(), mime)}
                    )
                    if res.status_code == 200:
                        st.success(f"✅ Image uploaded!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Refresh available assets
images_data = fetch_list("list-images")
available_images = images_data.get("images", [])

# --- Main Area Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🎵 Generate Mixtape", "📝 Generate Description", "🎬 Generate Video", "🚀 Full Pipeline"])

with tab1:
    st.markdown("### Audio Mixtape Generation")
    st.markdown("Combine your uploaded tracks into a seamless mixtape with crossfading.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        transition_ms = st.slider("Transition Duration (ms)", min_value=1000, max_value=15000, value=6000, step=500)
    
    if st.button("✨ Generate Mixtape Audio", key="gen_audio"):
        if not current_tracks:
            st.warning("Please upload tracks first!")
        else:
            with st.spinner("Mixing tracks... This might take a minute."):
                try:
                    res = requests.post(f"{API_BASE}/generate-mixtape", json={"transition_ms": transition_ms})
                    if res.status_code == 200:
                        job_id = res.json().get("job_id")
                        result = poll_job(job_id, "Mixtape generated!")
                        if result:
                            st.session_state['last_audio'] = result.get("filename")
                except Exception as e:
                    st.error(f"API Request failed: {str(e)}")
                    
    if 'last_audio' in st.session_state:
        st.divider()
        st.markdown(f"**Result:** `{st.session_state['last_audio']}`")
        audio_bytes = download_file_bytes(st.session_state['last_audio'])
        if audio_bytes:
            st.audio(audio_bytes)
            st.download_button("Download Mixtape", data=audio_bytes, file_name=st.session_state['last_audio'], mime="audio/mpeg")


with tab2:
    st.markdown("### YouTube Description Generation")

    # Show auto-generated suggestion if available
    if st.session_state.get('auto_name'):
        st.info(f"💡 Auto-detected: **{st.session_state['auto_name']}** · {st.session_state['auto_genre']}  —  Edit below if you'd like to change.")

    col1, col2 = st.columns(2)
    with col1:
        mixtape_name = st.text_input(
            "Mixtape Name",
            value=st.session_state.get('auto_name', ''),
            placeholder="e.g., Midnight Vibes",
            key="desc_name"
        )
        genre = st.text_input(
            "Genre / Vibe",
            value=st.session_state.get('auto_genre', ''),
            placeholder="e.g., Synthwave / Chill",
            key="desc_genre"
        )
    with col2:
        hashtags = st.text_area("Custom Hashtags (optional)", placeholder="e.g., #synthwave, #chill, #music")
        
    if st.button("📝 Generate Description", key="gen_desc"):
        if not mixtape_name or not genre:
            st.warning("Mixtape Name and Genre are required.")
        else:
            with st.spinner("Writing description..."):
                try:
                    hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()] if hashtags else None
                    payload = {
                        "mixtape_name": mixtape_name,
                        "genre": genre,
                        "hashtags": hashtag_list
                    }
                    res = requests.post(f"{API_BASE}/generate-description", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state['last_desc'] = data.get("description")
                        st.session_state['last_desc_file'] = data.get("filename")
                        st.success("Description generated!")
                except Exception as e:
                    st.error(f"API Request failed: {str(e)}")

    if 'last_desc' in st.session_state:
        st.divider()
        st.text_area("Generated Description (Copy below)", value=st.session_state['last_desc'], height=300)
        st.download_button("Download as .txt", data=st.session_state['last_desc'], file_name="description.txt", mime="text/plain")


with tab3:
    st.markdown("### Video Generation")
    st.markdown("Combine your mixtape audio with a background image for YouTube.")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_image = st.selectbox("Select Background Image", options=[""] + available_images)
        # Note: In a real app we'd fetch generated audios, using a text input for now or standard placeholder
        audio_target = st.text_input("Audio Filename (from output)", value=st.session_state.get('last_audio', ''), placeholder="e.g., mixtape_20260807_143012_a1b2c3.mp3")
    with col2:
        resolution = st.selectbox("Resolution", options=["720p", "1080p"])
        fps = st.number_input("FPS", min_value=1, max_value=30, value=1, help="Use 1 for static-image videos (smaller file)")
        
    if st.button("🎬 Generate Video", key="gen_vid"):
        if not selected_image or not audio_target:
            st.warning("Please provide an image and an audio filename.")
        else:
            with st.spinner("Rendering video... This will take a while."):
                try:
                    res_map = {"720p": [1280, 720], "1080p": [1920, 1080]}
                    payload = {
                        "image_filename": selected_image,
                        "audio_filename": audio_target,
                        "resolution": res_map.get(resolution, [1280, 720]),
                        "fps": fps
                    }
                    res = requests.post(f"{API_BASE}/generate-video", json=payload)
                    if res.status_code == 200:
                        job_id = res.json().get("job_id")
                        result = poll_job(job_id, "Video rendering complete!")
                        if result:
                            st.session_state['last_video'] = result.get("filename")
                except Exception as e:
                    st.error(f"API Request failed: {str(e)}")
                    
    if 'last_video' in st.session_state:
        st.divider()
        st.markdown(f"**Result:** `{st.session_state['last_video']}`")
        video_bytes = download_file_bytes(st.session_state['last_video'])
        if video_bytes:
            st.video(video_bytes)
            st.download_button("Download Video", data=video_bytes, file_name=st.session_state['last_video'], mime="video/mp4")


with tab4:
    st.markdown("### 🚀 One-Click Pipeline")
    st.markdown("Generate the audio mixtape, YouTube description, and final video all at once.")

    if st.session_state.get('auto_name'):
        st.info(f"💡 Auto-detected: **{st.session_state['auto_name']}** · {st.session_state['auto_genre']}  —  Edit below if you'd like to change.")

    col1, col2 = st.columns(2)
    with col1:
        pipe_name = st.text_input(
            "Mixtape Name",
            value=st.session_state.get('auto_name', ''),
            key="p_name"
        )
        pipe_genre = st.text_input(
            "Genre",
            value=st.session_state.get('auto_genre', ''),
            key="p_genre"
        )
    with col2:
        pipe_image = st.selectbox("Background Image", options=[""] + available_images, key="p_image")
        pipe_transition = st.slider("Transition (ms)", 1000, 15000, 6000, 500, key="p_trans")
        
    if st.button("🚀 Generate Everything", key="gen_all"):
        if not current_tracks:
            st.warning("Please upload tracks first!")
        elif not pipe_name or not pipe_genre or not pipe_image:
            st.warning("Please fill in all details and select an image.")
        else:
            with st.spinner("Running full pipeline... Go grab a coffee! ☕"):
                try:
                    payload = {
                        "mixtape_name": pipe_name,
                        "genre": pipe_genre,
                        "image_filename": pipe_image,
                        "transition_ms": pipe_transition
                    }
                    res = requests.post(f"{API_BASE}/generate-all", json=payload)
                    if res.status_code == 200:
                        job_id = res.json().get("job_id")
                        result = poll_job(job_id, "Pipeline complete! 🎉")
                        if result:
                            st.session_state['pipe_audio'] = result.get("audio_filename")
                            st.session_state['pipe_video'] = result.get("video_filename")
                            st.session_state['pipe_desc_file'] = result.get("description_filename")
                except Exception as e:
                    st.error(f"API Request failed: {str(e)}")
                    
    if 'pipe_video' in st.session_state:
        st.divider()
        st.success("All assets generated successfully!")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### Final Video")
            v_bytes = download_file_bytes(st.session_state['pipe_video'])
            if v_bytes:
                st.video(v_bytes)
                st.download_button("Download Final Video", data=v_bytes, file_name=st.session_state['pipe_video'], mime="video/mp4", key="dl_p_vid")
                
            st.markdown("#### Audio Mix")
            a_bytes = download_file_bytes(st.session_state['pipe_audio'])
            if a_bytes:
                st.audio(a_bytes)
                st.download_button("Download Audio Only", data=a_bytes, file_name=st.session_state['pipe_audio'], mime="audio/mpeg", key="dl_p_aud")
                
        with c2:
            st.markdown("#### Description")
            desc_file = st.session_state.get('pipe_desc_file')
            if desc_file:
                desc_bytes = download_file_bytes(desc_file)
                if desc_bytes:
                    st.text_area("YT Description", value=desc_bytes.decode('utf-8'), height=400, key="p_desc_area")
                    st.download_button("Download Description", data=desc_bytes, file_name=desc_file, mime="text/plain", key="dl_p_desc")

# --- Footer ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.4); font-size: 0.9rem;'>YT Mixtape Studio v1.0.0 • Premium Edition</p>", unsafe_allow_html=True)
