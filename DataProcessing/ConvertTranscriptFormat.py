"""
Transcript Format Converter
Converts old format (character name on separate line) to new format (character: dialogue on same line)

Old Format:
Michael
: All right Jim. Your quarterlies look very good.
Jim
: Oh, I told you. I couldn't close it.

New Format:
Michael: All right Jim. Your quarterlies look very good.
Jim: Oh, I told you. I couldn't close it.
"""

import os
import re
from pathlib import Path
from typing import List


class TranscriptFormatConverter:
    """Convert transcript from old format to new format"""
    
    def __init__(self, input_dir: str = "transcripts", output_dir: str = "transcripts_converted"):
        """
        Initialize converter
        
        Args:
            input_dir: Directory containing old format transcripts
            output_dir: Directory to save converted transcripts
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def convert_file(self, input_path: str, output_path: str) -> bool:
        """
        Convert a single transcript file from old to new format
        
        Args:
            input_path: Path to input file (old format)
            output_path: Path to output file (new format)
            
        Returns:
            True if successful
        """
        try:
            # Read input file
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Convert format
            converted_lines = self._convert_lines(lines)
            
            # Write output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(converted_lines)
            
            return True
            
        except Exception as e:
            print(f"✗ Error converting {input_path}: {e}")
            return False
    
    def _convert_lines(self, lines: List[str]) -> List[str]:
        """
        Convert lines from old format to new format
        
        Old Format:
            Michael
            : All right Jim.
            Jim
            : Oh, I told you.
        
        New Format:
            Michael: All right Jim.
            Jim: Oh, I told you.
        
        Args:
            lines: List of lines in old format
            
        Returns:
            List of lines in new format
        """
        converted = []
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip('\n')
            
            # Check if this line is a character name (next line starts with :)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # Pattern: Current line is character name, next line starts with ":"
                if next_line.startswith(':'):
                    # This is a character name
                    character = line.strip()
                    
                    # Get the dialogue (remove leading ":")
                    dialogue = next_line[1:].strip()
                    
                    # Check if dialogue continues on more lines
                    # Look ahead to see if the next lines are continuation (don't start with : and aren't character names)
                    j = i + 2
                    dialogue_parts = [dialogue]
                    
                    while j < len(lines):
                        peek_line = lines[j].strip()
                        
                        # Stop if empty line
                        if not peek_line:
                            break
                        
                        # Stop if next line starts with : (new dialogue)
                        if peek_line.startswith(':'):
                            break
                        
                        # Stop if it looks like a character name (check if line after is ":")
                        if j + 1 < len(lines) and lines[j + 1].strip().startswith(':'):
                            break
                        
                        # This line is continuation of dialogue
                        dialogue_parts.append(peek_line)
                        j += 1
                    
                    # Combine all dialogue parts
                    full_dialogue = ' '.join(dialogue_parts)
                    
                    # Write in new format: "Character: dialogue"
                    converted.append(f"{character}: {full_dialogue}\n")
                    
                    # Skip processed lines
                    i = j
                    continue
            
            # If we get here, this line is not a character:dialogue pattern
            # It might be an empty line, stage direction, etc. - keep as is
            if line.strip():
                converted.append(line + '\n')
            
            i += 1
        
        return converted
    
    def convert_all(self, pattern: str = "*.txt"):
        """
        Convert all transcript files in the input directory
        
        Args:
            pattern: File pattern to match (default: *.txt)
        """
        # Find all matching files
        input_files = list(Path(self.input_dir).glob(pattern))
        
        if not input_files:
            print(f"⚠ No files found matching '{pattern}' in {self.input_dir}")
            return
        
        print(f"Found {len(input_files)} files to convert")
        print(f"Input:  {self.input_dir}/")
        print(f"Output: {self.output_dir}/\n")
        
        successful = 0
        failed = 0
        
        for input_path in input_files:
            filename = input_path.name
            output_path = os.path.join(self.output_dir, filename)
            
            print(f"Converting: {filename}...", end=" ")
            
            if self.convert_file(str(input_path), output_path):
                print("✓")
                successful += 1
            else:
                print("✗")
                failed += 1
        
        # Summary
        print(f"\n{'='*70}")
        print(f"CONVERSION COMPLETE")
        print(f"{'='*70}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"\nConverted files saved to: {self.output_dir}/")
    
    def preview_conversion(self, input_path: str, num_lines: int = 20):
        """
        Preview how a file will be converted (first N lines)
        
        Args:
            input_path: Path to input file
            num_lines: Number of lines to show
        """
        try:
            # Read input
            with open(input_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Convert
            converted = self._convert_lines(lines)
            
            # Show comparison
            print("="*70)
            print(f"PREVIEW: {os.path.basename(input_path)}")
            print("="*70)
            
            print("\nORIGINAL FORMAT (first 20 lines):")
            print("-"*70)
            for line in lines[:num_lines]:
                print(line.rstrip())
            
            print("\n\nCONVERTED FORMAT (first 20 lines):")
            print("-"*70)
            for line in converted[:num_lines]:
                print(line.rstrip())
            
            print("\n" + "="*70)
            
        except Exception as e:
            print(f"✗ Error: {e}")


def main():
    """Main execution"""
    import sys
    
    print("="*70)
    print(" "*15 + "TRANSCRIPT FORMAT CONVERTER")
    print(" "*10 + "Old Format → New Format")
    print("="*70 + "\n")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--preview':
            # Preview mode
            if len(sys.argv) > 2:
                converter = TranscriptFormatConverter()
                converter.preview_conversion(sys.argv[2])
            else:
                print("Usage: python convert_transcript_format.py --preview <file>")
            return
    
    # Get input/output directories
    print("This will convert transcripts from:")
    print("  OLD: Character name on one line, ': dialogue' on next")
    print("  NEW: Character: dialogue on same line\n")
    
    input_dir = input("Input directory [transcripts]: ").strip() or "transcripts"
    output_dir = input("Output directory [transcripts_converted]: ").strip() or "transcripts_converted"
    
    print()
    
    # Initialize converter
    converter = TranscriptFormatConverter(
        input_dir=input_dir,
        output_dir=output_dir
    )
    
    # Convert all files
    converter.convert_all()
    
    print("\n✓ Done! Check the converted files in:", output_dir)


if __name__ == "__main__":
    main()