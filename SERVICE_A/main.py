from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import httpx
import os
from dotenv import load_dotenv
import uvicorn
import json
from tenacity import (                   # Tenacity is a Python library that automatically retries a function when it fails.
    retry, stop_after_attempt,
    wait_exponential, retry_if_exception_type)
from shared.logger import setup_logging
import uuid                                                 # to generate unique chunk ids
import asyncio                                              # to run chunks in // 
from pathlib import Path                                    #  used this instead of jsut loadenv 
                                                            #  bcz my env files are in apps folder not in
env_path = Path(__file__).resolve().parent / ".env"         # root dir so whule running from root dir
load_dotenv(dotenv_path=env_path)                           # it searches for env in root dir and this fixes this prob



logger = setup_logging("app-a")

APP_B_URL= os.getenv("APP_B_URL", "http://localhost:8001/process")

app = FastAPI()


jobs = {}        # plain dict to store all jobs in memory,   key = job_id(unique str) | Value = a dict with status + results


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

# this func contains old /upload to do chunking + calling service B and saving files now its just 
# a separate func so BackgroundTasks can run it in background, the main addition is it updates jobs[job_id]

async def process_in_background(job_id: str, text: str, filename:str):

    jobs[job_id]["status"] = "processing"

    chunks = split_into_chunks(text, chunk_size= 200)
    jobs[job_id]["total_chunks"] = len(chunks)

    summaries = []

    # NEW: asyncio.gather runs ALL chunk calls at the same time (parallel),
    # instead of waiting for each one to finish before starting the next.
    # return_exceptions=True means if one chunk fails, the others still finish.

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [call_service_b(client, chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # this chunk failed- log it and add placeholder so we dont lose whole job
            logger.error(f"Chunk {i} failed", extra = {"error": repr(result)})
            summaries.append({
                "chunk_index": i,
                "summary": f"[Error processing chunk {i}]",
                "word_count":0
            })
        else:
            summaries.append(result)
        
        jobs[job_id]["completed_chunks"] = i + 1  # live prgress : update after each chunk

    # this is from old /upload
    result =  {
        "file_name" : filename,
        "total_chunks": len(summaries),
        "summaries": summaries
    }


    # save to outputs folder 

    # Get project root (parent of SERVICE_A)
    BASE_DIR = Path(__file__).resolve().parent.parent
    # Define outputs folder in project root
    output_dir = BASE_DIR / "outputs"
    output_dir.mkdir(exist_ok=True)
    # Create output file path
    output_path = output_dir / f"{filename.replace('.txt', '')}_summary.json"
    # save json
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)


    # saving final code in job so /status can return it
    jobs[job_id]["summaries"] = summaries
    jobs[job_id]["status"] = "completed"
    logger.info(f"Job {job_id} completed")

@app.get("/health")
async def health():
    logger.info("App A is running")
    return{
        "Status": "Healthy",
        "Service": "ingestion-serive"
    }

# added BackgroundTask parameter, everything else is same
@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks , file: UploadFile = File(...)):

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
    

    # create unique id for this job
    job_id = str(uuid.uuid4())

    # registering the job in our dict before starting it,
    # so that /status can find it immediately even before processing starts

    jobs[job_id] = {
        "status": "queued",
        "file_name": file.filename,
        "total_chunks": 0,
        "completed_chunks": 0,
        "summaries": []
    }

    # now before we did the work right here (which mad ethe user wait ),
    # we hand it to fastapis BAckgroundTasks
    # fastapi will return our response first, Then run this func

    background_tasks.add_task(process_in_background, job_id, text, file.filename)

    logger.info(f"job {job_id} queued for file {file.filename}")

    # return immediately with just job_id
    return {
        "job_id" : job_id,
        "message": "File accepted! Processing in background",
        "check_status_at": f"/status/{job_id}"
    }





    
#     chunks = split_into_chunks(text, chunk_size = 200)
#     summaries = []

#     async with httpx.AsyncClient(timeout=30.0) as client:
#         for chunk in chunks:
#             try:
# #                response = await client.post(APP_B_URL, json=chunk)      when i wasnt using retry connection logic 
# #                response.raise_for_status()
#                 result_chunk = await call_service_b(client, chunk)
#                 summaries.append(result_chunk)
#             except httpx.RequestError as e:
#                 logger.error("Service B is unreachable",
#                              extra={
#                                  "error": str(e),
#                                  "target_url": f"{APP_B_URL}/upload"
#                              })
#                  # Service B is unreachable (network error, connection refused, etc.)
#                 raise HTTPException(
#                     status_code=503,
#                     detail=f"Service B is unreachable: {str(e)}"
#                 )
#             except httpx.HTTPStatusError as e:
#                 logger.error("Service B returned error",
#                              extra={
#                                  "error": str(e),
#                                  "target_url": f"{APP_B_URL}/upload"
#                              })
#                 # Service B returned an error status code
#                 raise HTTPException(
#                     status_code=502,
#                     detail=f"Service B returned error: {e.response.status_code}"
#                 )
#             except Exception as e :
#                 logger.error(f"Unexpected error processing chunk {chunk['chunk_index']}",
#                              extra={
#                                  "error": str(e),
#                                  "target_url": f"{APP_B_URL}/upload"
#                              })
#                 # Catch-all for unexpected errors
#                 raise HTTPException(
#                     status_code=500,
#                     detail= f"Unexpected error processing chunk {chunk['chunk_index']}: {str(e)}"
#                 )

#     result =  {
#         "file_name" : file.filename,
#         "total_chunks": len(summaries),
#         "summaries": summaries
#     }


#     # save to outputs folder 

#     # Get project root (parent of SERVICE_A)
#     BASE_DIR = Path(__file__).resolve().parent.parent
#     # Define outputs folder in project root
#     output_dir = BASE_DIR / "outputs"
#     output_dir.mkdir(exist_ok=True)
#     # Create output file path
#     output_path = output_dir / f"{file.filename.replace('.txt', '')}_summary.json"
#     # save json
#     with open(output_path, 'w') as f:
#         json.dump(result, f, indent=2)

#     return result



# new status endpint
@app.get("/status/{job_id}")
async def get_status(job_id:str):

    if job_id not in jobs:
        raise HTTPException(status_code = 404, detail = f"Job '{job_id}' not found")
    
    job = jobs[job_id]

    # always return status+ progress
    response = {
        "job_id": job_id,
        "status": job["status"],            # "queued" / "processing" / "completed"
        "file_name": job["file_name"],
        "completed_chunks": job["completed_chunks"],
        "total_chunks": job["total_chunks"]
    }   

    # olny attach summaries when the job is done

    if job["status"] == "completed":
        response["summaries"] = job["summaries"]

    return response






