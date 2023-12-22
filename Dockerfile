FROM python:latest

WORKDIR /app

RUN pip install poetry

COPY * /app

RUN poetry config virtualenvs.create false && poetry install

CMD ["python", "-m", "main"]