import os
import uuid
from datetime import date, datetime
from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends
from fastapi import FastAPI, UploadFile, File
from minio import Minio
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

import crud
import models
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
load_dotenv()

ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
MINIO_API_HOST = "http://localhost:9000"
client = Minio("localhost:9000", access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.post("/frames")
async def upload(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    request_id = str(datetime.now()).replace(' ', '')
    bucketname = date.today().strftime('%Y%m%d')
    if not client.bucket_exists(bucketname):
        client.make_bucket(bucketname)

    uploaded_files_list = []
    for file in files:
        new_filename = f'{uuid.uuid4()}.jpg'
        client.fput_object(bucketname, new_filename, file.filename, )
        crud.save_file(db, new_filename, request_id)
        uploaded_files_list.append(new_filename)
    return JSONResponse(content={"filenames": uploaded_files_list},
                        status_code=200)


@app.get("/frames/{request_id}")
def get_files(request_id: str, db: Session = Depends(get_db)):
    db_files = crud.get_files_by_request_id(db, id=request_id)
    if len(db_files) == 0:
        raise HTTPException(status_code=400, detail="No item found")
    results_list = [{result.filename: result.date_registered} for result in db_files]
    return JSONResponse(content={"files": results_list},
                        status_code=200)


@app.delete("/frames/{request_id}")
def delete_files(request_id: str, db: Session = Depends(get_db)):
    del_files = crud.get_files_by_request_id(db, request_id)
    if len(del_files) == 0:
        return JSONResponse(content={
            "removed": False,
            "error_message": "File not found in database"
        }, status_code=404)
    else:
        # получаем из request_id вида (2022-05-05 18:13:03.439350) bucketname вида (20220505)
        bucketname = request_id[:10].replace('-', '')
        if not client.bucket_exists(bucketname):
            return JSONResponse(content={"removed": False, "error_message": "No such Bucket!"},
                                status_code=404)

        if [obj.object_name for obj in client.list_objects(bucketname)]:
            # не получилось использовать client.remove_objects(bucketname, delete_object_list), тк
            # функция не вызывала какого-либо эффекта, возможно были проблемы с разрешениями
            delete_object_list = [result.filename for result in del_files]
            for obj in delete_object_list:
                client.remove_object(bucketname, obj)
            crud.delete_files_by_request_id(db, request_id)
            return JSONResponse(content={"removed": True
                                         }, status_code=200)
        else:
            return JSONResponse(content={
                "removed": False,
                "error_message": "File in bucket not found"
            }, status_code=404)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000, debug=True)
