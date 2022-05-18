import json
from datetime import datetime

import models
from sqlalchemy.orm import Session


def save_file(db: Session, filename: str, id: str):
    db_file = models.File(filename=filename, date_registered=str(datetime.now()), request_id=id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_files_by_request_id(db: Session, id: str):
    return db.query(models.File).filter(models.File.request_id == id).all()


def delete_files_by_request_id(db: Session, id: str):
    db_files = db.query(models.File).filter(models.File.request_id == id)
    db_files.delete()
    db.commit()
    return db_files


