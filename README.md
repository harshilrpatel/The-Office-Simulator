# The Office Simulator - RAG-Based Chatbot

A proof-of-concept chatbot that leverages transcript data from NBC's "The Office" to create an intelligent conversational agent. Built using ChromaDB for vector storage and OpenAI's GPT models for natural language understanding.

## Overview

This project demonstrates how to build a Retrieval-Augmented Generation (RAG) system using television show transcripts. The chatbot acts as "The Office Expert," capable of answering questions about characters, episodes, storylines, and memorable moments from the series.

Rather than simply regurgitating dialogue, the system uses semantic search to find relevant context and generates natural, conversational responses that feel like chatting with a fellow fan of the show.

## Motivation

This started as an exploration into building character-aware AI agents. The goal was to see how well a RAG system could capture the nuances of a TV show - character personalities, running gags, relationship dynamics, and episodic continuity - using only transcript data.

The Office made for an ideal test case given its distinctive characters, strong character development over 9 seasons, and rich dialogue-driven humor.

## Technical Architecture

### Data Pipeline

1. **Transcript Scraping** - Automated collection of episode transcripts from Forever Dreaming
2. **Format Conversion** - Standardization of various transcript formats into a consistent structure
3. **Data Processing** - Parsing dialogues with character attribution, episode metadata, and scene context
4. **Vector Embedding** - Converting ~80,000 dialogue lines into semantic embeddings via OpenAI
5. **Storage** - Persistent storage in ChromaDB for efficient similarity search

### RAG System

The chatbot uses a straightforward RAG architecture:

1. User submits a query
2. Query is embedded using OpenAI's text-embedding-3-small model
3. ChromaDB performs similarity search to retrieve top-k relevant dialogues
4. Retrieved context is injected into the LLM prompt
5. GPT-4 generates a natural response using the context

### Key Components

**Transcript Scraper** (`office_transcript_scraper.py`)
- Handles pagination across forum pages
- Parses episode metadata from page titles
- Cleans and normalizes transcript formatting
- Saves files with episode names for easy identification

**Format Converter** (`convert_transcript_format.py`)
- Converts various transcript formats to a standardized structure
- Handles multi-line dialogues and stage directions
- Preserves character attributions and scene context

**RAG Processor** (`transcript_to_rag.py`)
- Parses transcript files into structured JSON/CSV
- Normalizes character names (handles typos and variations)
- Preserves stage directions for richer character context
- Generates statistics on dialogue distribution

**ChromaDB Loader** (`load_data_to_chromadb.py`)
- Batch processing of dialogue data
- Generates embeddings via OpenAI API
- Creates persistent vector database
- Includes verification and statistics

**Chat Interface** (`office_expert_chat.py`)
- CLI-based conversation interface
- Semantic search for relevant context
- Natural language generation with GPT
- Protected system prompt to maintain character

## Features

**Natural Conversations**
The chatbot doesn't reference "dialogue" or "context" - it responds as a knowledgeable fan would, using the retrieved information to inform natural responses.

**Stage Direction Awareness**
Preserving stage directions like "(smiling)" and "(sarcastically)" provides crucial context about how lines are delivered, making character responses more authentic.

**Episode-Specific Knowledge**
Each dialogue is tagged with episode metadata, allowing the system to provide specific references when relevant.

**Character Name Normalization**
Handles variations like "Dwight K. Schrute" vs "Dwight" to ensure consistent character attribution.

**Prompt Injection Protection**
The system prompt includes explicit safeguards against attempts to override the chatbot's personality or extract system instructions.

## Installation

```bash
pip install chromadb openai python-dotenv pandas tqdm
```

Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

## Usage

**Process transcripts into RAG format:**
```bash
python transcript_to_rag.py
```

**Load data into ChromaDB (one-time setup):**
```bash
python load_data_to_chromadb.py
```

**Start chatting:**
```bash
python office_expert_chat.py
```

## Cost Considerations

**One-time setup:**
- Embedding generation: approximately $0.50-$2.00 for ~80,000 dialogue lines
- Uses OpenAI's text-embedding-3-small model

**Per query:**
- Query embedding: ~$0.00002
- GPT-4o-mini response: ~$0.001-$0.01
- Total per interaction: ~$0.01

The embedding cost is incurred only once during initial setup. Subsequent runs use the cached embeddings from ChromaDB.

## Project Structure

```
├── transcripts/                  # Raw transcript files
├── transcripts_converted/        # Processed transcript files
├── rag_data/                     # Processed dialogue data
├── chroma_db/                    # Vector database
├── DataProcessing
    ├── ConvertTranscriptFormat.py
    ├── SingleEpisodeScraper.py
    ├── TranscriptScraper.py
├── LoadDataToChromaDB.py         # Vector database setup
└── OfficeExpertChat.py         # Chat interface
```

## Lessons Learned

**Stage directions matter**
Initial versions stripped stage directions for "cleaner" text. Preserving them significantly improved the quality and authenticity of character-aware responses.

**Character name normalization is essential**
Transcripts use inconsistent character naming ("Michael Scott" vs "Michael" vs "Michel" typos). Without normalization, the same character appears fragmented across the database.

**Prompt engineering over fine-tuning**
A well-crafted system prompt with clear personality guidelines proved more effective than attempting to fine-tune models on the dialogue data directly.

**Semantic search isn't perfect**
Sometimes the retrieved context is tangentially related rather than directly relevant. This is an inherent limitation of embedding-based similarity search.

**RAG works well for this use case**
The combination of retrieval and generation handles the breadth of questions well - from specific episode details to general character analysis.

## Future Scope

This is a proof of concept demonstrating the technical feasibility of building character-aware conversational agents from transcript data. The current implementation is a single chatbot with knowledge of the entire show.

**Planned enhancements:**

**Multi-Character System**
Individual agents for each major character (Michael, Jim, Pam, Dwight, etc.) with:
- Character-specific response styles
- Filtered knowledge bases (only that character's dialogue and scenes they were in)
- Distinct personalities and speech patterns
- Awareness of relationships with other characters

**Slack Integration**
Transform this into a Slack workspace where:
- Each character is a separate bot
- Users can ask questions or chat with specific characters
- Characters can be tagged in conversations
- Group discussions where multiple character bots interact

**Agentic Capabilities**
Evolve from simple Q&A to autonomous agents that can:
- Initiate conversations based on context
- React to channel activity
- Interact with each other in character
- Maintain conversation history and context

## Acknowledgments

This project was built with significant assistance from Claude (Anthropic). The entire data pipeline, RAG system architecture, and implementation were developed through an iterative conversation - from initial concept through scraping, processing, vectorization, and deployment.

Claude helped with:
- Designing the transcript scraping system with pagination support
- Building format converters for various transcript structures
- Implementing the RAG processing pipeline
- Creating the ChromaDB integration
- Crafting the system prompts for natural conversation
- Debugging edge cases throughout the development process

The collaborative nature of this development - where I provided requirements and Claude generated implementations - made it possible to build this entire system in a matter of hours rather than weeks.

## Technical Notes

**Why ChromaDB**
Local-first, easy to set up, good Python integration, and sufficient for this scale (80k vectors).

**Why OpenAI embeddings**
High quality semantic representations, good API support, reasonable cost for one-time embedding generation.

**Why GPT-4o-mini**
Balanced cost/performance for the generation task. Can be swapped for GPT-4o for higher quality responses if needed.

**Why preserve stage directions**
They provide critical context about delivery and emotion that pure dialogue lacks. "(sarcastically)" vs "(sincerely)" completely changes interpretation.

## License

This project is for educational and demonstration purposes. The Office and its content are property of NBC Universal. This tool is not affiliated with or endorsed by NBC, Universal, or the creators of The Office.

## Disclaimer

This is a fan project and proof of concept. Transcript data was collected from publicly available sources for educational purposes. The chatbot generates responses based on show content but is not an official product.