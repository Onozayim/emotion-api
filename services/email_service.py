from sqlalchemy.dialects.mysql import insert
import models

def update_email_stats(db, received_date, primary_emotion, secondary_emotion, compound_emotion):

    increments = {
        primary_emotion: 1,
        f"sec_{secondary_emotion}": 1,
    }

    if compound_emotion:
        increments[compound_emotion] = (
            increments.get(compound_emotion, 0) + 1
        )

    stmt = insert(models.EmailCount).values(
        created_at=received_date,
        **increments
    )

    stmt = stmt.on_duplicate_key_update(
        **{
            column: getattr(models.EmailCount, column) + value
            for column, value in increments.items()
        }
    )

    db.execute(stmt)