from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import uvicorn
import ollama

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
    print("Calling LLM now...")
    try:
        response = ollama.chat(
            model= "llama3.2:1b",
            messages=[
                {
                    "role": "system",
                    "content": 'You are a helpful assistant that creates concise summaries. Summarize the given text in one clear sentence.'
                },
                {
                    'role': "user",
                    "content":  f'Summarize this text in one sentence:\n\n{text}'
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
        # Fallback to first sentence if Ollama fails
        print(f"Ollama error: {e}, falling back to first sentence")
        sentences = text.split(".")
        return sentences[0].strip() if sentences else text.strip()




@app.get("/health")
async def health():
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
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chunk : {str(e)} "
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)