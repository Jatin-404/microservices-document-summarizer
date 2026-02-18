from fastapi import FastAPI, UploadFile, File, HTTPException
import httpx
import os
from dotenv import load_dotenv
import uvicorn
import json
from pathlib import Path

load_dotenv()
APP_B_URL= os.getenv("APP_B_URL", "http://localhost:8001/process")
app = FastAPI()

def split_into_chunks(text: str, chunk_size: int = 200):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "chunk_index": i // chunk_size,
            "text": chunk_text
        })

    return chunks

@app.get("/health")
async def health():
    return{
        "Status": "Health",
        "Service": "ingestion-serive"
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt file allowed")
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid utf-8 text")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="File is empty")
    
    chunks = split_into_chunks(text, chunk_size = 200)
    summaries = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for chunk in chunks:
            try:
                response = await client.post(APP_B_URL, json=chunk)
                response.raise_for_status()
                summaries.append(response.json())
            except httpx.RequestError as e:
                 # Service B is unreachable (network error, connection refused, etc.)
                raise HTTPException(
                    status_code=503,
                    detail=f"Service B is unreachable: {str(e)}"
                )
            except httpx.HTTPStatusError as e:
                # Service B returned an error status code
                raise HTTPException(
                    status_code=502,
                    detail=f"Service B returned error: {e.response.status_code}"
                )
            except Exception as e :
                # Catch-all for unexpected errors
                raise HTTPException(
                    status_code=500,
                    detail= f"Unexpected error processing chunk {chunk['chunk_index']}: {str(e)}"
                )

    result =  {
        "file_name" : file.filename,
        "total_chunks": len(summaries),
        "summaries": summaries
    }


    # save to outputs folder 

    # Get project root (parent of SERVICE-A)
    BASE_DIR = Path(__file__).resolve().parent.parent
    # Define outputs folder in project root
    output_dir = BASE_DIR / "outputs"
    output_dir.mkdir(exist_ok=True)
    # Create output file path
    output_path = output_dir / f"{file.filename.replace('.txt', '')}_summary.json"
    # save json
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result




if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



