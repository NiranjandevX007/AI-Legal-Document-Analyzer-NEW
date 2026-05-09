import os
import io
import base64
import matplotlib.pyplot as plt
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_cpp import Llama

class LegalDocumentAnalyzer:
    def __init__(self):
        self.model_path = "./models/Phi-3-mini-4k-instruct-q4.gguf"
        self.llm = None
        
    def _load_model(self):
        if self.llm is None:
            print("Loading Phi-3-Mini (3.8B Parameters)...")
            try:
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=4096,
                    n_threads=10,
                    verbose=False
                )
                print("Model loaded successfully.")
            except Exception as e:
                raise Exception(f"Failed to load LLM: {str(e)}")

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
                chunk_size=2000, # Approx 400-500 words
                chunk_overlap=200,
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

    def analyze_document(self, file_path):
        self._load_model()
        text = self.extract_text(file_path)
        if not text.strip():
            raise Exception("No text could be extracted from the PDF.")
            
        chunks = self.chunk_text(text)
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
                f"- Extract ONLY the top 1-3 most critical risks and most important obligations. Ignore minor issues.\n"
                f"- Extract ONLY 1 or 2 extremely rare, highly complex legal jargon terms per section. If the terms are standard or easily understood by an average adult, you MUST return 'None' for Complex Terms.\n"
                f"- Classify EVERY risk with a Severity badge like: [High] Risk text, [Medium] Risk text, or [Low] Risk text.\n"
                f"- Categorize EVERY clause with a Category badge like: [Payment] Clause text, [Termination] Clause text, [Liability] Clause text, or [Insurance] Clause text.\n\n"
                f"Return EXACTLY in this format:\n\n"
                f"Summary:\n"
                f"- [Detailed summary]\n\n"
                f"Risks:\n"
                f"- [Severity] [Description of risk]\n\n"
                f"Obligations:\n"
                f"- [Description of obligation]\n\n"
                f"Financial:\n"
                f"- [Description of financial term]\n\n"
                f"Clauses:\n"
                f"- [Category] [Description of clause]\n\n"
                f"Complex Terms Explained:\n"
                f"- [Term explanation]\n"
                f"<|end|>\n"
                f"<|user|>\n"
                f"Analyze the following legal text:\n\n"
                f"{chunk}\n"
                f"<|end|>\n"
                f"<|assistant|>\n"
            )

            try:
                res = self.llm(prompt, max_tokens=800, temperature=0.1, stop=["<|end|>"], echo=False)
                output_text = res['choices'][0]['text'].strip()
            except Exception as e:
                print(f"Error during LLM generation for chunk {idx+1}: {e}")
                output_text = ""

            # Robust Parser
            current_key = None
            for line in output_text.split('\n'):
                clean_line = line.replace('*', '').strip()
                line_lower = clean_line.lower()
                
                if line_lower.startswith('summary:'):
                    current_key = 'summary'
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
                elif current_key and clean_line and clean_line.lower() not in ['none', 'none.']:
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
        
        # 1. FINAL GLOBAL SUMMARY
        print("--> Generating Final Global Summary...")
        final_summary = self._generate_global_summary(" ".join(raw_summaries))
        
        # Deduplication
        def remove_dups(seq):
            seen = set()
            return [x for x in seq if x and not (x in seen or seen.add(x))]
            
        all_risks = remove_dups(all_risks)
        all_obligations = remove_dups(all_obligations)
        all_financial = remove_dups(all_financial)
        all_complex_terms = remove_dups(all_complex_terms)
        all_clauses = remove_dups(all_clauses)
        
        # Charts
        chart_base64 = self.generate_chart(len(all_risks), len(all_obligations), len(all_financial), len(all_complex_terms))
        severity_chart_base64 = self.generate_severity_chart(all_risks)
        
        return {
            "metadata": f"Document processed. Word count: {word_count}. Chunks: {len(chunks)}.",
            "summary": final_summary,
            "risks": all_risks if all_risks else ["No specific risks identified."],
            "obligations": all_obligations if all_obligations else ["No specific obligations identified."],
            "financial_terms": all_financial if all_financial else ["No financial terms identified."],
            "clauses": all_clauses if all_clauses else ["No specific clauses identified."],
            "complex_terms": all_complex_terms if all_complex_terms else ["No complex legal terms identified."],
            "chart": chart_base64,
            "severity_chart": severity_chart_base64
        }
        
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
            res = self.llm(prompt, max_tokens=1000, temperature=0.2, stop=["<|end|>"], echo=False)
            return res['choices'][0]['text'].strip()
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
