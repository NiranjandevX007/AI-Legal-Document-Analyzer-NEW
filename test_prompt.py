import os
from llama_cpp import Llama

llm = Llama(
    model_path="./models/Phi-3-mini-4k-instruct-q4.gguf",
    n_ctx=4096,
    n_threads=10,
    verbose=False
)

chunk = "The Lessee agrees to pay the Lessor a monthly rent of $5,000. Failure to pay within 30 days constitutes a material breach, incurring a 5% late fee and potential eviction. The Lessee shall indemnify the Lessor against all claims arising from hazardous activities."

prompt = (
    f"<|user|>\n"
    f"You are an expert legal analyst. Read the following legal text and extract these 5 elements exactly in this format using clear, grammatically perfect English:\n"
    f"Summary: [A clear, elaborate summary]\n"
    f"Risks: [Any legal/financial risks, or 'None']\n"
    f"Obligations: [Any duties/obligations, or 'None']\n"
    f"Financial: [Any financial terms/payments, or 'None']\n"
    f"Complex: [Any complex jargon explained simply, or 'None']\n\n"
    f"Legal Text:\n{chunk}<|end|>\n"
    f"<|assistant|>\n"
)

print("Evaluating...")
res = llm(prompt, max_tokens=300, temperature=0.1, stop=["<|end|>"], echo=False)
output_text = res['choices'][0]['text'].strip()

print("==== RAW OUTPUT ====")
print(output_text)
