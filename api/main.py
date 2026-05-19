from fastapi import FastAPI
app = FastAPI(title="Pixel Orchestrator API")
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/devices")
def devices(): return {"devices": []}
