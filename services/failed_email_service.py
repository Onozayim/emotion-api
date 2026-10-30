import logging
from datetime import datetime, timezone

from database import SessionLocal
from models import FailedEmail

logger = logging.getLogger(__name__)


def save_failed_email(task_id, email, exception, attempts):
    db = SessionLocal()

    try:
        received_at = email.get("received_at")

        if isinstance(received_at, str):
            received_at = datetime.fromisoformat(
                received_at.replace("Z", "+00:00")
            )

        if received_at is not None and received_at.tzinfo is not None:
            received_at = received_at.astimezone(
                timezone.utc
            ).replace(tzinfo=None)

        failed_email = db.query(FailedEmail).filter(
            FailedEmail.task_id == task_id
        ).first()

        if failed_email is None:
            failed_email = FailedEmail(
                task_id=task_id,
                from_email=email.get("from_email"),
                subject=email.get("subject"),
                body=email.get("body"),
                received_at=received_at,
                error_type=type(exception).__name__,
                error_message=str(exception)[:4000],
                attempts=attempts,
                status="failed",
            )

            db.add(failed_email)

        else:
            failed_email.error_type = type(exception).__name__
            failed_email.error_message = str(exception)[:4000]
            failed_email.attempts = attempts
            failed_email.status = "failed"

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "Could not save failed email for task %s",
            task_id,
        )
        raise

    finally:
        db.close()