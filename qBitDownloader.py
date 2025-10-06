#!/usr/bin/env python3
"""
qBittorrent Unofficial Search Plugin Downloader
"""
import os
import re
import requests
from urllib.parse import urljoin
from pathlib import Path

#config
WIKI_URL = "https://github.com/qbittorrent/search-plugins/wiki/Unofficial-search-plugins"
OUTPUT_DIR = "qbittorrent_plugins" #save plugins here

def download_file(url, dest_path): 
    """Download a file from URL to destination path"""
    try:
        response = requests.get(url, timeout=30) # Fetch the file
        response.raise_for_status()# Raise error for bad status
         # Save to destination
        with open(dest_path, 'wb') as f: # binary write
            f.write(response.content) # Write content to file
        return True
    except Exception as e:
        print(f"  ✗ Failed to download {url}: {e}")
        return False

def extract_plugin_urls(html_content):
    """Extract all .py plugin URLs from HTML content"""
    # Look for GitHub raw URLs that point to .py files
    patterns = [
        r'https://raw\.githubusercontent\.com/[^\s"\)<]+\.py',
        r'https://github\.com/[^\s"\)<]+/raw/[^\s"\)<]+\.py',
        r'https://gist\.githubusercontent\.com/[^\s"\)<]+\.py',
    ]
    
    urls = [] # Store found URLs
    for pattern in patterns:
        found = re.findall(pattern, html_content) # Find all matches
        urls.extend(found) # Add to list
    
    # Remove duplicates while preserving order
    seen = set() # Track seen URLs
    unique_urls = [] # Store unique URLs
    for url in urls: 
        if url not in seen: # Check if URL is unique
            seen.add(url)
            unique_urls.append(url) # Store unique URLs
    
    return unique_urls

def main(): 
    print("qBittorrent Unofficial Search Plugin Downloader")
    print("=" * 30)
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(exist_ok=True) # Make sure output dir exists
    print(f"\n📁 Output directory: {os.path.abspath(OUTPUT_DIR)}") # Show absolute path locally
    
    # Fetch wiki page
    print(f"\n📥 Fetching wiki page...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(WIKI_URL, headers=headers, timeout=30) 
        response.raise_for_status() # Raise error for bad status
        html_content = response.text # Get page content
    except Exception as e:
        print(f"✗ Failed to fetch wiki page: {e}")
        return
    
    # Extract plugin URLs
    print("\n🔍 Extracting plugin URLs...")
    plugin_urls = extract_plugin_urls(html_content) # Get list of plugin URLs
    
    if not plugin_urls:
        print("✗ No plugin URLs found in the wiki page")
        return
    
    print(f"✓ Found {len(plugin_urls)} plugin(s)") # Show number of found plugins
    
    # Download plugins
    print(f"\n⬇️  Downloading plugins...")
    success_count = 0   # count successful downloads
    
    for url in plugin_urls:
        filename = url.split('/')[-1] # Get filename from URL
        dest_path = os.path.join(OUTPUT_DIR, filename) # Destination path locally
        
        print(f"\n  → {filename}") # Show filename
        if download_file(url, dest_path):   # Download the file
            print(f"    ✓ Downloaded successfully")
            success_count += 1  # Increment success count
    
    # Summary
    print("\n" + "=" * 30)
    print(f"✓ Successfully downloaded {success_count}/{len(plugin_urls)} plugins")
    print(f"\n📂 Plugins saved to: {os.path.abspath(OUTPUT_DIR)}")

    # Install instructions
    print("\n🔧 To install in qBittorrent:")
    print("   1. Open qBittorrent")
    print("   2. Go to Search tab")
    print("   3. Click 'Search plugins...' button")
    print("   4. Click 'Install a new one' → 'Local file'")
    print(f"   5. Select plugins from: {os.path.abspath(OUTPUT_DIR)}")  

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")