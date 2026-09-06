FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY reqs .

RUN pip install --no-cache-dir -r reqs

RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]