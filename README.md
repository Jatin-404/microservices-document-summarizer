# Microservices Document Summarizer

A multi-service document processing system built with FastAPI and Ollama. Uploads text files, chunks them into 200-word segments, and generates AI-powered summaries using a local LLM.

## Architecture

- **Service A (Ingestion)**: Handles file uploads, chunks text, orchestrates processing
- **Service B (Processor)**: Generates summaries using Ollama's local LLM

## Features

- ✅ Multi-service architecture with async inter-service communication
- ✅ File chunking with configurable chunk size
- ✅ AI-powered summarization using Ollama (llama3.2)
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
cd service-a
pip install -r requirements.txt

# Service B
cd ../service-b
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# In service-a/
cp .env.example .env
# Edit .env with your configuration
```

## Usage

1. Start Ollama:
```bash
ollama serve
```

2. Start Service B (Processor):
```bash
cd service-b
python main.py
# Runs on http://localhost:8001
```

3. Start Service A (Ingestion):
```bash
cd service-a
python main.py
# Runs on http://localhost:8000
```

4. Upload a document:
```bash
curl -X POST -F "file=@sample.txt" http://localhost:8000/upload
```

## API Endpoints

### Service A (Port 8000)
- `GET /health` - Health check
- `POST /upload` - Upload and process .txt files

### Service B (Port 8001)
- `GET /health` - Health check
- `POST /process` - Process text chunks and generate summaries

## Configuration

Service A `.env`:
```
APP_B_URL=http://localhost:8001/process
```

Service B `.env`:
```
OLLAMA_MODEL=llama3.2:1b
```

## Example Response
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
    ...
  ]
}
```

## Error Handling

- UTF-8 validation for uploaded files
- Empty file detection
- Service B availability checks
- Graceful fallback to extractive summarization if Ollama fails

## Learning Outcomes

This project demonstrates:
- Microservices architecture patterns
- Async/await in Python
- FastAPI best practices
- Inter-service HTTP communication
- Environment-based configuration
- Pydantic data validation
- Local LLM integration with Ollama

## Future Improvements

- [ ] Batch processing for parallel chunk summarization
- [ ] Support for PDF and DOCX files
- [ ] Caching layer for repeated chunks
- [ ] Docker containerization
- [ ] Persistent storage for results
- [ ] Web UI for file uploads

## License

MIT

## Author

[Your Name] - Learning FastAPI and microservices architecture