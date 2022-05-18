from sqlalchemy import Column, Integer, String

from database import Base


class File(Base):
    __tablename__ = "inbox"

    request_id = Column(String)
    filename = Column(String, unique=True, primary_key=True)
    date_registered = Column(String)
