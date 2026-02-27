from fastapi import FastAPI, UploadFile, File, HTTPException
import httpx
import os
from dotenv import load_dotenv
import uvicorn
import json
from tenacity import (                   # Tenacity is a Python library that automatically retries a function when it fails.
    retry, stop_after_attempt,
    wait_exponential, retry_if_exception_type)
from shared.logger import setup_logging
from pathlib import Path                                    #  used this instead of jsut loadenv 
                                                            #  bcz my env files are in apps folder not in
env_path = Path(__file__).resolve().parent / ".env"         # root dir so whule running from root dir
load_dotenv(dotenv_path=env_path)                           # it searches for env in root dir and this fixes this prob



logger = setup_logging("app-a")

APP_B_URL= os.getenv("APP_B_URL", "http://localhost:8001/process")
logger.info(f"APP_B_URL is: {APP_B_URL}")  # add this temporarily
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

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1),        # 1s, 2s, 4s
    retry=retry_if_exception_type(httpx.RequestError),  # only retry on network errors, not 4xx/5xx
    reraise=True
)
async def call_service_b(client: httpx.AsyncClient, chunk: dict) -> dict:
    logger.info("Calling Service B", extra={"chunk_index": chunk["chunk_index"]})
    response = await client.post(APP_B_URL, json=chunk)
    response.raise_for_status()
    return response.json()

@app.get("/health")
async def health():
    logger.info("App A is running")
    return{
        "Status": "Healthy",
        "Service": "ingestion-serive"
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        logger.error("Only .txt file allowed",
                     extra={
                         "target_url": f"{APP_B_URL}/upload"
                     })
        raise HTTPException(status_code=400, detail="Only .txt file allowed")
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        logger.error("File is not valid utf-8 text",
                     extra={
                         "target_url": f"{APP_B_URL}/upload"
                     })
        raise HTTPException(status_code=400, detail="File is not valid utf-8 text")
    
    if not text.strip():
        logger.error("File is empty",
                     extra={
                         "target_url": f"{APP_B_URL}/upload"
                     })
        raise HTTPException(status_code=400, detail="File is empty")
    
    chunks = split_into_chunks(text, chunk_size = 200)
    summaries = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for chunk in chunks:
            try:
#                response = await client.post(APP_B_URL, json=chunk)      when i wasnt using retry connection logic 
#                response.raise_for_status()
                result_chunk = await call_service_b(client, chunk)
                summaries.append(result_chunk)
            except httpx.RequestError as e:
                logger.error("Service B is unreachable",
                             extra={
                                 "error": str(e),
                                 "target_url": f"{APP_B_URL}/upload"
                             })
                 # Service B is unreachable (network error, connection refused, etc.)
                raise HTTPException(
                    status_code=503,
                    detail=f"Service B is unreachable: {str(e)}"
                )
            except httpx.HTTPStatusError as e:
                logger.error("Service B returned error",
                             extra={
                                 "error": str(e),
                                 "target_url": f"{APP_B_URL}/upload"
                             })
                # Service B returned an error status code
                raise HTTPException(
                    status_code=502,
                    detail=f"Service B returned error: {e.response.status_code}"
                )
            except Exception as e :
                logger.error(f"Unexpected error processing chunk {chunk['chunk_index']}",
                             extra={
                                 "error": str(e),
                                 "target_url": f"{APP_B_URL}/upload"
                             })
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



