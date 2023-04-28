from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from app.database.base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass
