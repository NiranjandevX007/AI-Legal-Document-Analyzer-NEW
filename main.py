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
    executive: dict = {}

class ChatRequest(BaseModel):
    message: str = ""
    history: list = []


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
        "executive": req.executive,
    }

    prompt = f"""You are a legal translator. Translate all string values in the following JSON from English to Kannada.

Rules:
- Preserve all JSON keys exactly as-is. Do not translate keys.
- Preserve any badge prefixes in square brackets exactly as English (e.g. [High], [Medium], [Low], [Payment], [Termination], [Liability], [Insurance]) — translate only the text that comes after the badge.
- For financial_terms list items, preserve the pipe | delimiters exactly — they separate Title, Value, and Meaning fields. Translate only the text portions, not the pipe characters.
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


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    analyzer._load_model()

    context = analyzer.document_text[:30000] if analyzer.document_text else ""

    # Detect Kannada via Unicode block U+0C80–U+0CFF
    is_kannada = bool(re.search(r'[ಀ-೿]', req.message))

    # Build conversation history section from last 8 turns
    history_section = ""
    if req.history:
        lines = []
        for turn in req.history[-8:]:
            role = "User" if turn.get("role") == "user" else "LegalLens"
            content = str(turn.get("content", "")).strip()
            if content:
                lines.append(f"{role}: {content}")
        if lines:
            history_section = "\nPrevious conversation:\n" + "\n".join(lines) + "\n"

    doc_section = (
        f"\nUploaded Document:\n'''\n{context}\n'''\n"
        if context else "\n[No document uploaded — answer from general knowledge.]\n"
    )

    if is_kannada:
        lang_rules = (
            "- ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ. ಸರಳ, ಸ್ಪಷ್ಟ ಕನ್ನಡ ಬಳಸಿ.\n"
            "- ವಿಮೆ ಮತ್ತು ಕಾನೂನು ಪದಗಳನ್ನು ಕನ್ನಡದಲ್ಲಿ ಸ್ವಾಭಾವಿಕವಾಗಿ ವಿವರಿಸಿ.\n"
            "- ನಿರ್ದಿಷ್ಟ ಮೊತ್ತಗಳು ಮತ್ತು ಪಾಲಿಸಿ ಸಂಖ್ಯೆಗಳನ್ನು ಯಥಾವತ್ತಾಗಿ ಇರಿಸಿ.\n"
            "- ದಾಖಲೆಯಲ್ಲಿ ಸಿಗದಿದ್ದರೆ ಸಾಮಾನ್ಯ ಜ್ಞಾನ ಬಳಸಿ ಉತ್ತರಿಸಿ: "
            "'ದಾಖಲೆಯಲ್ಲಿ ಈ ಮಾಹಿತಿ ಸಿಗಲಿಲ್ಲ, ಆದರೆ ಸಾಮಾನ್ಯವಾಗಿ: ...'"
        )
    else:
        lang_rules = (
            "- Reply in English.\n"
            "- If not in the document: say 'I couldn't find that in the document, but generally: [your answer]'"
        )

    prompt = f"""You are LegalLens AI, an intelligent legal and insurance document advisor.

RESPONSE GUIDELINES:
1. DOCUMENT questions (about this specific policy/contract/clauses): Answer from the uploaded document; quote relevant sections.
2. GENERAL questions (legal/insurance concepts, definitions, how coverage works): Answer using your knowledge.
3. RECOMMENDATIONS / COMPARISONS / OPINIONS (should I buy, compare with others): Combine document analysis with general knowledge.
4. If not found in document but you know the answer: "I couldn't find that in the document, but generally: [answer]"
5. Only decline requests completely unrelated to legal, insurance, or financial matters.
6. CONCISENESS: Keep answers to 3-6 lines by default. Use bullet points instead of paragraphs. Only provide detailed multi-paragraph answers when the user explicitly asks ("explain in detail", "elaborate", "tell me more"). For recommendations, use a brief Pros/Cons bullet format.
{lang_rules}
{doc_section}{history_section}
Current question: {req.message}"""

    try:
        response = analyzer.llm.generate_content(prompt)
        answer = response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat API call failed: {e}")

    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


