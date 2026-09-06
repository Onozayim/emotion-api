import json
from datetime import datetime, timezone

import models
from analyzer import predict_emotion
from celery_app import celery
from database import SessionLocal
from model_loader import model, tokenizer


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
                body=email["body"],
                subject=email["subject"],
                from_email=email["from_email"],
                emotion=primary_emotion,
                secondary_emotion=secondary_emotion,
                compound_emotion=compound_emotion,
            )

            db.add(new_email)

            stats = (
                db.query(models.EmailCount)
                .filter(
                    models.EmailCount.created_at == datetime.now(timezone.utc).today()
                )
                .first()
            )

            if not stats:
                stats = models.EmailCount()
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