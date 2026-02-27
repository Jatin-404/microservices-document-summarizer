from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import ollama
from shared.logger import setup_logging
logger = setup_logging("app-b")

app = FastAPI()

class ChunkRequest(BaseModel):
    chunk_index: int = Field(..., ge=0)
    text: str

    @field_validator("text")
    def text_must_not_be_empty(cls,value):
        if not value.strip():
            raise ValueError("Text can't be empty")
        return value

class ChunkResponse(BaseModel):
    chunk_index: int
    summary: str
    word_count: int

async def generate_summary(text: str) -> str:
    logger.info("Calling LLM now...")
    try:
        response = ollama.chat(
            model= "llama3.2:1b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a summarization engine. "
                    "Return ONLY one concise sentence summarizing the text. "
                    "Do NOT include explanations, prefixes, or extra text."
                },
                {
                    'role': "user",
                    "content":  text
                }
            ],
            options={
                'temperature':0.3, # Lower = more focused
                'num_predict':50   # Max tokens in response
            }
        )
        summary = response['message']['content'].strip()
        return summary
    except Exception as e:
        logger.error("Ollama error, falling back to first sentence",
                     extra={
                         "error": str(e)
                     })
        # Fallback to first sentence if Ollama fails
        sentences = text.split(".")
        return sentences[0].strip() if sentences else text.strip()




@app.get("/health")
async def health():
    logger.info("Health check called")
                
    return {
        "Status": "Healthy",
        "Service": "processor-service"
    }

@app.post("/process", response_model=ChunkResponse)
async def process_chunk(data: ChunkRequest):
    
    try:
        summary = await generate_summary(data.text)

        return ChunkResponse(
            chunk_index= data.chunk_index,
            summary=summary,
            word_count=len(data.text.split())
        )
    except Exception as e:
        logger.error("Error processing chunk",
                     extra={
                         "error": str(e),
                         "target_endpoint": f"/process"
                     })
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chunk : {str(e)} "
        )
