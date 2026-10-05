from fastapi import FastAPI

app = FastAPI(title="Local GenAI Data Assistant")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Local GenAI Data Assistant API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
