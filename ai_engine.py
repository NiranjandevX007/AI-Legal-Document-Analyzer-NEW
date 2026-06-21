import os
import io
import re
import json
import base64
import matplotlib.pyplot as plt
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai

class LegalDocumentAnalyzer:
    def __init__(self):
        self.model_path = "./models/Phi-3-mini-4k-instruct-q4.gguf"
        self.llm = None
        self.document_text = None  # stored after each analysis for chatbot grounding
        
    def _load_model(self):
        if self.llm is None:
            print("Loading LegalLens AI Engine...")

            genai.configure(
               api_key=os.getenv("GEMINI_API_KEY")
        )

            self.llm = genai.GenerativeModel(
                "gemini-2.5-flash"
        )

            print("LegalLens AI Engine loaded successfully.")

    def extract_text(self, file_path):
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF with pdfplumber: {str(e)}")
        return text

    def chunk_text(self, text):
        try:
            # Smart sentence-aware chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000, # Approx 600-800 words for much faster processing
                chunk_overlap=300,
                length_function=len,
                is_separator_regex=False,
            )
            return text_splitter.split_text(text)
        except Exception as e:
            print(f"Warning: Smart chunking failed ({e}), falling back to basic split.")
            words = text.split()
            chunks = []
            i = 0
            while i < len(words):
                chunk = " ".join(words[i:i + 400])
                chunks.append(chunk)
                i += 350
            return chunks

    def cap_chunks(self, chunks, max_chunks=5):
        """Merge adjacent chunks until count is at most max_chunks."""
        if len(chunks) <= max_chunks:
            return chunks
        print(f"[CHUNK CAP] {len(chunks)} raw chunks → merging to max {max_chunks}")
        while len(chunks) > max_chunks:
            # Merge the adjacent pair with the smallest combined size
            best = min(range(len(chunks) - 1),
                       key=lambda i: len(chunks[i]) + len(chunks[i + 1]))
            chunks = chunks[:best] + [chunks[best] + '\n\n' + chunks[best + 1]] + chunks[best + 2:]
        print(f"[CHUNK CAP] Final chunk count: {len(chunks)}")
        return chunks

    def analyze_document(self, file_path):
        self._load_model()
        text = self.extract_text(file_path)
        if not text.strip():
            raise Exception("No text could be extracted from the PDF.")
        self.document_text = text

        chunks = self.chunk_text(text)
        chunks = self.cap_chunks(chunks)
        word_count = len(text.split())
        
        all_risks = []
        all_obligations = []
        all_financial = []
        all_complex_terms = []
        all_clauses = []
        
        print(f"\n======================================")
        print(f"Processing {len(chunks)} smart chunks sequentially...")
        print(f"======================================\n")

        unordered_summaries = {}
        
        for idx, chunk in enumerate(chunks):
            print(f"--> [STARTED] Chunk {idx+1}/{len(chunks)} is generating...")
            
            prompt = (
                f"<|system|>\n"
                f"You are a highly accurate AI legal document analyst specializing in insurance policies, contracts, "
                f"and formal legal documents.\n\n"
                f"Extract meaningful information in a clear, professional manner.\n"
                f"IMPORTANT INSTRUCTIONS:\n"
                f"- Return 'None' if information is missing.\n"
                f"- Extract ALL material risks (typically 4-8 per document). Cover: exclusions, waiting periods, co-pay clauses, deductibles, claim restrictions, documentation requirements, cancellation risks, sub-limits, coverage caps, premium revision clauses, non-disclosure consequences. Do NOT skip a risk just because it is common.\n"
                f"- Format EVERY risk EXACTLY as: [Severity] Risk Title — One-sentence explanation. Example: [High] Pre-existing Disease Waiting Period — Claims may not be covered during the initial waiting period.\n"
                f"- Extract ONLY the top 1-3 most important obligations. Ignore minor procedural ones.\n"
                f"- Extract ONLY 1 or 2 extremely rare, highly complex legal jargon terms per section. If the terms are standard or easily understood by an average adult, you MUST return 'None' for Complex Terms.\n"
                f"- Do NOT use [High/Medium/Low] badges for Obligations. Only use them for Risks.\n"
                f"- Categorize EVERY clause with a Category badge like: [Payment] Clause text, [Termination] Clause text, [Liability] Clause text, or [Insurance] Clause text.\n"
                f"- For Financial items: extract ONLY entries with actual monetary significance — premiums, coverage limits, sum insured, deductibles, co-pay percentages, claim limits, IDV, penalties, discounts, refunds, minimum retained amounts. SKIP generic descriptions with no specific number or percentage. Format EXACTLY as: Title | Exact amount or % (or N/A if not stated) | One-sentence explanation.\n\n"
                f"Return EXACTLY in this format. DO NOT use brackets [] except for Severity and Category badges:\n\n"
                f"Summary:\n"
                f"- <Detailed summary>\n\n"
                f"Risks:\n"
                f"- [Severity] <Risk Title> — <One-sentence explanation of the risk>\n\n"
                f"Obligations:\n"
                f"- <Description of obligation>\n\n"
                f"Financial:\n"
                f"- <Title> | <Exact amount or percentage, or N/A> | <One-sentence explanation>\n\n"
                f"Clauses:\n"
                f"- [Category] <Description of clause>\n\n"
                f"Complex Terms Explained:\n"
                f"- <Term explanation>\n"
                f"<|end|>\n"
                f"<|user|>\n"
                f"Analyze the following legal text:\n\n"
                f"{chunk}\n"
                f"<|end|>\n"
                f"<|assistant|>\n"
            )

            try:
                response=self.llm.generate_content(prompt)
                output_text = response.text.strip()
                print("\n===== AI OUTPUT =====")
                print(output_text)
                print("=========================\n")
            except Exception as e:
                print(f"Error during LLM generation for chunk {idx+1}: {e}")
                output_text = ""

            # Robust Parser
            # Force newlines before ANY badge to completely break apart squashed text
            output_text = re.sub(r'\s*(\[.*?\])', r'\n\1', output_text)
            
            current_key = None
            for line in output_text.split('\n'):
                clean_line = line.replace('*', '').strip()
                if not clean_line: continue
                line_lower = clean_line.lower()
                
                # Route by badge TYPE only — prevents cross-category contamination
                badge_search = re.search(r'\[([^\]]+)\]', clean_line)
                if badge_search:
                    badge_type = badge_search.group(1).strip().upper()
                    if badge_type in ('HIGH', 'MEDIUM', 'LOW'):
                        all_risks.append(clean_line)
                        continue
                    if badge_type in ('PAYMENT', 'TERMINATION', 'LIABILITY', 'INSURANCE',
                                      'CONFIDENTIALITY', 'ROOM RENT', 'SUB-LIMIT',
                                      'EXCLUSION', 'WAITING PERIOD', 'CO-PAY', 'OTHER'):
                        all_clauses.append(clean_line)
                        continue
                    # Unknown badge: fall through to current_key routing

                # Standard header parsing
                if line_lower.startswith('summary:'):
                    current_key = 'summary'
                    text_after = clean_line.split(':', 1)[1].strip()
                    if text_after and text_after.lower() != 'none':
                        unordered_summaries[idx] = unordered_summaries.get(idx, "") + text_after + " "
                elif line_lower.startswith('risks:') or line_lower.startswith('risk:'):
                    current_key = 'risk'
                elif line_lower.startswith('obligations:') or line_lower.startswith('obligation:'):
                    current_key = 'ob'
                elif line_lower.startswith('financial:') or line_lower.startswith('financials:'):
                    current_key = 'fin'
                elif line_lower.startswith('clauses:') or line_lower.startswith('clause:'):
                    current_key = 'clause'
                elif line_lower.startswith('complex:') or line_lower.startswith('complex terms'):
                    current_key = 'complex'
                elif current_key and clean_line.lower() not in ['none', 'none.']:
                    # Continuation lines (usually bullet points starting with "- ")
                    if clean_line == "-": continue
                    clean_line = clean_line.lstrip('- ').strip()
                    if not clean_line: continue
                    
                    if current_key == 'summary': unordered_summaries[idx] = unordered_summaries.get(idx, "") + clean_line + " "
                    elif current_key == 'risk': all_risks.append(clean_line)
                    elif current_key == 'ob': all_obligations.append(clean_line)
                    elif current_key == 'fin': all_financial.append(clean_line)
                    elif current_key == 'clause': all_clauses.append(clean_line)
                    elif current_key == 'complex': all_complex_terms.append(clean_line)
                    
            print(f"<-- [FINISHED] Chunk {idx+1}/{len(chunks)}")
            
        # Reconstruct summaries
        raw_summaries = []
        for i in range(len(chunks)):
            if i in unordered_summaries and len(unordered_summaries[i]) > 10:
                raw_summaries.append(unordered_summaries[i])
        
        # 1. FINAL GLOBAL SUMMARY (Disabled for speed, using simple concatenation)
        print("--> Stitching together chunk summaries...")
        final_summary = " ".join(raw_summaries)
        
        # Case-insensitive deduplication to catch near-duplicate extractions
        def remove_dups(seq):
            seen = set()
            result = []
            for x in seq:
                if not x:
                    continue
                key = x.strip().lower()
                if key not in seen:
                    seen.add(key)
                    result.append(x)
            return result
            
        all_risks         = remove_dups(all_risks)
        all_obligations   = remove_dups(all_obligations)
        all_financial     = remove_dups(all_financial)
        all_complex_terms = remove_dups(all_complex_terms)
        all_clauses       = remove_dups(all_clauses)

        # Semantic dedup: one Gemini call to collapse near-duplicates across chunks
        total = (len(all_risks) + len(all_obligations) + len(all_financial)
                 + len(all_complex_terms) + len(all_clauses))
        if total > 1:
            print("--> [DEDUP] Running semantic deduplication across all categories...")
            try:
                deduped = self._semantic_dedup(
                    all_risks, all_obligations, all_financial,
                    all_clauses, all_complex_terms
                )
                all_risks         = deduped.get('risks',          all_risks)
                all_obligations   = deduped.get('obligations',     all_obligations)
                all_financial     = deduped.get('financial_terms', all_financial)
                all_clauses       = deduped.get('clauses',         all_clauses)
                all_complex_terms = deduped.get('complex_terms',   all_complex_terms)
                print(f"[DEDUP] Done. Risks:{len(all_risks)} Obl:{len(all_obligations)} "
                      f"Fin:{len(all_financial)} Cl:{len(all_clauses)} Cx:{len(all_complex_terms)}")
            except Exception as e:
                print(f"[DEDUP] Semantic dedup skipped ({e}) — using basic dedup only.")

        # Executive Summary
        executive = {}
        print("--> [EXEC] Generating executive summary...")
        try:
            executive = self._generate_executive_summary(final_summary, all_risks, all_financial)
            print(f"[EXEC] Rating: {executive.get('rating', '?')}")
        except Exception as e:
            print(f"[EXEC] Executive summary skipped ({e}) — computing algorithmically.")
            high_count = sum(1 for r in all_risks if '[high]' in r.lower())
            total_risks = len(all_risks)
            if high_count == 0 and total_risks <= 2:
                rating = 'Excellent'
            elif high_count <= 1 and total_risks <= 4:
                rating = 'Good'
            elif high_count <= 2:
                rating = 'Average'
            else:
                rating = 'Poor'
            biggest = ''
            for r in all_risks:
                if '[high]' in r.lower():
                    biggest = re.sub(r'^\[[^\]]+\]\s*', '', r).split('—')[0].strip()[:90]
                    break
            if not biggest and all_risks:
                biggest = re.sub(r'^\[[^\]]+\]\s*', '', all_risks[0]).split('—')[0].strip()[:90]
            executive = {
                'rating': rating,
                'key_strength': 'Comprehensive coverage identified in this policy.',
                'biggest_risk': biggest or 'Review exclusions and waiting period clauses.',
            }

        # Charts
        chart_base64 = self.generate_chart(len(all_risks), len(all_obligations), len(all_financial), len(all_complex_terms))
        severity_chart_base64 = self.generate_severity_chart(all_risks)

        return {
            "metadata": f"Document processed. Word count: {word_count}. Chunks: {len(chunks)}.",
            "summary": final_summary,
            "executive": executive,
            "risks": all_risks if all_risks else ["No specific risks identified."],
            "obligations": all_obligations if all_obligations else ["No specific obligations identified."],
            "financial_terms": all_financial if all_financial else ["No financial terms identified."],
            "clauses": all_clauses if all_clauses else ["No specific clauses identified."],
            "complex_terms": all_complex_terms if all_complex_terms else ["No complex legal terms identified."],
            "chart": chart_base64,
            "severity_chart": severity_chart_base64
        }
        
    def _generate_executive_summary(self, summary, risks, financial_terms):
        """Quick Gemini call to produce an overall rating, key strength, and biggest risk."""
        high_risks = [r for r in risks if '[high]' in r.lower()]
        brief = {
            "summary_snippet": summary[:600],
            "high_risks": high_risks[:3],
            "total_risk_count": len(risks),
            "financial_term_count": len(financial_terms),
        }
        prompt = (
            "You are a legal document rating assistant.\n\n"
            "Based on the analysis below, produce:\n"
            "1. rating: Exactly one of — Excellent, Good, Average, Poor\n"
            "   (Excellent = minimal risks, broad coverage; Poor = many high-severity risks, heavy exclusions)\n"
            "2. key_strength: One sentence, ≤12 words, describing the best aspect of this document.\n"
            "3. biggest_risk: One sentence, ≤12 words, describing the single most critical concern.\n\n"
            "Return ONLY valid JSON with keys: rating, key_strength, biggest_risk. No markdown, no explanation.\n\n"
            f"Analysis:\n{json.dumps(brief, ensure_ascii=False, indent=2)}"
        )
        response = self.llm.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith('```'):
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        result = json.loads(raw)
        if not all(k in result for k in ('rating', 'key_strength', 'biggest_risk')):
            raise ValueError("Missing keys in executive summary response")
        return result

    def _semantic_dedup(self, risks, obligations, financial, clauses, complex_terms):
        """Single Gemini call to semantically deduplicate all five category lists.

        Gemini understands paraphrased duplicates that case-insensitive exact
        matching misses. Raises on parse failure so the caller can fall back.
        """
        data = {
            "risks":          risks,
            "obligations":    obligations,
            "financial_terms": financial,
            "clauses":        clauses,
            "complex_terms":  complex_terms,
        }

        prompt = (
            "You are a legal document deduplication assistant.\n\n"
            "The JSON below contains items extracted from MULTIPLE CHUNKS of the same document. "
            "Some items are exact duplicates; others convey the same information in different words "
            "(semantic duplicates). A few may be genuinely distinct and must both be kept.\n\n"
            "Rules:\n"
            "1. Remove exact duplicates.\n"
            "2. Remove semantic duplicates — items that describe the same fact, risk, clause, or term "
            "even when worded differently. Keep the MOST DETAILED / LONGEST version.\n"
            "3. NEVER merge two items into a new sentence. Only choose which existing items to keep.\n"
            "4. Preserve all badge prefixes exactly: [High], [Medium], [Low], [Payment], etc.\n"
            "5. Preserve pipe | delimiters in financial_terms items exactly.\n"
            "6. Keep items that are genuinely distinct, even if they share a few words.\n"
            "7. Return ONLY valid JSON with the same five keys. No markdown fences, no explanation.\n\n"
            f"Input:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        )

        response = self.llm.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        result = json.loads(raw)

        required = ("risks", "obligations", "financial_terms", "clauses", "complex_terms")
        for key in required:
            if key not in result or not isinstance(result[key], list):
                raise ValueError(f"Dedup response missing or invalid key: {key}")

        return result

    def _generate_global_summary(self, raw_text):
        if not raw_text or len(raw_text) < 100:
            return raw_text
            
        prompt = (
            f"<|user|>\n"
            f"You are a master legal summarizer. I have extracted summaries from various parts of a legal contract. "
            f"Please rewrite them into ONE cohesive, professional, flowing executive summary. Remove any repetition.\n\n"
            f"Raw Summaries:\n{raw_text}\n<|end|>\n"
            f"<|assistant|>\n"
        )
        try:
            response=self.llm.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Global summary failed: {e}")
            return raw_text

    def generate_chart(self, risk_count, ob_count, fin_count, comp_count):
        labels = ['Risks', 'Obligations', 'Financial', 'Complex Terms']
        sizes = [risk_count, ob_count, fin_count, comp_count]
        if sum(sizes) == 0:
            sizes, labels = [1, 1, 1, 1], ['No Risks', 'No Obligations', 'No Financial', 'No Complex']
        colors = ['#e07a5f', '#81b29a', '#f2cc8f', '#3d405b']
        explode = (0.1, 0, 0, 0)
        
        plt.figure(figsize=(6, 6))
        plt.rcParams.update({'font.size': 12, 'text.color': '#333333', 'axes.labelcolor': '#333333'})
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140, textprops={'color':"#333333"})
        plt.axis('equal')
        plt.title("Entity Distribution", color='#333333')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{img_str}"
        
    def generate_severity_chart(self, risks):
        high, med, low = 0, 0, 0
        for r in risks:
            rl = r.lower()
            if '[high]' in rl: high += 1
            elif '[medium]' in rl: med += 1
            elif '[low]' in rl: low += 1
            else: med += 1 # Default
            
        labels = ['High Severity', 'Medium Severity', 'Low Severity']
        counts = [high, med, low]
        if sum(counts) == 0:
            return ""
            
        plt.figure(figsize=(6, 4))
        plt.rcParams.update({'font.size': 10, 'text.color': '#333333', 'axes.labelcolor': '#333333'})
        bars = plt.bar(labels, counts, color=['#e07a5f', '#f2cc8f', '#81b29a'])
        plt.title("Risk Severity Analysis", color='#333333', pad=15)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, int(yval), ha='center', va='bottom', color='#333333', fontweight='bold')
            
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return f"data:image/png;base64,{img_str}"
