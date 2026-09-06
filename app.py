import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from tasks import process_emails

app = FastAPI()

load_dotenv()

class Email(BaseModel):
    body: str
    subject: str
    from_email: str

class PredictionRequest(BaseModel):
    emails: list[Email]

@app.post("/predict")
def predict(req: list[Email]):

    emails = [
        {
            "body": email.body,
            "subject": email.subject,
            "from_email": email.from_email,
        }
        for email in req
    ]

    task = process_emails.delay(emails)

    return {
        "status": "queued",
        "task_id": task.id
    }

# @app.post(
#     "/predict",
# )
# def predict(req: list[Email], db: Session = Depends(get_db)):
#     for email in req:
#         # sentence = normalized_sentence(email.body)
#         result = predict_emotion(email.body, tokenizer, model)
#         result = json.loads(result)

#         items_iter = iter(result["probabilities"].items())

#         primary_emotion, _ = next(items_iter)
#         secondary_emotion, _ = next(items_iter)
#         primary_emotion = primary_emotion.lower()
#         secondary_emotion = secondary_emotion.lower()
#         compound_emotion = ""

#         if (primary_emotion == "joy" and secondary_emotion == "sadness") or (
#             primary_emotion == "sadness" and secondary_emotion == "joy"
#         ):
#             compound_emotion = "nostalgia"
#         elif (primary_emotion == "joy" and secondary_emotion == "disgust") or (
#             primary_emotion == "disgust" and secondary_emotion == "joy"
#         ):
#             compound_emotion = "intrigue"
#         elif (primary_emotion == "joy" and secondary_emotion == "fear") or (
#             primary_emotion == "fear" and secondary_emotion == "joy"
#         ):
#             compound_emotion = "surprise"
#         elif (primary_emotion == "joy" and secondary_emotion == "anger") or (
#             primary_emotion == "anger" and secondary_emotion == "joy"
#         ):
#             compound_emotion = "justice"
#         elif (primary_emotion == "sadness" and secondary_emotion == "disgust") or (
#             primary_emotion == "disgust" and secondary_emotion == "sadness"
#         ):
#             compound_emotion = "contempt"
#         elif (primary_emotion == "sadness" and secondary_emotion == "fear") or (
#             primary_emotion == "fear" and secondary_emotion == "sadness"
#         ):
#             compound_emotion = "anxiety"
#         elif (primary_emotion == "sadness" and secondary_emotion == "anger") or (
#             primary_emotion == "anger" and secondary_emotion == "sadness"
#         ):
#             compound_emotion = "betrayal"
#         elif (primary_emotion == "disgust" and secondary_emotion == "fear") or (
#             primary_emotion == "fear" and secondary_emotion == "disgust"
#         ):
#             compound_emotion = "repulsion"
#         elif (primary_emotion == "disgust" and secondary_emotion == "anger") or (
#             primary_emotion == "anger" and secondary_emotion == "disgust"
#         ):
#             compound_emotion = "aversion"
#         elif (primary_emotion == "fear" and secondary_emotion == "anger") or (
#             primary_emotion == "anger" and secondary_emotion == "fear"
#         ):
#             compound_emotion = "hate"

#         new_email = models.Email(
#             body=email.body,
#             subject=email.subject,
#             from_email=email.from_email,
#             emotion=primary_emotion,
#             secondary_emotion=secondary_emotion,
#             compound_emotion = compound_emotion,
#         )

#         db.add(new_email)

#         stats = (
#             db.query(models.EmailCount)
#             .filter(models.EmailCount.created_at == datetime.now(timezone.utc).today())
#             .first()
#         )

#         if not stats:
#             stats = models.EmailCount()
#             db.add(stats)
            
#         current_value = getattr(stats, primary_emotion, 0) or 0
#         setattr(stats, primary_emotion, current_value + 1)

#         current_value = getattr(stats, "sec_" + secondary_emotion, 0) or 0
#         setattr(stats, "sec_" + secondary_emotion, current_value + 1)

#         current_value = getattr(stats, compound_emotion, 0) or 0
#         setattr(stats, compound_emotion, current_value + 1)

#         db.commit()

#     return {"result": "ok"}


@app.get("/health")
def health():
    return {"result": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST"), port=os.getenv("PORT"))
