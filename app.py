import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

from tasks import process_emails

app = FastAPI()

load_dotenv()

class Email(BaseModel):
    body: str
    subject: str
    from_email: str
    received_at: datetime

class PredictionRequest(BaseModel):
    emails: list[Email]

@app.post("/predict")
def predict(req: list[Email]):
    emails = [
        {
            "body": email.body,
            "subject": email.subject,
            "from_email": email.from_email,
            "received_at": email.received_at.isoformat()
                if isinstance(email.received_at, datetime)
                else email.received_at,
        }
        for email in req
    ]

    task = process_emails.delay(emails)

    return {
        "status": "queued",
        "task_id": task.id
    }

@app.get("/health")
def health():
    return {"result": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST"), port=os.getenv("PORT"))
