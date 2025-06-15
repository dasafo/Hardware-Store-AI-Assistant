from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hardware-Store-AI-Assistant is running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}