#!/usr/bin/env python3
"""
YouTube Playlist Downloader
Downloads videos from a YouTube playlist with the following conditions:
- Skips videos longer than 30 minutes
- Skips already downloaded files
- Downloads to a 'downloads' folder
- Shows real-time progress while fetching playlist info
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import time

def install_yt_dlp():
    """Install yt-dlp if not already installed"""
    try:
        import yt_dlp
        return True
    except ImportError:
        print("yt-dlp not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            import yt_dlp
            return True
        except subprocess.CalledProcessError:
            print("Failed to install yt-dlp. Please install it manually: pip install yt-dlp")
            return False

def get_playlist_urls_fast(playlist_url):
    """Get video URLs from playlist quickly using flat extraction"""
    try:
        import yt_dlp
        
        print("Getting video list from playlist (this may take a moment)...")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Fast extraction - just URLs and titles
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            if 'entries' in playlist_info:
                video_list = []
                for entry in playlist_info['entries']:
                    if entry:  # Skip None entries
                        video_list.append({
                            'id': entry.get('id'),
                            'title': entry.get('title', 'Unknown Title'),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                        })
                return video_list
            else:
                print("No videos found in playlist")
                return []
                
    except Exception as e:
        print(f"Error extracting playlist: {e}")
        return []

def check_available_formats(video_url, show_formats=False):
    """Check what video formats are available and return the best quality info"""
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': show_formats,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if show_formats and 'formats' in info:
                print("\nAvailable formats:")
                for fmt in info['formats'][-10:]:  # Show last 10 (usually highest quality)
                    if fmt.get('height'):
                        print(f"  {fmt['format_id']}: {fmt.get('height', '?')}p - {fmt.get('ext', '?')} - {fmt.get('filesize_approx', 0)/1024/1024:.1f}MB")
            
            # Get the best video quality available
            best_height = 0
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('height') and fmt.get('height') > best_height:
                        best_height = fmt.get('height')
            
            return best_height, info.get('duration')
            
    except Exception as e:
        if show_formats:
            print(f"Could not get format info: {e}")
        return None, None

def get_video_duration(video_url):
    """Get video duration efficiently"""
    _, duration = check_available_formats(video_url, show_formats=False)
    return duration

def is_already_downloaded(video_title, download_dir):
    """Check if video is already downloaded by checking for similar filenames"""
    if not os.path.exists(download_dir):
        return False, None
        
    # Clean the title for filename comparison
    clean_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
    
    # Check for various possible filename formats
    for file in os.listdir(download_dir):
        if file.endswith(('.mp4', '.mkv', '.webm', '.m4a', '.mp3')):
            file_stem = os.path.splitext(file)[0]
            # Simple check if the clean title is in the filename
            if len(clean_title) > 10 and clean_title.lower() in file_stem.lower():
                return True, file
            elif len(file_stem) > 10 and file_stem.lower() in clean_title.lower():
                return True, file
    return False, None

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds is None:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    else:
        return f"{minutes}m {secs}s"

def download_video(video_url, download_dir, video_title, quality_format):
    """Download a single video"""
    try:
        import yt_dlp
        
        # Configure download options for maximum quality
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'format': quality_format,
            'ignoreerrors': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',  # Ensure final output is MP4
            'writesubtitles': False,  # Set to True if you want subtitles
            'writeautomaticsub': False,  # Set to True for auto-generated subs
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            return True
            
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False

def main():
    # CONFIGURATION - Modify these settings as needed
    playlist_url = "YOUTUBE PLAYLIST .url" #change relative to URL
    download_dir = "downloads"
    max_duration = 30 * 60  # 30 minutes in seconds
    
    quality_format = 'bestvideo+bestaudio/best'        # HIGHEST QUALITY (recommended for max quality)
    
    print(f"Quality setting: {quality_format} (this downloads separate video+audio streams for maximum quality)")
    
    print(f"Quality setting: {quality_format}")
    
    # Install yt-dlp if needed
    print("Checking dependencies...")
    if not install_yt_dlp():
        return
    
    # Create download directory
    Path(download_dir).mkdir(exist_ok=True)
    print(f"Download directory: {os.path.abspath(download_dir)}")
    
    # Get video list quickly first
    print("\n" + "="*60)
    video_list = get_playlist_urls_fast(playlist_url)
    
    if not video_list:
        print("No videos found in playlist or error occurred.")
        return
    
    print(f"Found {len(video_list)} videos in playlist")
    print("="*60)
    
    downloaded_count = 0
    skipped_duration = 0
    skipped_exists = 0
    errors = 0
    
    for i, video in enumerate(video_list, 1):
        title = video['title']
        url = video['url']
        
        print(f"\n[{i}/{len(video_list)}] Processing: {title}")
        
        # Check if already downloaded first (fastest check)
        already_exists, existing_file = is_already_downloaded(title, download_dir)
        if already_exists:
            print(f"⏭️  SKIPPED: Already downloaded as '{existing_file}'")
            skipped_exists += 1
            continue
        
        # Get duration and quality info
        print("   📏 Checking video info...")
        best_quality, duration = check_available_formats(url, show_formats=False)
        duration_str = format_duration(duration)
        quality_str = f"{best_quality}p" if best_quality else "Unknown"
        print(f"   Duration: {duration_str} | Best available: {quality_str}")
        
        # Check if video is too long
        if duration and duration > max_duration:
            print(f"⏭️  SKIPPED: Video is longer than 30 minutes ({duration_str})")
            skipped_duration += 1
            continue
        
        # Download the video
        print("📥 Downloading...")
        if download_video(url, download_dir, title, quality_format):
            print("✅ Download completed!")
            downloaded_count += 1
        else:
            print("❌ Download failed!")
            errors += 1
        
        # Small delay to prevent overwhelming the API
        time.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY:")
    print(f"Total videos in playlist: {len(video_list)}")
    print(f"Successfully downloaded: {downloaded_count}")
    print(f"Skipped (too long): {skipped_duration}")
    print(f"Skipped (already exists): {skipped_exists}")
    print(f"Errors: {errors}")
    print(f"Downloads saved to: {os.path.abspath(download_dir)}")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("You can try running the script again.")

