# Microservices Document Summarizer

A multi-service document processing system built with FastAPI and Ollama. Uploads text files, chunks them into 200-word segments, and generates AI-powered summaries using a local LLM.

## Architecture

- **Service A (Ingestion)**: Handles file uploads, chunks text, orchestrates processing, and saves results
- **Service B (Processor)**: Generates summaries using Ollama's local LLM

## Features

- ✅ Multi-service architecture with async inter-service communication
- ✅ File chunking with configurable chunk size
- ✅ AI-powered summarization using Ollama (llama3.2)
- ✅ Automatic JSON output file generation
- ✅ Comprehensive error handling and health checks
- ✅ Environment-based configuration
- ✅ Pydantic validation for request/response models

## Tech Stack

- **FastAPI** - Web framework
- **Ollama** - Local LLM inference
- **httpx** - Async HTTP client
- **Pydantic** - Data validation
- **python-dotenv** - Environment management

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Ollama model pulled: `ollama pull llama3.2:1b`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/microservices-document-summarizer.git
cd microservices-document-summarizer
```

2. Install dependencies:
```bash
# Service A
cd SERVICE-A
pip install -r requirements.txt

# Service B
cd ../SERVICE-B
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# In SERVICE-A/
cp .env.example .env

# In SERVICE-B/
cp .env.example .env

# Edit .env files with your configuration if needed
```

## Usage

1. Start Ollama:
```bash
ollama serve
```

2. Start Service B (Processor):
```bash
cd SERVICE-B
python main.py
# Runs on http://localhost:8001
```

3. Start Service A (Ingestion):
```bash
cd SERVICE-A
python main.py
# Runs on http://localhost:8000
```

4. Upload a document:
```bash
curl -X POST -F "file=@test.txt" http://localhost:8000/upload
```

## API Endpoints

### Service A (Port 8000)
- `GET /health` - Health check
- `POST /upload` - Upload and process .txt files

### Service B (Port 8001)
- `GET /health` - Health check
- `POST /process` - Process text chunks and generate summaries

## Configuration

**Service A `.env`:**
```env
APP_B_URL=http://localhost:8001/process
```

**Service B `.env`:**
```env
OLLAMA_MODEL=llama3.2:1b
```

## Output Files

Processed documents are automatically saved to `SERVICE-A/outputs/` as JSON files.

**Example output structure:**
```json
{
  "file_name": "sample.txt",
  "total_chunks": 3,
  "summaries": [
    {
      "chunk_index": 0,
      "summary": "This text discusses the importance of...",
      "word_count": 200
    },
    {
      "chunk_index": 1,
      "summary": "The document continues with examples of...",
      "word_count": 200
    },
    {
      "chunk_index": 2,
      "summary": "Finally, the text concludes by highlighting...",
      "word_count": 150
    }
  ],
  "processed_at": "2024-02-18T10:30:45.123456"
}
```

Output files are named: `{original_filename}_summary.json`

## Error Handling

- **UTF-8 validation** for uploaded files
- **Empty file detection**
- **Service B availability checks** with proper HTTP error codes
- **Graceful fallback** to extractive summarization if Ollama fails
- **Comprehensive exception handling** for network and processing errors

## Project Structure
```
microservices-document-summarizer/
├── README.md
├── .gitignore
├── requirements.txt
├── SERVICE-A/
│   ├── main.py
│   ├── .env.example
│   ├── requirements.txt
│   └── outputs/
│       └── .gitkeep
├── SERVICE-B/
│   ├── main.py
│   ├── .env.example
│   └── requirements.txt
├── test.txt
└── test2.txt
```

## Learning Outcomes

This project demonstrates:
- Microservices architecture patterns
- Async/await in Python
- FastAPI best practices
- Inter-service HTTP communication
- Environment-based configuration
- Pydantic data validation
- Local LLM integration with Ollama
- File I/O and JSON serialization
- Error handling and HTTP status codes

## Future Improvements

- [ ] Batch processing for parallel chunk summarization
- [ ] Support for PDF and DOCX files
- [ ] Caching layer for repeated chunks
- [ ] Docker containerization with docker-compose
- [ ] Web UI for file uploads
- [ ] Logging system for debugging and monitoring
- [ ] Unit tests with pytest
- [ ] Retry logic for Service B calls

## Troubleshooting

**Service B unreachable:**
- Ensure Ollama is running: `ollama serve`
- Check if the model is pulled: `ollama list`
- Verify Service B is running on port 8001

**Ollama errors:**
- Pull the model if not available: `ollama pull llama3.2:1b`
- Check Ollama logs for issues
- Ensure sufficient system resources (RAM)

**File upload errors:**
- Only `.txt` files are supported
- Ensure file is UTF-8 encoded
- Check that file is not empty

## License

MIT

## Author

Jatin Sharma - Learning FastAPI and microservices architecture

---

**Built as part of a 10-week learning journey toward building a full RAG (Retrieval-Augmented Generation) system.**
