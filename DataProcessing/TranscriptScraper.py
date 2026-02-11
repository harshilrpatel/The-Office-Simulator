"""
Office Transcript Scraper for Forever Dreaming
Scrapes all episodes from https://transcripts.foreverdreaming.org/viewforum.php?f=574
Saves to individual files like 09x26.txt, 09x24-25.txt, etc.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import os
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin


class OfficeTranscriptScraper:
    """Scraper for The Office transcripts from Forever Dreaming"""
    
    def __init__(self, output_dir: str = "transcripts"):
        """
        Initialize the scraper
        
        Args:
            output_dir: Directory to save transcript files
        """
        self.base_url = "https://transcripts.foreverdreaming.org"
        self.forum_url = f"{self.base_url}/viewforum.php?f=574"
        self.output_dir = output_dir
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Session for maintaining cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Stats
        self.total_episodes = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        
        # Episode storage: {season_num: ['Episode Name 1', 'Episode Name 2', ...]}
        self.episodes_by_season = {}
    
    def get_all_episode_links(self) -> Dict[int, List[str]]:
        """
        Get all episode links from all pages with pagination support
        
        Returns:
            Dict mapping season number to list of episode titles (0-indexed)
            Example: {1: ['Pilot', 'Diversity Day', ...], 2: ['The Dundies', ...]}
        """
        print(f"Fetching episode list from: {self.forum_url}")
        print("Scanning all pages for episodes...\n")
        
        all_episodes = []
        page_num = 0
        
        while True:
            # Construct URL for current page
            # phpBB pagination format: ?f=574&start=0, &start=50, &start=100, etc.
            if page_num == 0:
                url = self.forum_url
            else:
                start = page_num * 50  # phpBB typically shows 50 topics per page
                url = f"{self.forum_url}&start={start}"
            
            print(f"Fetching page {page_num + 1}... ({url})")
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all topic links (episode threads)
                topic_links = soup.find_all('a', class_='topictitle')
                
                if not topic_links:
                    print(f"  No more episodes found. Stopping.\n")
                    break
                
                page_episodes = 0
                for link in topic_links:
                    title = link.text.strip()
                    url = link.get('href')
                    
                    # Make absolute URL
                    if url and not url.startswith('http'):
                        url = urljoin(self.base_url, url)
                    
                    # Extract episode info
                    episode_info = self._parse_episode_title(title)
                    
                    if episode_info and url:
                        episode_info['url'] = url
                        all_episodes.append(episode_info)
                        page_episodes += 1
                
                print(f"  Found {page_episodes} episodes on this page")
                
                # Check if there's a next page
                # Look for pagination links
                next_page = soup.find('a', class_='next') or soup.find('li', class_='next')
                
                if not next_page or page_episodes == 0:
                    print(f"  No next page found. Stopping.\n")
                    break
                
                page_num += 1
                
                # Be respectful - add small delay between page requests
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Error fetching page: {e}")
                break
        
        # Organize episodes by season
        episodes_by_season = self._organize_by_season(all_episodes)
        
        # Store in instance variable
        self.episodes_by_season = episodes_by_season
        
        # Calculate total
        self.total_episodes = sum(len(eps) for eps in episodes_by_season.values())
        
        # Print summary
        print("="*70)
        print(f"✓ Found {self.total_episodes} total episodes across {len(episodes_by_season)} seasons")
        print("="*70)
        for season in sorted(episodes_by_season.keys()):
            print(f"  Season {season}: {len(episodes_by_season[season])} episodes")
        print()
        
        return episodes_by_season
    
    def _parse_episode_title(self, title: str) -> Optional[Dict]:
        """
        Parse episode title to extract season, episode number, and name
        
        Examples:
            "9x26 Finale" -> {season: 9, episode_num: 26, name: 'Finale', ...}
            "9x24/25 A.A.R.M." -> {season: 9, episode_num: 24, name: 'A.A.R.M.', ...}
            "1x01 Pilot" -> {season: 1, episode_num: 1, name: 'Pilot', ...}
        
        Args:
            title: Full episode title from forum
            
        Returns:
            Dict with episode info or None
        """
        # Pattern for episode codes like "9x26" or "9x24/25"
        match = re.search(r'(\d+)x(\d+(?:/\d+)?)\s*(.*)', title, re.IGNORECASE)
        
        if match:
            season = int(match.group(1))
            episode_str = match.group(2)
            name = match.group(3).strip()
            
            # Handle double episodes like "24/25"
            if '/' in episode_str:
                episodes = episode_str.split('/')
                episode_num = int(episodes[0])  # Use first episode number
                episode_code = f"{season:02d}x{episodes[0].zfill(2)}-{episodes[1].zfill(2)}"
            else:
                episode_num = int(episode_str)
                episode_code = f"{season:02d}x{episode_str.zfill(2)}"
            
            # Create filename with episode name
            # Sanitize episode name for filename (remove special characters)
            safe_name = self._sanitize_filename(name)
            
            return {
                'season': season,
                'episode_num': episode_num,
                'name': name,
                'full_title': title,
                'episode_code': episode_code,
                'filename': f"{episode_code}_{safe_name}.txt"
            }
        
        return None
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize episode name for use in filename
        
        Examples:
            "Pilot" -> "Pilot"
            "The Dundies" -> "The_Dundies"
            "A.A.R.M." -> "AARM"
            "Dinner Party" -> "Dinner_Party"
        
        Args:
            name: Episode name
            
        Returns:
            Safe filename string
        """
        # Remove or replace special characters
        # Keep alphanumeric, spaces, hyphens
        safe_name = re.sub(r'[^\w\s\-]', '', name)
        
        # Replace spaces with underscores
        safe_name = safe_name.replace(' ', '_')
        
        # Remove multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove leading/trailing underscores
        safe_name = safe_name.strip('_')
        
        # Limit length to avoid filename issues
        if len(safe_name) > 50:
            safe_name = safe_name[:50].rstrip('_')
        
        return safe_name
    
    def _organize_by_season(self, episodes: List[Dict]) -> Dict[int, List[str]]:
        """
        Organize episodes by season with 0-indexed episode names
        
        Args:
            episodes: List of episode dicts
            
        Returns:
            Dict: {season_num: ['Episode 1 Name', 'Episode 2 Name', ...]}
        """
        by_season = {}
        
        # Group episodes by season
        for ep in episodes:
            season = ep['season']
            if season not in by_season:
                by_season[season] = []
            by_season[season].append(ep)
        
        # Sort each season by episode number and extract names (0-indexed)
        result = {}
        for season in sorted(by_season.keys()):
            # Sort by episode number
            sorted_eps = sorted(by_season[season], key=lambda x: x['episode_num'])
            # Extract just the names
            result[season] = [ep['name'] for ep in sorted_eps]
        
        return result
    
    def get_episode_links(self) -> List[Dict]:
        """
        Get all episode links (legacy method for backward compatibility)
        Now calls get_all_episode_links and flattens the result
        
        Returns:
            List of dicts with episode info: {'title', 'url', 'episode_code'}
        """
        episodes_by_season = self.get_all_episode_links()
        
        # Flatten into list format for backward compatibility
        all_episodes = []
        for season_eps in episodes_by_season.values():
            all_episodes.extend(season_eps)
        
        return all_episodes
    
    def _extract_episode_code(self, title: str) -> Optional[str]:
        """
        Extract episode code from title
        
        Examples:
            "9x26 Finale" -> "09x26"
            "9x24/25 A.A.R.M." -> "09x24-25"
            "1x01 Pilot" -> "01x01"
        
        Args:
            title: Episode title
            
        Returns:
            Formatted episode code or None
        """
        # Pattern for episode codes like "9x26" or "9x24/25"
        match = re.search(r'(\d+)x(\d+(?:/\d+)?)', title, re.IGNORECASE)
        
        if match:
            season = match.group(1).zfill(2)  # Pad to 2 digits
            episode = match.group(2)
            
            # Handle double episodes like "24/25"
            if '/' in episode:
                episodes = episode.split('/')
                episodes = [e.zfill(2) for e in episodes]
                episode = '-'.join(episodes)
            else:
                episode = episode.zfill(2)
            
            return f"{season}x{episode}"
        
        return None
    
    def scrape_transcript(self, episode_url: str) -> Optional[str]:
        """
        Scrape transcript text from an episode page
        
        Args:
            episode_url: URL of the episode thread
            
        Returns:
            Transcript text or None if failed
        """
        try:
            response = self.session.get(episode_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the post content
            # Forever Dreaming puts transcripts in the first post's content div
            post_content = soup.find('div', class_='content')
            
            if not post_content:
                # Try alternative selectors
                post_content = soup.find('div', class_='postbody')
            
            if not post_content:
                print("    ⚠ Could not find transcript content")
                return None
            
            # Get text and clean it up
            transcript = post_content.get_text(separator='\n', strip=True)
            
            # Remove forum signatures and other noise
            transcript = self._clean_transcript(transcript)
            
            return transcript
            
        except requests.exceptions.RequestException as e:
            print(f"    ✗ Error fetching transcript: {e}")
            return None
    
    def _clean_transcript(self, text: str) -> str:
        """
        Clean up transcript text
        
        Fixes formatting issues where character names have content on the next line:
        - "Dwight:\n-------" -> "Dwight: -------"
        - "Dwight:\nSome dialogue" -> "Dwight: Some dialogue"
        
        Args:
            text: Raw transcript text
            
        Returns:
            Cleaned transcript
        """
        # Remove common forum artifacts
        # Remove "Top" links
        text = re.sub(r'\s*Top\s*', '', text)
        
        # Fix character names that have content on the next line
        # Split into lines for processing
        lines = text.split('\n')
        cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Check if this line is a character name (ends with colon only, starts with capital)
            # Match patterns like "Dwight:" or "Michael:" with nothing after the colon
            if re.match(r'^[A-Z][a-zA-Z\s\'\.]+:\s*$', line):
                character_name = line.rstrip(':').strip()
                
                # Check if next line exists
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # If next line has content (not empty), merge it with character name
                    if next_line and next_line != '':
                        # Put character name and content on same line
                        cleaned_lines.append(f"{character_name}: {next_line}")
                        i += 2  # Skip the next line since we merged it
                        continue
                
                # If next line is empty or doesn't exist, keep as is (will be removed as empty line)
                cleaned_lines.append(line)
            else:
                # Normal line - keep it
                cleaned_lines.append(line)
            
            i += 1
        
        # Join lines back together
        text = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines (3 or more newlines -> 2 newlines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def save_transcript(self, transcript: str, filename: str) -> bool:
        """
        Save transcript to file
        
        Args:
            transcript: Transcript text
            filename: Output filename
            
        Returns:
            True if successful
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(transcript)
            return True
        except Exception as e:
            print(f"    ✗ Error saving file: {e}")
            return False
    
    def scrape_all_episodes(self, delay: float = 2.0, start_index: int = 0, 
                           max_episodes: Optional[int] = None):
        """
        Scrape all episodes from the forum (with pagination support)
        
        Args:
            delay: Delay between requests in seconds (be respectful!)
            start_index: Index to start from (useful for resuming)
            max_episodes: Maximum number of episodes to scrape (None for all)
        """
        # Get all episodes organized by season (with pagination)
        episodes_by_season = self.get_all_episode_links()
        
        if not episodes_by_season:
            print("No episodes found. Exiting.")
            return
        
        # Flatten into a list for scraping
        all_episodes = []
        for season in sorted(episodes_by_season.keys()):
            # Get the full episode data (not just names)
            # We need to reconstruct this from the stored data
            pass
        
        # Actually, we need to store the full episode data, not just names
        # Let me call the internal method that returns full data
        episodes_full = self._get_all_episodes_full()
        
        if not episodes_full:
            print("No episodes found. Exiting.")
            return
        
        # Apply limits
        if start_index > 0:
            episodes_full = episodes_full[start_index:]
            print(f"Starting from episode {start_index + 1}")
        
        if max_episodes:
            episodes_full = episodes_full[:max_episodes]
            print(f"Limiting to {max_episodes} episodes")
        
        print(f"\nStarting download of {len(episodes_full)} episodes")
        print(f"Delay between requests: {delay} seconds")
        print(f"Output directory: {self.output_dir}")
        print("="*70 + "\n")
        
        for idx, episode in enumerate(episodes_full, start_index + 1):
            print(f"[{idx}/{self.total_episodes}] {episode['episode_code']}: {episode['full_title']}")
            
            # Check if file already exists
            filepath = os.path.join(self.output_dir, episode['filename'])
            if os.path.exists(filepath):
                print("    ✓ Already downloaded (skipping)")
                self.successful_downloads += 1
                continue
            
            # Scrape transcript
            transcript = self.scrape_transcript(episode['url'])
            
            if transcript:
                # Save to file
                if self.save_transcript(transcript, episode['filename']):
                    print(f"    ✓ Saved to: {episode['filename']}")
                    self.successful_downloads += 1
                else:
                    self.failed_downloads += 1
            else:
                print(f"    ✗ Failed to get transcript")
                self.failed_downloads += 1
            
            # Respectful delay between requests
            if idx < len(episodes_full):
                time.sleep(delay)
        
        # Print summary
        self._print_summary()
    
    def _get_all_episodes_full(self) -> List[Dict]:
        """
        Internal method to get full episode data (not just names)
        Used for scraping
        
        Returns:
            List of episode dicts with full info
        """
        all_episodes = []
        page_num = 0
        
        while True:
            # Construct URL for current page
            if page_num == 0:
                url = self.forum_url
            else:
                start = page_num * 50
                url = f"{self.forum_url}&start={start}"
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                topic_links = soup.find_all('a', class_='topictitle')
                
                if not topic_links:
                    break
                
                for link in topic_links:
                    title = link.text.strip()
                    url = link.get('href')
                    
                    if url and not url.startswith('http'):
                        url = urljoin(self.base_url, url)
                    
                    episode_info = self._parse_episode_title(title)
                    
                    if episode_info and url:
                        episode_info['url'] = url
                        all_episodes.append(episode_info)
                
                # Check for next page
                next_page = soup.find('a', class_='next') or soup.find('li', class_='next')
                if not next_page or not topic_links:
                    break
                
                page_num += 1
                time.sleep(0.5)  # Small delay between pages
                
            except requests.exceptions.RequestException:
                break
        
        return all_episodes
    
    def get_episodes_dict(self) -> Dict[int, List[str]]:
        """
        Get episodes organized by season
        
        Returns:
            Dict: {season_num: ['Episode Name 1', 'Episode Name 2', ...]}
                  Episodes are 0-indexed within each season
        """
        if not self.episodes_by_season:
            self.get_all_episode_links()
        
        return self.episodes_by_season
    
    def print_episodes_dict(self):
        """
        Print the episodes dictionary in a readable format
        """
        episodes_dict = self.get_episodes_dict()
        
        print("\n" + "="*70)
        print("EPISODES BY SEASON (0-indexed)")
        print("="*70 + "\n")
        
        for season in sorted(episodes_dict.keys()):
            print(f"Season {season}:")
            print("{")
            for idx, episode_name in enumerate(episodes_dict[season]):
                print(f"  {idx}: '{episode_name}',")
            print("}")
            print()
        
        print(f"Total: {sum(len(eps) for eps in episodes_dict.values())} episodes across {len(episodes_dict)} seasons")
    
    def save_episodes_dict(self, filename: str = "episodes_dict.json"):
        """
        Save the episodes dictionary to a JSON file
        
        Args:
            filename: Output filename
        """
        import json
        
        episodes_dict = self.get_episodes_dict()
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(episodes_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Episodes dictionary saved to: {filepath}")
    
    def _print_summary(self):
        """Print download summary"""
        print("\n" + "="*70)
        print("DOWNLOAD SUMMARY")
        print("="*70)
        print(f"Total episodes found: {self.total_episodes}")
        print(f"Successfully downloaded: {self.successful_downloads}")
        print(f"Failed: {self.failed_downloads}")
        print(f"Output directory: {self.output_dir}")
        print("\n✓ Scraping complete!")
    
    def resume_scraping(self, delay: float = 2.0):
        """
        Resume scraping from where it left off
        Checks which files already exist and skips them
        
        Args:
            delay: Delay between requests in seconds
        """
        episodes = self.get_episode_links()
        
        # Find first missing episode
        start_index = 0
        for idx, episode in enumerate(episodes):
            filepath = os.path.join(self.output_dir, episode['filename'])
            if not os.path.exists(filepath):
                start_index = idx
                break
        
        if start_index == 0 and os.path.exists(
            os.path.join(self.output_dir, episodes[0]['filename'])
        ):
            print("✓ All episodes already downloaded!")
            return
        
        print(f"Resuming from episode {start_index + 1}")
        self.scrape_all_episodes(delay=delay, start_index=start_index)


def main():
    """Main execution"""
    print("="*70)
    print(" "*15 + "THE OFFICE TRANSCRIPT SCRAPER")
    print(" "*10 + "Forever Dreaming - Complete Series")
    print("="*70 + "\n")
    
    print("IMPORTANT NOTES:")
    print("• This will download ALL episodes (~200 transcripts)")
    print("• Please be respectful - we add 2-second delays between requests")
    print("• This may take 10-15 minutes to complete")
    print("• You can stop and resume anytime (Ctrl+C)")
    print("• Files are saved as you go, so progress is not lost")
    print()
    
    # Get user confirmation
    response = input("Ready to start downloading? (y/n): ")
    
    if response.lower() != 'y':
        print("\nExiting. Run again when ready!")
        return
    
    print()
    
    # Initialize scraper
    scraper = OfficeTranscriptScraper(output_dir="transcripts")
    
    try:
        # Start scraping with 2-second delay
        scraper.scrape_all_episodes(delay=2.0)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        print(f"Progress saved! Downloaded: {scraper.successful_downloads} episodes")
        print("\nTo resume, run:")
        print("  scraper = OfficeTranscriptScraper()")
        print("  scraper.resume_scraping()")
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print(f"Progress saved! Downloaded: {scraper.successful_downloads} episodes")


if __name__ == "__main__":
    main()