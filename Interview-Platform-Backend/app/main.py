from fastapi import FastAPI
from app.api.interview import router as interview_router
app = FastAPI()

app.include_router(interview_router)


@app.get("/")
def health_check():
    return {"status": "running"}