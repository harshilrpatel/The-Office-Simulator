"""
Alternative transcript scaper using transcripts.foreverdreaming.org
This source has better structure transacripts
"""


import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Dialogue:
    """Represents a single line of dialogue"""
    character : str
    text: str
    episode_title: str
    season: int
    episode_number: int
    scene_context: str = ""
    timestamp: str = "" #Some source includes timestamps

    def to_dict(self):
        return asdict(self)
    
class AlternativeTranscriptScraper:
    """
    Alternative scraper with support for multiple transcripts source
    """

    def __init__(self, source: str = "foreverdreaming"):
        """
        Initialize scraper

        Args:
            source: Which transcripts source to use
                -'foreverdreaming': transcripts.foreverdreaming.org
                -'officequotes': officequotes.net (original)
        """
        self.source = source
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Window NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        #Episode metadata
        self.episode_metadata = self._load_episode_metadata()
    
    def _load_episode_metadata(self) -> Dict:
        """
        Load episode metadata (titles, air dates, etc.)
        """
        return {
            1: [
                "Pilot", "Diversity Day", "Health Care", "The Alliance",
                "Basketball", "Hot Girl"
            ],
            2: [
                "The Dundies", "Sexual Harassment", "Office Olympics", "The Fire",
                "Halloween", "The Fight", "The Client", "Performance Review",
                "Email Surveillance", "Christmas Party", "Booze Cruise",
                "The Injury", "The Secret", "The Carpet", "Boys and Girls",
                "Valentine's Day", "Dwight's Speech", "Take Your Daughter to Work Day",
                "Michael's Birthday", "Drug Testing", "Conflict Resolution",
                "Casino Night"
            ],
        }

    def parse_simple_transcript(self, text:str, episode_title:str, season:int, episode_num:int) -> List[Dialogue]:
        """
        Parse a simple transcript format where dialogue is:
        CHARACTER: dialogue text

        This works for most transcript sources
        """
        dialogues = []
        lines = text.split("\n")
        current_scene = "Scene 1"
        scene_counter = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            #Scene makers (various formats)
            if any(marker in line.lower() for marker in ['[scene:', 'scene', 'int.', 'ext']):
                current_scene = line.strip('[]')
                scene_counter += 1
                continue

            #Stage directions (usually in brackets or parentheses)
            if line.startswith('[') and line.endswith(']'):
                continue
            if line.startswith('(') and line.endswith(')'):
                continue
                
            #Try to match dialogue format : "CHARACTER: text"
            #Support various formats
            match = re.match(r'^([A-Z][A-Za-z\s\'\-\.]+?):\s*(.+)$', line)

            if match:
                character = match.group(1).strip()
                text = match.group(2).strip()

                #Clean up the text (remove stage directions in parantheses)
                text = re.sub(r'\([^)]*\)', '', text).strip()

                if text: #Only add if there's actual dialogue
                    dialogue = Dialogue(
                        character=self._normalize_character_name(character),
                        text = text,
                        episode_title = episode_title,
                        season = season,
                        episode_number=episode_num,
                        scene_context=current_scene
                    )
                    dialogues.append(dialogue)
        return dialogues
    
    def _normalize_character_name(self, name:str)-> str:
        """ Normalize character names to standard formats """
        name = name.strip()

        #Remove common suffixes
        name = re.sub(r'\s*\(.*\)', '', name)  # Remove (V.O.), (O.S.), etc.

        #Title case
        name = name.title()

        # Character name mappings
        mappings = {
            'Dwight K. Schrute': 'Dwight',
            'Dwight K Schrute': 'Dwight',
            'Dwight Schrute': 'Dwight',
            'Dwight': 'Dwight',
            'Jim Halpert': 'Jim',
            'Jim': 'Jim',
            'Pam Beesly': 'Pam',
            'Pam Halpert': 'Pam',
            'Pam': 'Pam',
            'Pamela': 'Pam',
            'Michael Scott': 'Michael',
            'Michael': 'Michael',
            'Mike': 'Michael',
            'Angela Martin': 'Angela',
            'Angela': 'Angela',
            'Kevin Malone': 'Kevin',
            'Kevin': 'Kevin',
            'Oscar Martinez': 'Oscar',
            'Oscar': 'Oscar',
            'Stanley Hudson': 'Stanley',
            'Stanley': 'Stanley',
            'Phyllis Vance': 'Phyllis',
            'Phyllis Lapin': 'Phyllis',
            'Phyllis': 'Phyllis',
            'Ryan Howard': 'Ryan',
            'Ryan': 'Ryan',
            'Kelly Kapoor': 'Kelly',
            'Kelly': 'Kelly',
            'Toby Flenderson': 'Toby',
            'Toby': 'Toby',
            'Creed Bratton': 'Creed',
            'Creed': 'Creed',
            'Meredith Palmer': 'Meredith',
            'Meredith': 'Meredith',
            'Erin Hannon': 'Erin',
            'Erin': 'Erin',
            'Andy Bernard': 'Andy',
            'Andy': 'Andy',
            'Darryl Philbin': 'Darryl',
            'Darryl': 'Darryl',
            'Jan Levinson': 'Jan',
            'Jan': 'Jan',
            'David Wallace': 'David',
            'Roy Anderson': 'Roy',
            'Roy': 'Roy',
        }
        
        return mappings.get(name, name)

    def load_from_file(self, filepath:str, episode_title:str, season:int, episode_num:int) -> List[Dialogue]:
        """
        Load and parse transcript from a local file
        Useful if you've already downloaded transcripts

        Args:
            filepath: Path to the transcript file
            episode_title: Episode title
            season: Season number
            episode_num: Episode number

        Returns:
            List of Dialogue objects
        """
        print(f"Loading transcript from {filepath}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dialogues = self.parse_simple_transcript(content, episode_title, season, episode_num)

            print(f" -> Parsed {len(dialogues)} dialogue lines")
            return dialogues
        
        except Exception as e:
            print(f"Error loading file {filepath} : {e}")
            return []
    
    def save_to_json(self, dialogues:List[Dialogue], filename: str):
        """
        Save dialogues to JSON file
        """
        data = [d.to_dict() for d in dialogues]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f" Saved {len(dialogues)} dialogues to {filename}")
    
    def save_to_csv(self, dialogues:List[Dialogue], filename: str):
        """
        Save dialogues to CSV file using pandas
        """
        data = [d.to_dict() for d in dialogues]
        df = pd.DataFrame(data)

        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(dialogues)} dialogues to {filename}")
    
    def get_statistics(self, dialogues: List[Dialogue]) -> Dict:
        """
        Get comprehensive stats about the dataset
        """

        df = pd.DataFrame([d.to_dict() for d in dialogues])
        stats = {
            'total_dialogues': len(dialogues),
            'unique_characters': df['character'].nunique(),
            'seasons': sorted(df['season'].unique().tolist()),
            'episodes_count': df.groupby('season')['episode_number'].nunique().to_dict(),
            'character_stats': df.groupby('character').agg({
                'text': 'count',
                'episode_title': 'nunique'
            }).rename(columns={
                'text': 'line_count',
                'episode_title': 'episodes_appeared'
            }).sort_values('line_count', ascending=False).to_dict('index'),
            'top_characters': df['character'].value_counts().head(15).to_dict()
        }
        
        return stats

    def print_statistics(self, stats: Dict):
        """Pretty print statistics"""
        print("\n" + "="*70)
        print("DATASET STATISTICS")
        print("="*70)
        print(f"Total Dialogue Lines: {stats['total_dialogues']:,}")
        print(f"Unique Characters: {stats['unique_characters']}")
        print(f"Seasons: {', '.join(map(str, stats['seasons']))}")
        print(f"\nEpisodes per season: {stats['episodes_count']}")
        
        print("\n" + "-"*70)
        print("TOP 15 CHARACTERS BY LINE COUNT")
        print("-"*70)
        print(f"{'Rank':<5} {'Character':<20} {'Lines':<10} {'Episodes'}")
        print("-"*70)
        
        for idx, (char, count) in enumerate(stats['top_characters'].items(), 1):
            episodes = stats['character_stats'][char]['episodes_appeared']
            print(f"{idx:<5} {char:<20} {count:<10} {episodes}")
    

def create_sample_transcript():
    """Create a sample transcript file for testing"""
    sample_text = """[SCENE: Dunder Mifflin Office - Morning]

Michael: Good morning everyone! Who's ready for another great day at Dunder Mifflin?

Jim: (smiling at camera) Another day in paradise.

Pam: Morning Michael. You seem extra chipper today.

Michael: That's because I am! I have an announcement to make. Everyone, conference room, five minutes!

Dwight: Michael, I've already prepared the conference room. I took the liberty of arranging the chairs in order of seniority.

Jim: Of course you did.

[SCENE: Conference Room]

Michael: Alright everyone, settle down. I have some very exciting news. We are getting new computers!

Oscar: Finally. These computers are from the 90s.

Michael: Yes, Oscar, I know you're very tech-savvy. But let me finish.

Angela: Can we make this quick? Some of us have actual work to do.

Michael: Angela, this IS work. This is very important work stuff.

Kevin: New computers! Nice!

Stanley: I don't care about new computers. I just want to do my crossword in peace.

Michael: Stanley, your lack of enthusiasm is noted. Moving on...
"""
    with open('Transcripts/sample_transcript.txt', 'w', encoding='utf-8') as f:
        f.write(sample_text)
    
    print("Created sample transcript at: Transcripts/sample_transcript.txt")

def main():
    """ Demo the alternative scraper """
    print("Alternatice Transcript Scraper Demo")
    print("="*70 + "\n")

    #Create a sample transcript
    create_sample_transcript()

    # Initialize scraper
    scraper = AlternativeTranscriptScraper()
    
    # Load the sample transcript
    dialogues = scraper.load_from_file(
        'Transcripts/sample_transcript.txt',
        episode_title='The Sample Episode',
        season=1,
        episode_num=1
    )
    
    if dialogues:
        print(f"\n✓ Successfully parsed {len(dialogues)} dialogue lines\n")
        
        # Show first few dialogues
        print("Sample Dialogues:")
        print("-"*70)
        for d in dialogues[:5]:
            print(f"{d.character}: {d.text}")
        
        # Save to JSON
        scraper.save_to_json(dialogues, 'Transcripts/sample_output.json')
        
        # Save to CSV
        scraper.save_to_csv(dialogues, 'Transcripts/sample_output.csv')
        
        # Get and print statistics
        stats = scraper.get_statistics(dialogues)
        scraper.print_statistics(stats)
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("1. Download actual transcripts from sources like:")
    print("   - https://transcripts.foreverdreaming.org/viewforum.php?f=574")
    print("   - https://www.officequotes.net/")
    print("   - Fan-made transcript repositories on GitHub")
    print("\n2. Place transcript files in a folder (e.g., /transcripts/)")
    print("\n3. Use load_from_file() to process each transcript")
    print("\n4. Combine all dialogues and save to JSON/CSV")


if __name__ == "__main__":
    main()
    
