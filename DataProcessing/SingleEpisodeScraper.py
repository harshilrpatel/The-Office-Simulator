"""
Single Episode Downloader
Downloads a transcript from a specific Forever Dreaming URL

Usage:
    python download_single_episode.py "https://transcripts.foreverdreaming.org/viewtopic.php?t=12345"
"""

import sys
import os
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict


class SingleEpisodeDownloader:
    """Download a single episode transcript from a URL"""
    
    def __init__(self, output_dir: str = "transcripts"):
        """
        Initialize downloader
        
        Args:
            output_dir: Directory to save transcript file
        """
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def extract_episode_info_from_url(self, url: str) -> Optional[Dict]:
        """
        Extract episode information by fetching the page
        
        Args:
            url: URL of the episode page
            
        Returns:
            Dict with episode info or None
        """
        try:
            print(f"Fetching page: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get page title (usually contains episode info)
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.text.strip()
                print(f"Page title: {page_title}")
                
                # Try to extract episode info from title
                # Format: "9x26 Finale" or similar
                match = re.search(r'(\d+)x(\d+(?:/\d+)?)\s*(.*?)(?:\s*[-•]\s*|$)', page_title)
                
                if match:
                    return self._parse_episode_from_match(match)
            
            # Alternative: Look for topic title in the page
            topic_title = soup.find('h1', class_='topic-title') or soup.find('h2', class_='topic-title')
            if topic_title:
                title_text = topic_title.text.strip()
                print(f"Topic title: {title_text}")
                
                match = re.search(r'(\d+)x(\d+(?:/\d+)?)\s*(.*)', title_text)
                if match:
                    return self._parse_episode_from_match(match)
            
            # Manual input fallback
            print("\n⚠ Could not auto-detect episode info from page")
            return self._get_episode_info_manually()
            
        except Exception as e:
            print(f"✗ Error fetching page: {e}")
            return self._get_episode_info_manually()
    
    def _parse_episode_from_match(self, match) -> Dict:
        """Parse episode info from regex match"""
        season = int(match.group(1))
        episode_str = match.group(2)
        name = match.group(3).strip() if len(match.groups()) >= 3 else ""
        
        # Handle double episodes like "24/25"
        if '/' in episode_str:
            episodes = episode_str.split('/')
            episode_num = int(episodes[0])
            episode_code = f"{season:02d}x{episodes[0].zfill(2)}-{episodes[1].zfill(2)}"
        else:
            episode_num = int(episode_str)
            episode_code = f"{season:02d}x{episode_str.zfill(2)}"
        
        return {
            'season': season,
            'episode_num': episode_num,
            'name': name,
            'episode_code': episode_code
        }
    
    def _get_episode_info_manually(self) -> Optional[Dict]:
        """Get episode info from user input"""
        print("\n" + "="*70)
        print("MANUAL EPISODE INFO ENTRY")
        print("="*70)
        
        try:
            season = int(input("Enter season number (1-9): "))
            episode = int(input("Enter episode number: "))
            name = input("Enter episode name (or press Enter to skip): ").strip()
            
            episode_code = f"{season:02d}x{episode:02d}"
            
            return {
                'season': season,
                'episode_num': episode,
                'name': name,
                'episode_code': episode_code
            }
        except (ValueError, KeyboardInterrupt):
            print("\n✗ Invalid input")
            return None
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize episode name for filename
        
        Args:
            name: Episode name
            
        Returns:
            Safe filename string
        """
        # Remove special characters
        safe_name = re.sub(r'[^\w\s\-]', '', name)
        
        # Replace spaces with underscores
        safe_name = safe_name.replace(' ', '_')
        
        # Remove multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove leading/trailing underscores
        safe_name = safe_name.strip('_')
        
        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50].rstrip('_')
        
        return safe_name
    
    def download_transcript(self, url: str) -> bool:
        """
        Download transcript from URL and save to file
        
        Args:
            url: URL of the episode page
            
        Returns:
            True if successful, False otherwise
        """
        # Validate URL
        if 'foreverdreaming.org' not in url:
            print("⚠ Warning: This doesn't look like a Forever Dreaming URL")
            proceed = input("Continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                return False
        
        # Get episode info
        episode_info = self.extract_episode_info_from_url(url)
        
        if not episode_info:
            print("✗ Could not determine episode information")
            return False
        
        # Confirm with user
        print("\n" + "="*70)
        print("EPISODE INFORMATION")
        print("="*70)
        print(f"Season: {episode_info['season']}")
        print(f"Episode: {episode_info['episode_num']}")
        print(f"Name: {episode_info['name'] or '(not specified)'}")
        print(f"Code: {episode_info['episode_code']}")
        
        # Generate filename
        if episode_info['name']:
            safe_name = self._sanitize_filename(episode_info['name'])
            filename = f"{episode_info['episode_code']}_{safe_name}.txt"
        else:
            filename = f"{episode_info['episode_code']}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        print(f"\nWill save to: {filepath}")
        
        # Check if file exists
        if os.path.exists(filepath):
            print(f"\n⚠ File already exists!")
            overwrite = input("Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                print("Cancelled.")
                return False
        
        print("\nDownloading transcript...")
        
        # Fetch and parse transcript
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find transcript content
            # Forever Dreaming uses .content or .postbody classes
            post_content = soup.find('div', class_='content') or soup.find('div', class_='postbody')
            
            if not post_content:
                print("✗ Could not find transcript content on page")
                print("The page structure may have changed.")
                return False
            
            # Extract text
            transcript = post_content.get_text(separator='\n', strip=True)
            
            # Clean up
            transcript = self._clean_transcript(transcript)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            print(f"\n✓ Successfully saved transcript to: {filename}")
            print(f"   Size: {len(transcript)} characters")
            print(f"   Lines: {len(transcript.split(chr(10)))} lines")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"\n✗ Error downloading transcript: {e}")
            return False
        except Exception as e:
            print(f"\n✗ Error processing transcript: {e}")
            return False
    
    def _clean_transcript(self, text: str) -> str:
        """
        Basic cleaning of transcript text
        
        Args:
            text: Raw transcript text
            
        Returns:
            Cleaned text
        """
        # Remove "Top" links
        text = re.sub(r'\s*Top\s*', '', text)
        
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()


def main():
    """Main execution"""
    print("="*70)
    print(" "*15 + "SINGLE EPISODE DOWNLOADER")
    print(" "*10 + "Forever Dreaming Transcript Downloader")
    print("="*70 + "\n")
    
    # Get URL from command line or user input
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Enter the URL of the episode page:")
        print("Example: https://transcripts.foreverdreaming.org/viewtopic.php?t=12345")
        print()
        url = input("URL: ").strip()
    
    if not url:
        print("✗ No URL provided")
        return
    
    # Initialize downloader
    downloader = SingleEpisodeDownloader(output_dir="transcripts")
    
    # Download
    success = downloader.download_transcript(url)
    
    if success:
        print("\n" + "="*70)
        print("✓ DOWNLOAD COMPLETE!")
        print("="*70)
        print("\nNext steps:")
        print("1. Check the transcript file in transcripts/ directory")
        print("2. Run transcript_to_rag.py to process it for RAG")
        print("3. Or download more episodes with this script")
    else:
        print("\n" + "="*70)
        print("✗ DOWNLOAD FAILED")
        print("="*70)
        print("\nTroubleshooting:")
        print("1. Check the URL is correct")
        print("2. Check your internet connection")
        print("3. The site may be blocking automated requests")
        print("4. Try using manual_download_helper.py instead")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")