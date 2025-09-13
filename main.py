from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io, re
from typing import List
from fastapi.responses import JSONResponse

app = FastAPI(title="Adaptive Learning Starter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_bytes(data: bytes, filename: str) -> str:
    text = ""
    if filename.lower().endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(data))
            for p in reader.pages:
                text += p.extract_text() or ""
        except Exception:
            text = ""
    else:
        try:
            text = data.decode("utf-8")
        except:
            text = ""
    return re.sub(r"\s+", " ", text).strip()

def simple_quiz_from_text(text: str, n_questions: int = 5):
    import random, re
    sents = re.split(r'(?<=[.!?])\s+', text)
    candidates = []
    for s in sents:
        words = re.findall(r"\b[A-Za-z][A-Za-z']{5,}\b", s)
        proper = re.findall(r"\b[A-Z][a-z]{2,}\b", s)
        keywords = list(dict.fromkeys(words + proper))
        if keywords and len(s.split()) > 6:
            candidates.append((s, keywords))
    random.shuffle(candidates)
    quiz = []
    for sent, keywords in candidates[:n_questions]:
        key = keywords[0]
        question = sent.replace(key, "_", 1)
        distractors = []
        pool = [k for _, ks in candidates for k in ks if k != key]
        random.shuffle(pool)
        for d in pool[:3]:
            distractors.append(d)
        options = [key] + distractors
        random.shuffle(options)
        quiz.append({"question": question, "answer": key, "options": options})
    return quiz

class QuizRequest(BaseModel):
    text: str
    n_questions: int = 5

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    data = await file.read()
    text = extract_text_from_bytes(data, file.filename)
    if not text:
        return JSONResponse(status_code=400, content={"error": "Could not extract text."})
    return {"text": text[:5000]}

@app.post("/generate_quiz")
async def generate_quiz(req: QuizRequest):
    quiz = simple_quiz_from_text(req.text, req.n_questions)
    return {"quiz": quiz, "n_generated": len(quiz)}

@app.get("/")
def root():
    return {"msg": "Adaptive Learning Starter API running."}