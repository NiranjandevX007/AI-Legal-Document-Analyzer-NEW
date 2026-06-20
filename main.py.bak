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
    text: str


@app.post("/translate-kannada")
async def translate_kannada(req: TranslationRequest):

    prompt = f"""
Translate the following legal text into Kannada.

Rules:
- Keep the legal meaning unchanged.
- Return only Kannada text.
- Do not add explanations.

Text:
{req.text}
"""

    response = analyzer.llm.generate_content(prompt)

    return {
        "translated_text": response.text.strip()
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


