import os
import json
import yt_dlp
from datetime import datetime, timedelta

#config
CHANNEL_UPLOADS_PLAYLIST = 'https://www.youtube.com/playlist?list=channelurl' #YouTube playlist that includes all videos uploaded by the channel (make sure  its in encrypted format such as US2i283yh14nbjut5 rather than a user created URl
DOWNLOAD_PATH = r'C:\Users\conor\Videos\videodownloader'#local folder to store downloaded videos
DOWNLOADED_FILE = os.path.join(DOWNLOAD_PATH, 'downloaded_videos.json') #file to store list of already downloaded video IDs
LOG_FILE = os.path.join(DOWNLOAD_PATH, 'videodownloader_log.txt') #log file path

# YouTube API limits
MAX_DURATION = 15 * 60 #maximum video duration (in seconds) = 15 minutes
MAX_AGE_HOURS = 48 #only download videos uploaded in the last 48 hours
OLD_VIDEO_STREAK_LIMIT = 3 #stop scanning after this many old videos in a row

# -------- LOGGING FUNCTION -------- #

def log(message: str):
    # Write a timestamped message to both console and log file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_message + '\n')

# -------- SETUP -------- #

#make sure output folder exists
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

#load downloaded video IDs from file, or create a new set
if os.path.exists(DOWNLOADED_FILE):
    with open(DOWNLOADED_FILE, 'r') as f:
        downloaded = set(json.load(f))
else:
    downloaded = set()

#compute 48-hour cutoff timestamp
cutoff_datetime = datetime.utcnow() - timedelta(hours=MAX_AGE_HOURS)

#VIDEO LIST FETCH

log("📡 Fetching video list from uploads playlist...")
with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
    result = ydl.extract_info(CHANNEL_UPLOADS_PLAYLIST, download=False)
    videos = result.get('entries', [])

log(f"🔍 Found {len(videos)} videos. Scanning for recent short uploads...")

#counter for early exit if too many old videos in a row
old_streak = 0

# -------- MAIN LOOP -------- #

for video in videos:
    video_id = video.get('id')

    #skip already downloaded videos
    if video_id in downloaded:
        continue

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        #fetch full metadata
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            upload_date_str = info.get('upload_date')  # format: YYYYMMDD
            upload_datetime = datetime.strptime(upload_date_str, '%Y%m%d')
    except Exception as e:
        log(f"❌ Error fetching info for {video_url}: {e}")
        continue

    #check upload age
    if upload_datetime < cutoff_datetime:
        log(f"⏭️ Skipping (too old): {title} (uploaded {upload_datetime.strftime('%Y-%m-%d')})")
        old_streak += 1
        if old_streak >= OLD_VIDEO_STREAK_LIMIT:
            log(f"🛑 Reached {OLD_VIDEO_STREAK_LIMIT} old videos in a row. Stopping scan early.")
            break
        continue
    else:
        old_streak = 0  #reset streak if video is recent

    #skip long videos
    if duration > MAX_DURATION:
        log(f"⏭️ Skipping (too long): {title} ({duration // 60} min)")
        continue

    # -------- DOWNLOAD -------- #
    log(f"⬇️ Downloading: {title}")
    try:
        ydl_opts = {
            #progressive MP4 stream (no ffmpeg needed)
            'format': 'best[ext=mp4][protocol^=http][vcodec^=avc1]',
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title).200s.%(ext)s'),
            'quiet': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        downloaded.add(video_id)  #save video ID
    except Exception as e:
        log(f"❌ Failed to download {title}: {e}")


#save the updated set of downloaded video IDs
with open(DOWNLOADED_FILE, 'w') as f:
    json.dump(list(downloaded), f)

log("✅ Done! All recent short uploads downloaded.\n")
