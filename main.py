import os
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['HF_HUB_DISABLE_CERT_VERIFICATION'] = '1'

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import shutil
import warnings
import json
import re

warnings.filterwarnings("ignore")

from ai_engine import LegalDocumentAnalyzer

app = FastAPI(title="AI Legal Document Analyzer")

analyzer = LegalDocumentAnalyzer()

# Make sure static and uploads folders exist
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    file_path = f"uploads/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        results = analyzer.analyze_document(file_path)
        return results
    except Exception as e:
        print(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup uploaded file to save space
        if os.path.exists(file_path):
            os.remove(file_path)
class TranslationRequest(BaseModel):
    summary: str = ""
    metadata: str = ""
    complex_terms: list = []
    risks: list = []
    obligations: list = []
    financial_terms: list = []
    clauses: list = []


@app.post("/translate-kannada")
async def translate_kannada(req: TranslationRequest):
    analyzer._load_model()

    data = {
        "summary": req.summary,
        "metadata": req.metadata,
        "complex_terms": req.complex_terms,
        "risks": req.risks,
        "obligations": req.obligations,
        "financial_terms": req.financial_terms,
        "clauses": req.clauses,
    }

    prompt = f"""You are a legal translator. Translate all string values in the following JSON from English to Kannada.

Rules:
- Preserve all JSON keys exactly as-is. Do not translate keys.
- Preserve any badge prefixes in square brackets exactly as English (e.g. [High], [Medium], [Low], [Payment], [Termination], [Liability], [Insurance]) — translate only the text that comes after the badge.
- Return ONLY valid JSON with the same structure. No markdown fences, no explanations, nothing else.

Input JSON:
{json.dumps(data, ensure_ascii=False, indent=2)}
"""

    response = analyzer.llm.generate_content(prompt)
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        translated = json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation parsing failed: {e}")

    return translated


if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


