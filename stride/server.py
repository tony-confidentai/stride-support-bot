import os
import secrets

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Header, HTTPException
from openai import OpenAIError
from pydantic import BaseModel

from stride.bot import answer

app = FastAPI(title="Stride support bot")
TOKEN = os.environ["STRIDE_API_TOKEN"]


class ChatRequest(BaseModel):
    question: str
    source: str = "customer"


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat(body: ChatRequest, authorization: str = Header("")):
    if not secrets.compare_digest(authorization, f"Bearer {TOKEN}"):
        raise HTTPException(status_code=401, detail="Missing or wrong API token.")
    try:
        text, docs, tools_called = answer(body.question, source=body.source)
    except OpenAIError as error:
        # name the model error, so a failed eval run shows the cause
        raise HTTPException(status_code=503, detail=f"OpenAI unavailable: {type(error).__name__}")
    return {"answer": text, "sources": docs, "tools_called": tools_called}
