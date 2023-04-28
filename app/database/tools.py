from typing import AsyncIterable

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy import Select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import BooleanClauseList, ColumnElement
from sqlalchemy.sql._typing import _TP

from app.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = sessionmaker(
    engine,  # type: ignore
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_engine() -> AsyncEngine:
    return engine


async def get_session() -> AsyncIterable[AsyncSession]:
    async with async_session() as session:
        yield session


class FilterConditionChain:
    complex_condition: BooleanClauseList | ColumnElement[bool] | None

    def __init__(self, condition: ColumnElement[bool] | None):
        self.complex_condition = condition

    def __and__(self, condition: ColumnElement[bool] | None):
        if condition is None:
            return self
        if self.complex_condition is None:
            self.complex_condition = condition
            return self
        self.complex_condition &= condition
        return self

    def resolve(self, query: Select[_TP]) -> Select[_TP]:
        if self.complex_condition is None:
            return query
        return query.filter(self.complex_condition)
