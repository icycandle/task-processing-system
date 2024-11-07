FROM python:3.13-slim

WORKDIR /app

RUN pip install poetry uvicorn

COPY . /app

# RUN poetry config virtualenvs.create false
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-dev

EXPOSE 8000
