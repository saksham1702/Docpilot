import modal

# Define the image with necessary dependencies
image = (
    modal.Image.debian_slim()
    .pip_install("sentence-transformers", "torch", "fastapi")
)

app = modal.App("docpilot-embedder", image=image)

with image.imports():
    from sentence_transformers import SentenceTransformer

@app.cls(min_containers=1)
class Model:
    @modal.enter()
    def load_model(self):
        print(" Loading model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print(" Model loaded!")
    
    @modal.method()
    def embed_text(self, text: str):
        return self.model.encode(text).tolist()

    @modal.fastapi_endpoint(method="POST")
    def embedding_webhook(self, item: dict):
        text = item.get("text", "")
        if not text:
            return {"error": "No text provided"}
        
        vector = self.embed_text.local(text)
        return {"embedding": vector}

