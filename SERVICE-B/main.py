from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import uvicorn

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


def extract_first_sentence(text: str) -> str:
    sentences = text.split(".")
    first_sentence = sentences[0].strip()
    return first_sentence
@app.get("/health")
async def health():
    return {
        "Status": "Healthy",
        "Service": "processor-service"
    }

@app.post("/process", response_model=ChunkResponse)
async def process_chunk(data: ChunkRequest):
    
    try:
        summary = extract_first_sentence(data.text)

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