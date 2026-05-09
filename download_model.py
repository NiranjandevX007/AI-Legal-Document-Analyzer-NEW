import os
from huggingface_hub import hf_hub_download

os.environ['HF_HUB_DISABLE_CERT_VERIFICATION'] = '1'

print("Downloading Phi-3-mini-4k-instruct-q4.gguf...")
try:
    path = hf_hub_download(
        repo_id="microsoft/Phi-3-mini-4k-instruct-gguf", 
        filename="Phi-3-mini-4k-instruct-q4.gguf", 
        local_dir="./models"
    )
    print(f"Successfully downloaded to {path}")
except Exception as e:
    print(f"Error downloading: {e}")
