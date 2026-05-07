import os
# Disable SSL verification for Hugging Face on proxy/firewall networks
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

import torch
# Optimize PyTorch CPU Threads to prevent thrashing
# 3 threads per task * 4 tasks running concurrently = 12 active threads (perfect for i5-1334U)
torch.set_num_threads(3)

from transformers import pipeline
import PyPDF2
import base64
import io
import matplotlib.pyplot as plt
import concurrent.futures

class LegalDocumentAnalyzer:
    def __init__(self):
        # Initialize the model lazily to save resources on startup
        self.model_name = "google/flan-t5-large"
        self.summarizer = None
        
    def _load_model(self):
        if self.summarizer is None:
            print(f"Loading {self.model_name}...")
            # Use CPU or GPU depending on availability
            device = 0 if torch.cuda.is_available() else -1
            self.summarizer = pipeline("text2text-generation", model=self.model_name, device=device)
            print("Model loaded.")

    def extract_text(self, file_path):
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        return text

    def chunk_text(self, text, max_words=200, overlap=30):
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + max_words])
            chunks.append(chunk)
            i += (max_words - overlap)
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
        
        print(f"\n======================================")
        print(f"Processing {len(chunks)} chunks in PARALLEL...")
        print(f"======================================\n")

        def process_chunk(chunk_data):
            idx, chunk = chunk_data
            print(f"--> [STARTED] Chunk {idx+1}/{len(chunks)} is generating...")
            
            # Reverted back to 5 separate independent prompts for MAXIMUM QUALITY
            prompts = [
                ("summary", f"Summarize the following legal text in very simple, basic terminology that any normal person can understand. Text: {chunk}"),
                ("risk", f"Identify any potential legal or financial risks or penalties in this text. If none, output exactly 'None'. Text: {chunk}"),
                ("ob", f"Identify any obligations, duties, or requirements placed on the parties in this text. If none, output exactly 'None'. Text: {chunk}"),
                ("fin", f"Extract any financial terms, payments, monetary values, or amounts mentioned in this text. If none, output exactly 'None'. Text: {chunk}"),
                ("complex", f"Extract any hard-to-understand or complex legal terms from this text, and explain their significance in simple words. If none, output exactly 'None'. Text: {chunk}")
            ]

            results = {}
            # We run these 5 prompts sequentially for this specific chunk, 
            # while the ThreadPoolExecutor runs other chunks simultaneously
            for p_type, prompt in prompts:
                res = self.summarizer(prompt, max_new_tokens=150, do_sample=False)[0]['generated_text']
                results[p_type] = res
                
            print(f"<-- [FINISHED] Chunk {idx+1}/{len(chunks)} is complete!")
            return idx, results

        unordered_summaries = {}
        
        # Use ThreadPoolExecutor to run MULTIPLE CHUNKS AT ONCE
        # max_workers=4 means 4 chunks are being processed at the exact same time
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            chunk_data_list = [(i, chunk) for i, chunk in enumerate(chunks)]
            futures = [executor.submit(process_chunk, c) for c in chunk_data_list]
            
            for future in concurrent.futures.as_completed(futures):
                idx, res = future.result()
                
                unordered_summaries[idx] = res["summary"]
                
                if res["risk"].lower() != 'none' and len(res["risk"]) > 5: 
                    all_risks.append(res["risk"])
                if res["ob"].lower() != 'none' and len(res["ob"]) > 5: 
                    all_obligations.append(res["ob"])
                if res["fin"].lower() != 'none' and len(res["fin"]) > 3: 
                    all_financial.append(res["fin"])
                if res["complex"].lower() != 'none' and len(res["complex"]) > 5: 
                    all_complex_terms.append(res["complex"])
                    
        # Reconstruct summaries in the correct chronological order of the document
        summaries = []
        for i in range(len(chunks)):
            if i in unordered_summaries and len(unordered_summaries[i]) > 10:
                summaries.append(unordered_summaries[i])
                
        # Clean up duplicates roughly while preserving order
        def remove_dups(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]
            
        all_risks = remove_dups(all_risks)
        all_obligations = remove_dups(all_obligations)
        all_financial = remove_dups(all_financial)
        all_complex_terms = remove_dups(all_complex_terms)
        
        # Combine the simple summaries into one elaborate summary
        final_summary = " ".join(summaries)
        
        # Append the required string
        final_summary += f"\n\nDocument processed successfully. Total word count: {word_count}. Chunks analyzed: {len(chunks)}."
        
        # Generate chart
        chart_base64 = self.generate_chart(len(all_risks), len(all_obligations), len(all_financial), len(all_complex_terms))
        
        return {
            "summary": final_summary,
            "risks": all_risks if all_risks else ["No specific risks identified."],
            "obligations": all_obligations if all_obligations else ["No specific obligations identified."],
            "financial_terms": all_financial if all_financial else ["No financial terms identified."],
            "complex_terms": all_complex_terms if all_complex_terms else ["No complex legal terms identified."],
            "chart": chart_base64
        }
        
    def generate_chart(self, risk_count, ob_count, fin_count, comp_count):
        # Create a pie chart
        labels = ['Risks', 'Obligations', 'Financial Terms', 'Complex Terms']
        sizes = [risk_count, ob_count, fin_count, comp_count]
        
        # If all 0, make it equal so chart doesn't break
        if sum(sizes) == 0:
            sizes = [1, 1, 1, 1]
            labels = ['No Risks', 'No Obligations', 'No Financial Terms', 'No Complex Terms']
            
        colors = ['#e07a5f', '#81b29a', '#f2cc8f', '#3d405b']
        explode = (0.1, 0, 0, 0)
        
        plt.figure(figsize=(6, 6))
        # Ensure texts are legible for subtle UI (dark grey text)
        plt.rcParams.update({'font.size': 12, 'text.color': '#333333', 'axes.labelcolor': '#333333'})
        
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=140, textprops={'color':"#333333"})
        plt.axis('equal')
        plt.title("Distribution of Extracted Entities", color='#333333')
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{img_str}"
