import json
import logging

import models
from analyzer import predict_emotion, clean_email
from celery_app import celery
from database import SessionLocal
from model_loader import model, tokenizer
from services.email_service import update_email_stats
from services.survey_service import create_or_update_survey_answer
from datetime import datetime
from services.failed_email_service import save_failed_email
from celery import Task

from sqlalchemy.exc import OperationalError
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
)

logger = logging.getLogger(__name__)

TEMPORARY_AWS_ERRORS = {
    "ThrottlingException",
    "TooManyRequestsException",
    "InternalServerException",
    "ServiceUnavailableException",
}


def is_temporary_aws_error(exc):
    code = exc.response.get("Error", {}).get("Code", "")
    return code in TEMPORARY_AWS_ERRORS

class EmailProcessingTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        email = args[0] if args else kwargs.get("email", {})

        try:
            save_failed_email(
                task_id=task_id,
                email=email,
                exception=exc,
                attempts=self.request.retries + 1,
            )

            logger.error(
                "Email permanently failed. Task ID: %s",
                task_id,
            )

        except Exception:
            logger.exception(
                "Could not persist failed email. Task ID: %s",
                task_id,
            )

@celery.task
def process_emails(emails):
    task_ids = []

    for email in emails:
        task = process_single_email.delay(email)
        task_ids.append(task.id)

    return {
        "queued": len(task_ids),
        "task_ids": task_ids,
    }

def process_one_email(db, email):
    cleaned = clean_email(
        subject=email["subject"],
        body=email["body"],
    )

    logger.info(
        "Processing email from: %s",
        email["from_email"],
    )

    result = predict_emotion(
        cleaned["body"],
        tokenizer,
        model,
    )

    result = json.loads(result)

    emotions = list(result["probabilities"].keys())

    primary_emotion = emotions[0].lower()
    secondary_emotion = emotions[1].lower()

    compound_emotion = get_compound_emotion(
        primary_emotion,
        secondary_emotion,
    )

    received_at = email["received_at"]

    if isinstance(received_at, str):
        received_at = datetime.fromisoformat(
            received_at.replace("Z", "+00:00")
        )

    received_date = (
        received_at.date()
        if isinstance(received_at, datetime)
        else received_at
    )

    new_email = models.Email(
        body=cleaned["body"].strip(),
        subject=cleaned["subject"].strip(),
        from_email=email["from_email"].strip(),
        emotion=primary_emotion,
        secondary_emotion=secondary_emotion,
        compound_emotion=compound_emotion,
        created_at=received_at,
    )

    db.add(new_email)
    db.flush()

    create_or_update_survey_answer(
        db=db,
        email_address=email["from_email"].strip(),
        emotion=primary_emotion,
    )

    update_email_stats(
        db=db,
        received_date=received_date,
        primary_emotion=primary_emotion,
        secondary_emotion=secondary_emotion,
        compound_emotion=compound_emotion,
    )

    return new_email.id


@celery.task(bind=True, base=EmailProcessingTask, max_retries=3)
def process_single_email(self, email):
    db = None

    try:
        db = SessionLocal()
        email_id = process_one_email(db, email)

        db.commit()

        logger.info(
            "Successfully processed email from: %s",
            email["from_email"],
        )

        return {
            "status": "processed",
            "email_id": email_id,
            "task_id": self.request.id,
        }

    except (
        OperationalError,
        EndpointConnectionError,
        ConnectTimeoutError,
        ReadTimeoutError,
    ) as exc:
        if db is not None:
            db.rollback()

        logger.warning(
            "Temporary error processing email. "
            "Task ID: %s. Retry: %s/%s. Error: %s",
            self.request.id,
            self.request.retries,
            self.max_retries,
            exc,
        )

        countdown = 30 * (2 ** self.request.retries)

        raise self.retry(
            exc=exc,
            countdown=countdown,
        )

    except ClientError as exc:
        if db is not None:
            db.rollback()

        if is_temporary_aws_error(exc):
            countdown = 30 * (2 ** self.request.retries)

            raise self.retry(
                exc=exc,
                countdown=countdown,
            )

        logger.exception(
            "Non-retryable AWS error. Task ID: %s",
            self.request.id,
        )
        raise

    except ValueError:
        if db is not None:
            db.rollback()

        logger.exception(
            "Invalid email data. Task ID: %s",
            self.request.id,
        )
        raise

    except Exception:
        if db is not None:
            db.rollback()

        logger.exception(
            "Unexpected email processing failure. Task ID: %s",
            self.request.id,
        )
        raise

    finally:
        if db is not None:
            db.close()


def get_compound_emotion(primary, secondary):
    emotions = frozenset([primary, secondary])

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

    return combinations.get(emotions, "")