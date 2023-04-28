FROM python:3.10.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml /src/
WORKDIR /src

RUN poetry config virtualenvs.create false && poetry install --no-dev --no-ansi

COPY . /src
