import json

import models
from analyzer import predict_emotion
from celery_app import celery
from database import SessionLocal
from model_loader import model, tokenizer
from services.survey_service import create_or_update_survey_answer


@celery.task
def process_emails(emails):

    db = SessionLocal()

    try:
        for email in emails:

            result = predict_emotion(
                email["body"],
                tokenizer,
                model
            )

            result = json.loads(result)

            items_iter = iter(
                result["probabilities"].items()
            )

            primary_emotion, _ = next(items_iter)
            secondary_emotion, _ = next(items_iter)

            primary_emotion = primary_emotion.lower()
            secondary_emotion = secondary_emotion.lower()

            compound_emotion = get_compound_emotion(
                primary_emotion,
                secondary_emotion
            )

            new_email = models.Email(
                body=email["body"].strip(),
                subject=email["subject"].strip(),
                from_email=email["from_email"].strip(),
                emotion=primary_emotion.strip(),
                secondary_emotion=secondary_emotion.strip(),
                compound_emotion=compound_emotion.strip(),
                created_at=email["received_at"]
            )

            db.add(new_email)

            db.flush()

            create_or_update_survey_answer(
                db=db,
                email_address=email["from_email"],
                emotion=primary_emotion
            )

            stats = (
                db.query(models.EmailCount)
                .filter(
                    models.EmailCount.created_at == email["received_at"]
                )
                .first()
            )

            if not stats:
                stats = models.EmailCount(
                    created_at=email["received_at"]
                )
                db.add(stats)
                db.flush()

            # Primary emotion
            current_value = (
                getattr(stats, primary_emotion, 0) or 0
            )

            setattr(
                stats,
                primary_emotion,
                current_value + 1
            )

            # Secondary emotion
            secondary_field = "sec_" + secondary_emotion

            current_value = (
                getattr(stats, secondary_field, 0) or 0
            )

            setattr(
                stats,
                secondary_field,
                current_value + 1
            )

            # Compound emotion
            if compound_emotion:

                current_value = (
                    getattr(stats, compound_emotion, 0) or 0
                )

                setattr(
                    stats,
                    compound_emotion,
                    current_value + 1
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_compound_emotion(primary, secondary):

    emotions = {primary, secondary}

    combinations = {
        frozenset(["joy", "sadness"]): "nostalgia",
        frozenset(["joy", "disgust"]): "intrigue",
        frozenset(["joy", "fear"]): "surprise",
        frozenset(["joy", "anger"]): "justice",
        frozenset(["sadness", "disgust"]): "contempt",
        frozenset(["sadness", "fear"]): "anxiety",
        frozenset(["sadness", "anger"]): "betrayal",
        frozenset(["disgust", "fear"]): "repulsion",
        frozenset(["disgust", "anger"]): "aversion",
        frozenset(["fear", "anger"]): "hate",
    }

    return combinations.get(frozenset(emotions), "")