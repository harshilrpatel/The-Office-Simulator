"""
Transcript to RAG Processor
Converts raw transcript .txt files into structured JSON/CSV for RAG systems
Handles formatting issues like "Michael :\nxyz" and "Dwight:\nabc"
"""

import os
import re
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Dialogue:
    """Structured dialogue entry for RAG"""
    character: str
    text: str
    episode_code: str
    season: int
    episode_number: int
    episode_title: str
    line_number: int
    scene_context: str = ""
    
    def to_dict(self):
        return asdict(self)


class TranscriptToRAGProcessor:
    """Process raw transcripts into RAG-ready format"""
    
    def __init__(self, input_dir: str = "transcripts_converted", output_dir: str = "rag_data",
                 keep_stage_directions: bool = True):
        """
        Initialize processor
        
        Args:
            input_dir: Directory containing .txt transcript files
            output_dir: Directory to save processed JSON/CSV files
            keep_stage_directions: Whether to keep stage directions like (smiling), (sarcastically)
                                  True = Keep them (more realistic characters)
                                  False = Remove them (cleaner text)
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.keep_stage_directions = keep_stage_directions
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Character name normalization mapping
        self.character_mappings = {
            'Micheal': 'Michael',
            'Diwght': 'Dwight',
            'Michel': 'Michael',
            'Dwigh': 'Dwight',
            'Pam Beesly': 'Pam',
            'Pam Halpert': 'Pam',
            'Jim Halpert': 'Jim',
            'Dwight Schrute': 'Dwight',
            'Dwight K. Schrute': 'Dwight',
            'Michael Scott': 'Michael',
            'Michael Gary Scott': 'Michael',
            'Angela Martin': 'Angela',
            'Oscar Martinez': 'Oscar',
            'Kevin Malone': 'Kevin',
            'Stanley Hudson': 'Stanley',
            'Phyllis Vance': 'Phyllis',
            'Ryan Howard': 'Ryan',
            'Kelly Kapoor': 'Kelly',
            'Toby Flenderson': 'Toby',
            'Creed Bratton': 'Creed',
            'Meredith Palmer': 'Meredith',
            'Erin Hannon': 'Erin',
            'Andy Bernard': 'Andy',
            'Darryl Philbin': 'Darryl',
            'Holly Flax' : 'Holly',
            'Holly' : 'Holly'
        }
        
        # Stats
        self.total_files = 0
        self.total_dialogues = 0
        self.dialogues_by_season = defaultdict(list)
    
    def normalize_character_name(self, name: str) -> str:
        """
        Normalize character name (fix typos, standardize)
        
        Args:
            name: Raw character name
            
        Returns:
            Normalized name
        """
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Title case
        name = name.title()
        
        # Apply mappings
        return self.character_mappings.get(name, name)
    
    def parse_episode_filename(self, filename: str) -> Optional[Dict]:
        """
        Parse episode information from filename
        
        Examples:
            "01x01.txt" -> {season: 1, episode: 1, code: "01x01", title: ""}
            "01x01_Pilot.txt" -> {season: 1, episode: 1, code: "01x01", title: "Pilot"}
            "09x24-25.txt" -> {season: 9, episode: 24, code: "09x24-25", title: ""}
            "09x24-25_AARM.txt" -> {season: 9, episode: 24, code: "09x24-25", title: "AARM"}
        
        Args:
            filename: Transcript filename
            
        Returns:
            Dict with episode info or None
        """
        # Remove .txt extension
        name = filename.replace('.txt', '')
        
        # Match pattern: 01x01 or 09x24-25, optionally followed by _Episode_Name
        match = re.match(r'(\d+)x(\d+(?:-\d+)?)(?:_(.+))?', name)
        
        if match:
            season = int(match.group(1))
            episode_str = match.group(2)
            title_from_filename = match.group(3) if match.group(3) else ""
            
            # Convert underscores back to spaces in title
            if title_from_filename:
                title_from_filename = title_from_filename.replace('_', ' ')
            
            # Handle double episodes
            if '-' in episode_str:
                episode = int(episode_str.split('-')[0])
            else:
                episode = int(episode_str)
            
            return {
                'season': season,
                'episode_number': episode,
                'episode_code': match.group(1) + 'x' + episode_str,
                'title_from_filename': title_from_filename
            }
        
        return None
    
    def parse_transcript(self, filepath: str, episode_info: Dict) -> List[Dialogue]:
        """
        Parse a transcript file into structured dialogues
        
        Handles formats like:
        - "Michael :\nxyz"
        - "Dwight:\nabc"
        - "Jim: Hello there"
        - "[SCENE: Office]"
        
        Args:
            filepath: Path to transcript file
            episode_info: Dict with season, episode_number, episode_code
            
        Returns:
            List of Dialogue objects
        """
        dialogues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
            return []
        
        # Split into lines
        lines = content.split('\n')
        
        current_scene = "Opening"
        line_number = 0
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for scene markers
            if line.startswith('[') or (line.isupper() and len(line) < 100 and ':' not in line):
                current_scene = line.strip('[]')
                i += 1
                continue
            
            # Check for character dialogue
            # Pattern: "Character :" or "Character:"
            # Handle spaces before colon
            match = re.match(r'^([A-Z][a-zA-Z\s\'\.\-]+?)\s*:\s*(.*)$', line)
            
            if match:
                character = match.group(1).strip()
                dialogue_start = match.group(2).strip()
                
                # Normalize character name
                character = self.normalize_character_name(character)
                
                # Collect dialogue (might be on next lines)
                dialogue_parts = []
                
                if dialogue_start:
                    # Dialogue on same line
                    dialogue_parts.append(dialogue_start)
                else:
                    # Dialogue on next line(s)
                    i += 1
                    while i < len(lines):
                        next_line = lines[i].strip()
                        
                        # Stop if empty line or next character
                        if not next_line:
                            break
                        
                        # Stop if it's a new character speaking
                        if re.match(r'^[A-Z][a-zA-Z\s\'\.\-]+?\s*:', next_line):
                            i -= 1  # Back up to process this line next
                            break
                        
                        # Stop if it's a scene marker
                        if next_line.startswith('['):
                            i -= 1
                            break
                        
                        dialogue_parts.append(next_line)
                        i += 1
                
                # Combine dialogue parts
                dialogue_text = ' '.join(dialogue_parts).strip()
                
                # Stage directions handling
                if not self.keep_stage_directions:
                    # Remove stage directions in parentheses
                    dialogue_text = re.sub(r'\([^)]*\)', '', dialogue_text).strip()
                # else: Keep stage directions for more realistic character behavior
                
                # Only add if there's actual dialogue (not just dashes)
                if dialogue_text and dialogue_text not in ['---', '----', '-----', '------', '-------']:
                    line_number += 1
                    
                    dialogue = Dialogue(
                        character=character,
                        text=dialogue_text,
                        episode_code=episode_info['episode_code'],
                        season=episode_info['season'],
                        episode_number=episode_info['episode_number'],
                        episode_title=episode_info.get('episode_title', ''),
                        line_number=line_number,
                        scene_context=current_scene
                    )
                    
                    dialogues.append(dialogue)
            
            i += 1
        
        return dialogues
    
    def process_all_transcripts(self, episode_titles: Optional[Dict[int, List[str]]] = None):
        """
        Process all transcript files in the input directory
        
        Args:
            episode_titles: Optional dict mapping season -> list of episode titles
                           {1: ['Pilot', 'Diversity Day', ...], 2: [...]}
        """
        # Find all .txt files
        txt_files = sorted(Path(self.input_dir).glob('*.txt'))
        
        if not txt_files:
            print(f"⚠ No .txt files found in {self.input_dir}")
            return
        
        print(f"Found {len(txt_files)} transcript files")
        print(f"Processing...\n")
        
        self.total_files = len(txt_files)
        all_dialogues = []
        
        for filepath in txt_files:
            filename = filepath.name
            
            # Parse episode info from filename
            episode_info = self.parse_episode_filename(filename)
            
            if not episode_info:
                print(f"⚠ Skipping {filename} - couldn't parse episode info")
                continue
            
            # Add episode title if available
            if episode_titles:
                season = episode_info['season']
                ep_num = episode_info['episode_number']
                if season in episode_titles and ep_num - 1 < len(episode_titles[season]):
                    episode_info['episode_title'] = episode_titles[season][ep_num - 1]
                elif episode_info.get('title_from_filename'):
                    # Use title from filename if episodes_dict doesn't have it
                    episode_info['episode_title'] = episode_info['title_from_filename']
                else:
                    episode_info['episode_title'] = f"Episode {ep_num}"
            elif episode_info.get('title_from_filename'):
                # No episodes_dict, use title from filename
                episode_info['episode_title'] = episode_info['title_from_filename']
            else:
                episode_info['episode_title'] = f"S{episode_info['season']}E{episode_info['episode_number']}"
            
            print(f"Processing: {filename} - {episode_info['episode_title']}")
            
            # Parse transcript
            dialogues = self.parse_transcript(str(filepath), episode_info)
            
            print(f"  ✓ Extracted {len(dialogues)} dialogue lines")
            
            # Store by season
            self.dialogues_by_season[episode_info['season']].extend(dialogues)
            all_dialogues.extend(dialogues)
        
        self.total_dialogues = len(all_dialogues)
        
        print(f"\n{'='*70}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Files processed: {self.total_files}")
        print(f"Total dialogues: {self.total_dialogues:,}")
        print(f"Seasons: {len(self.dialogues_by_season)}")
    
    def save_by_season(self, format: str = 'both'):
        """
        Save processed dialogues split by season
        
        Args:
            format: 'json', 'csv', or 'both'
        """
        print(f"\n{'='*70}")
        print(f"SAVING FILES BY SEASON")
        print(f"{'='*70}\n")
        
        for season in sorted(self.dialogues_by_season.keys()):
            dialogues = self.dialogues_by_season[season]
            
            print(f"Season {season}: {len(dialogues)} dialogues")
            
            # Convert to dicts
            data = [d.to_dict() for d in dialogues]
            
            # Save JSON
            if format in ['json', 'both']:
                json_path = os.path.join(self.output_dir, f'season_{season}.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved: {json_path}")
            
            # Save CSV
            if format in ['csv', 'both']:
                csv_path = os.path.join(self.output_dir, f'season_{season}.csv')
                df = pd.DataFrame(data)
                df.to_csv(csv_path, index=False, encoding='utf-8')
                print(f"  ✓ Saved: {csv_path}")
            
            print()
    
    def save_combined(self, format: str = 'both'):
        """
        Save all dialogues in a single file
        
        Args:
            format: 'json', 'csv', or 'both'
        """
        print(f"{'='*70}")
        print(f"SAVING COMBINED FILE")
        print(f"{'='*70}\n")
        
        # Combine all dialogues
        all_dialogues = []
        for season in sorted(self.dialogues_by_season.keys()):
            all_dialogues.extend(self.dialogues_by_season[season])
        
        data = [d.to_dict() for d in all_dialogues]
        
        # Save JSON
        if format in ['json', 'both']:
            json_path = os.path.join(self.output_dir, 'all_dialogues.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved: {json_path} ({len(all_dialogues):,} dialogues)")
        
        # Save CSV
        if format in ['csv', 'both']:
            csv_path = os.path.join(self.output_dir, 'all_dialogues.csv')
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"✓ Saved: {csv_path} ({len(all_dialogues):,} dialogues)")
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        stats = {
            'total_files': self.total_files,
            'total_dialogues': self.total_dialogues,
            'dialogues_by_season': {
                season: len(dialogues) 
                for season, dialogues in self.dialogues_by_season.items()
            },
            'character_stats': {}
        }
        
        # Character statistics
        character_counts = defaultdict(int)
        for dialogues in self.dialogues_by_season.values():
            for d in dialogues:
                character_counts[d.character] += 1
        
        # Sort by count
        stats['character_stats'] = dict(
            sorted(character_counts.items(), key=lambda x: x[1], reverse=True)
        )
        
        return stats
    
    def print_statistics(self):
        """Print detailed statistics"""
        stats = self.get_statistics()
        
        print(f"\n{'='*70}")
        print(f"STATISTICS")
        print(f"{'='*70}\n")
        
        print(f"Total Files Processed: {stats['total_files']}")
        print(f"Total Dialogue Lines: {stats['total_dialogues']:,}")
        print(f"Seasons: {len(stats['dialogues_by_season'])}\n")
        
        print("Dialogues per Season:")
        print("-" * 70)
        for season, count in sorted(stats['dialogues_by_season'].items()):
            print(f"  Season {season}: {count:,} lines")
        
        print(f"\nTop 15 Characters:")
        print("-" * 70)
        for idx, (char, count) in enumerate(list(stats['character_stats'].items())[:15], 1):
            print(f"  {idx:2d}. {char:20s} {count:6,} lines")
    
    def save_statistics(self):
        """Save statistics to JSON"""
        stats = self.get_statistics()
        
        stats_path = os.path.join(self.output_dir, 'statistics.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n✓ Statistics saved to: {stats_path}")


def main():
    """Main execution"""
    print("="*70)
    print(" "*15 + "TRANSCRIPT TO RAG PROCESSOR")
    print("="*70 + "\n")
    
    # Initialize processor (keeps stage directions for realistic characters)
    processor = TranscriptToRAGProcessor(
        input_dir="transcripts_converted",
        output_dir="rag_data",
        keep_stage_directions=True  # Keep (smiling), (sarcastically), etc.
    )
    
    # Check if episode titles exist
    episode_titles = None
    if os.path.exists('transcripts_converted/episodes_dict.json'):
        print("Found episodes_dict.json - loading episode titles...")
        with open('transcripts_converted/episodes_dict.json', 'r') as f:
            data = json.load(f)
            # Convert string keys to int
            episode_titles = {int(k): v for k, v in data.items()}
        print("✓ Episode titles loaded\n")
    else:
        print("No episodes_dict.json found - using default episode names\n")
    
    # Process all transcripts
    processor.process_all_transcripts(episode_titles=episode_titles)
    
    # Print statistics
    processor.print_statistics()
    
    # Save files
    print(f"\n{'='*70}")
    print("SAVING OUTPUT FILES")
    print(f"{'='*70}\n")
    
    response = input("Save format (json/csv/both) [both]: ").strip().lower()
    if not response:
        response = 'both'
    
    # Save by season
    processor.save_by_season(format=response)
    
    # Save combined
    processor.save_combined(format=response)
    
    # Save statistics
    processor.save_statistics()
    
    print(f"\n{'='*70}")
    print("✓ PROCESSING COMPLETE!")
    print(f"{'='*70}")
    print(f"\nOutput directory: {processor.output_dir}/")
    print(f"\nFiles created:")
    print(f"  - season_1.json/csv")
    print(f"  - season_2.json/csv")
    print(f"  - ...")
    print(f"  - all_dialogues.json/csv")
    print(f"  - statistics.json")


if __name__ == "__main__":
    main()