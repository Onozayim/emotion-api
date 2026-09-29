from sqlalchemy import func
from models import SurveyTemplate, SurveyAnswer, Email, SurveyStatus

POSITIVE_EMOTIONS = {
    "joy",
    "love",
    "surprise",
}

NEUTRAL_EMOTIONS = {
    "intrigue",
    "nostalgia",
}

NEGATIVE_EMOTIONS = {
    "sadness",
    "anger",
    "fear",
    "disgust",
    "contempt",
    "anxiety",
    "betrayal",
    "repulsion",
    "aversion",
    "hate",
}


def get_user_emotion_distribution(db, email_address: str):

    effective_emotion = func.coalesce(
        Email.fixed_compound_emotion, Email.compound_emotion
    )

    results = (
        db.query(
            effective_emotion.label("emotion"), func.count(Email.id).label("count")
        )
        .filter(Email.from_email == email_address)
        .filter(effective_emotion.isnot(None))
        .group_by(effective_emotion)
        .all()
    )

    categories = {"positive": 0, "neutral": 0, "negative": 0}

    for emotion, count in results:
        category = get_emotion_category(emotion)
        categories[category] += count

    total = sum(categories.values())

    if total == 0:
        return {"positive": 0, "neutral": 0, "negative": 0}

    return {
        "positive": categories["positive"] / total,
        "neutral": categories["neutral"] / total,
        "negative": categories["negative"] / total,
    }


def get_dominant_category(distribution: dict) -> str:
    return max(distribution, key=distribution.get)


def get_emotion_category(emotion: str) -> str:
    emotion = emotion.lower()

    if emotion in POSITIVE_EMOTIONS:
        return "positive"

    if emotion in NEGATIVE_EMOTIONS:
        return "negative"

    return "neutral"


def create_or_update_survey_answer(db, email_address: str, emotion: str):
    distribution = get_user_emotion_distribution(db, email_address)

    category = get_dominant_category(distribution)

    survey_template = (
        db.query(SurveyTemplate).filter(SurveyTemplate.emotion == category).first()
    )

    if not survey_template:
        raise ValueError(f"No survey template found for category: {category}")

    survey_answer = (
        db.query(SurveyAnswer)
        .filter(SurveyAnswer.email == email_address)
        .filter(SurveyAnswer.responded_at.is_(None))
        .first()
    )

    if survey_answer:
        survey_answer.survey_id = survey_template.id
        survey_answer.last_activity_at = func.now()

        return survey_answer

    survey_answer = SurveyAnswer(
        email=email_address.strip(),
        survey_id=survey_template.id,
        answers=None,
        responded_at=None,
    )

    db.add(survey_answer)

    return survey_answer
