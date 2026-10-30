import nltk
import re
import json
import numpy as np

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory, LangDetectException
import boto3
from botocore.config import Config
from email.header import decode_header, make_header

# --------------------------------------------------
# NLTK configuration
# --------------------------------------------------
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

stop_words = set(stopwords.words("english"))

DetectorFactory.seed = 0

translate_client = boto3.client(
    "translate",
    region_name="us-east-1",
    config=Config(
        retries={
            "max_attempts": 5,
            "mode": "standard"
        }
    )
)

def decode_email_header(text: str) -> str:
    """Decode RFC 2047 MIME-encoded text."""
    if not text:
        return ""

    try:
        return str(make_header(decode_header(text)))
    except (UnicodeError, LookupError, ValueError):
        return text


def clean_email_body(body: str) -> str:
    """Clean an already decoded email body."""
    if not body:
        return ""

    # Decode MIME encoded-words if present in the body
    # (some email sources incorrectly include them there).
    body = decode_email_header(body)

    soup = BeautifulSoup(body, "html.parser")

    for element in soup([
        "script",
        "style",
        "head",
        "noscript"
    ]):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_email(subject: str, body: str) -> dict:
    """Return cleaned subject and body for database storage."""

    clean_subject = decode_email_header(subject).strip()
    clean_subject = re.sub(r"\s+", " ", clean_subject)

    clean_body = clean_email_body(body)

    return {
        "subject": clean_subject,
        "body": clean_body
    }

def remove_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")

    # Remove HTML elements that should not be analyzed
    for element in soup(["script", "style", "head", "noscript"]):
        element.decompose()

    return soup.get_text(separator=" ", strip=True)


def lemmatization(text):
    lemmatizer = WordNetLemmatizer()

    text = text.split()
    text = [lemmatizer.lemmatize(y) for y in text]

    return " ".join(text)


def remove_stop_words(text):
    Text = [i for i in str(text).split() if i not in stop_words]
    return " ".join(Text)


def Removing_numbers(text):
    text = "".join([i for i in text if not i.isdigit()])
    return text


def lower_case(text):
    text = text.split()
    text = [y.lower() for y in text]
    return " ".join(text)


def Removing_punctuations(text):
    text = re.sub(
        "[%s]" % re.escape(
            """!"#$%&'()*+,،-./:;<=>؟?@[\]^_`{|}~"""
        ),
        " ",
        text
    )

    text = text.replace("؛", "")
    text = re.sub(r"\s+", " ", text)

    return " ".join(text.split()).strip()


def Removing_urls(text):
    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    return url_pattern.sub("", text)


def remove_small_sentences(text):
    for i in range(len(text)):
        if len(text.iloc[i].split()) < 3:
            text.iloc[i] = np.nan


def normalize_text(text):
    text = remove_html_tags(text)
    text = lower_case(text)
    text = remove_stop_words(text)
    text = Removing_numbers(text)
    text = Removing_punctuations(text)
    text = Removing_urls(text)
    text = lemmatization(text)
    return text


def normalized_sentence(sentence):
    sentence = lower_case(sentence)
    sentence = Removing_urls(sentence)
    sentence = Removing_numbers(sentence)
    sentence = Removing_punctuations(sentence)
    sentence = remove_stop_words(sentence)
    sentence = lemmatization(sentence)
    return sentence


def detect_email_language(text):
    if not text or not text.strip():
        return "unknown"

    try:
        return detect(text)

    except LangDetectException:
        return "unknown"

def split_text(text, max_length=4000):
    words = text.split()
    chunks = []

    current_chunk = []
    current_length = 0

    for word in words:

        if len(word) > max_length:

            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

            for i in range(0, len(word), max_length):
                chunks.append(word[i:i + max_length])

            continue

        additional_length = len(word) + (
            1 if current_chunk else 0
        )

        if (
            current_chunk
            and current_length + additional_length > max_length
        ):
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)

        else:
            current_chunk.append(word)
            current_length += additional_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def translate_to_english(text, language):

    if language == "en":
        return text

    if language != "es":
        raise ValueError(
            f"Unsupported language: {language}"
        )

    # Split long emails into smaller chunks
    chunks = split_text(
        text,
        max_length=4000
    )

    translated_chunks = []

    for chunk in chunks:

        response = translate_client.translate_text(
            Text=chunk,
            SourceLanguageCode="es",
            TargetLanguageCode="en"
        )

        translated_chunks.append(
            response["TranslatedText"]
        )

    return " ".join(translated_chunks)

def prepare_email_text(text):
    text = decode_email_header(text)

    clean_text = remove_html_tags(text)
    if not text or not text.strip():
        raise ValueError("Email body is empty")

    if not clean_text:
        raise ValueError(
            "Email does not contain readable text"
        )

    language = detect_email_language(clean_text)

    english_text = translate_to_english(
        clean_text,
        language
    )

    normalized_text = normalized_sentence(english_text)

    if not normalized_text.strip():
        raise ValueError(
            "Email became empty after normalization"
        )

    return normalized_text, language

def predict_emotion(text, tokenizer, model):

    labels = {
        0: "Sadness",
        1: "Joy",
        2: "Disgust",
        3: "Anger",
        4: "Fear"
    }

    # HTML extraction, language detection,
    # translation and normalization
    text, language = prepare_email_text(text)

    seq = tokenizer.texts_to_sequences([text])[0]

    if not seq:
        raise ValueError("No tokens available for prediction")

    MAX_LENGTH = 19

    # Split token sequence into chunks of 19
    chunks = [
        seq[i:i + MAX_LENGTH]
        for i in range(0, len(seq), MAX_LENGTH)
    ]

    # Pad each chunk to exactly 19 tokens
    padded_chunks = pad_sequences(
        chunks,
        maxlen=MAX_LENGTH,
        padding="post",
        truncating="post"
    )

    # Predict all chunks in one batch
    predictions = model.predict(
        padded_chunks,
        verbose=0
    )

    # Average probabilities across chunks
    prediction = np.mean(predictions, axis=0)

    print("\n========== CHUNK ANALYSIS ==========")

    for i, chunk_prediction in enumerate(predictions):
        chunk_tokens = chunks[i]

        chunk_words = [
            tokenizer.index_word.get(token_id, "<UNKNOWN>")
            for token_id in chunk_tokens
        ]

        chunk_probabilities = {
            labels[j]: round(float(chunk_prediction[j]), 4)
            for j in range(len(chunk_prediction))
        }

        print(f"\nCHUNK {i + 1}")
        print("WORDS:", " ".join(chunk_words))
        print("PROBABILITIES:", chunk_probabilities)
        print(
            "PREDICTED EMOTION:",
            labels[int(np.argmax(chunk_prediction))]
        )

    print("\nAVERAGED PROBABILITIES:", prediction)
    print("====================================")

    emotion_id = int(np.argmax(prediction))

    probabilities = {
        labels[i]: float(prediction[i])
        for i in range(len(prediction))
    }

    probabilities = dict(
        sorted(
            probabilities.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    print("\nFINAL PREDICTION") 
    print(probabilities)

    return json.dumps({
        "emotion": labels[emotion_id],
        "confidence": float(prediction[emotion_id]),
        "language": language,
        "chunks_analyzed": len(chunks),
        "probabilities": probabilities
    })