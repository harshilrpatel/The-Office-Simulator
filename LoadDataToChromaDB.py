"""
Load The Office dialogue data into ChromaDB with OpenAI embeddings

This script:
1. Reads all_dialogues.json from rag_data/
2. Generates embeddings using OpenAI text-embedding-3-small
3. Stores in ChromaDB for fast retrieval
4. Shows progress and statistics

Usage:
    python load_data_to_chromadb.py
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from tqdm import tqdm
from typing import List, Dict


class OfficeDialogueLoader:
    """Load Office dialogue into ChromaDB"""
    
    def __init__(self, 
                 data_path: str = "rag_data/all_dialogues.json",
                 db_path: str = "./chroma_db",
                 collection_name: str = "office_dialogues"):
        """
        Initialize loader
        
        Args:
            data_path: Path to all_dialogues.json
            db_path: Path to ChromaDB storage
            collection_name: Name of the collection
        """
        self.data_path = data_path
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found! "
                "Create a .env file with: OPENAI_API_KEY=your-key-here"
            )
        
        print(f"✓ API key loaded")
    
    def load_data(self) -> List[Dict]:
        """Load dialogue data from JSON"""
        print(f"\nLoading data from: {self.data_path}")
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                dialogues = json.load(f)
            
            print(f"✓ Loaded {len(dialogues):,} dialogue entries")
            return dialogues
            
        except FileNotFoundError:
            print(f"✗ Error: {self.data_path} not found!")
            print(f"\nRun this first: python transcript_to_rag.py")
            return []
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return []
    
    def initialize_chromadb(self):
        """Initialize ChromaDB client and collection"""
        print(f"\nInitializing ChromaDB at: {self.db_path}")
        
        # Create persistent client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create OpenAI embedding function
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.api_key,
            model_name="text-embedding-3-small"
        )
        
        # Delete collection if it exists (for fresh start)
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"✓ Deleted existing collection: {self.collection_name}")
        except:
            pass
        
        # Create collection
        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=openai_ef,
            metadata={"description": "The Office TV Show Dialogues"}
        )
        
        print(f"✓ Created collection: {self.collection_name}")
    
    def load_to_chromadb(self, dialogues: List[Dict], batch_size: int = 100):
        """
        Load dialogues into ChromaDB with embeddings
        
        Args:
            dialogues: List of dialogue dictionaries
            batch_size: Number of items to process at once (lower = slower but safer)
        """
        print(f"\nLoading {len(dialogues):,} dialogues into ChromaDB...")
        print(f"Batch size: {batch_size}")
        print(f"This will take ~5-10 minutes...\n")
        
        total_batches = (len(dialogues) + batch_size - 1) // batch_size
        
        with tqdm(total=len(dialogues), desc="Processing") as pbar:
            for i in range(0, len(dialogues), batch_size):
                batch = dialogues[i:i + batch_size]
                
                # Prepare data for ChromaDB
                ids = []
                documents = []
                metadatas = []
                
                for idx, dialogue in enumerate(batch):
                    # Unique ID
                    doc_id = f"dialogue_{i + idx}"
                    
                    # Document text (what gets embedded and searched)
                    # Include character and text for better context
                    doc_text = f"{dialogue['character']}: {dialogue['text']}"
                    
                    # Metadata (for filtering and display)
                    metadata = {
                        'character': dialogue['character'],
                        'season': dialogue['season'],
                        'episode_number': dialogue['episode_number'],
                        'episode_code': dialogue['episode_code'],
                        'episode_title': dialogue['episode_title'],
                        'line_number': dialogue['line_number'],
                        'scene_context': dialogue.get('scene_context', ''),
                    }
                    
                    ids.append(doc_id)
                    documents.append(doc_text)
                    metadatas.append(metadata)
                
                # Add batch to collection (generates embeddings via OpenAI)
                try:
                    self.collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    print(f"\n✗ Error processing batch {i}-{i+len(batch)}: {e}")
                    print("Continuing with next batch...")
                    pbar.update(len(batch))
        
        print(f"\n✓ Successfully loaded {len(dialogues):,} dialogues!")
    
    def verify_data(self):
        """Verify data was loaded correctly"""
        print("\n" + "="*70)
        print("VERIFICATION")
        print("="*70)
        
        # Count items
        count = self.collection.count()
        print(f"Total items in collection: {count:,}")
        
        # Test query
        print("\nTest query: 'That's what she said'")
        results = self.collection.query(
            query_texts=["That's what she said"],
            n_results=3
        )
        
        if results['documents']:
            print("\nTop 3 results:")
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
                print(f"\n{i}. {doc[:100]}...")
                print(f"   Episode: {metadata['episode_code']} - {metadata['episode_title']}")
                print(f"   Season {metadata['season']}, Episode {metadata['episode_number']}")
    
    def print_statistics(self, dialogues: List[Dict]):
        """Print data statistics"""
        from collections import Counter
        
        print("\n" + "="*70)
        print("DATA STATISTICS")
        print("="*70)
        
        # Count by season
        seasons = Counter([d['season'] for d in dialogues])
        print("\nDialogues per season:")
        for season in sorted(seasons.keys()):
            print(f"  Season {season}: {seasons[season]:,}")
        
        # Count by character
        characters = Counter([d['character'] for d in dialogues])
        print("\nTop 10 characters by dialogue count:")
        for char, count in characters.most_common(10):
            print(f"  {char:20s} {count:6,} lines")
    
    def run(self):
        """Main execution"""
        print("="*70)
        print(" "*15 + "LOADING DATA TO CHROMADB")
        print("="*70)
        
        # Load dialogue data
        dialogues = self.load_data()
        
        if not dialogues:
            print("\n✗ No data to load. Exiting.")
            return
        
        # Print statistics
        self.print_statistics(dialogues)
        
        # Initialize ChromaDB
        self.initialize_chromadb()
        
        # Confirm before proceeding
        print("\n" + "="*70)
        print("READY TO LOAD")
        print("="*70)
        print(f"Items to process: {len(dialogues):,}")
        print(f"Estimated cost: $0.50 - $2.00 (one-time)")
        print(f"Estimated time: 5-10 minutes")
        
        response = input("\nProceed with loading? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return
        
        # Load data
        self.load_to_chromadb(dialogues)
        
        # Verify
        self.verify_data()
        
        print("\n" + "="*70)
        print("✓ ALL DONE!")
        print("="*70)
        print(f"\nChromaDB created at: {self.db_path}/")
        print(f"Collection name: {self.collection_name}")
        print(f"\nNext step: Run office_expert_chat.py to start chatting!")


def main():
    """Main entry point"""
    loader = OfficeDialogueLoader()
    loader.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()