import nltk
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import json
from bs4 import BeautifulSoup

nltk.download("stopwords")
stop_words = set(stopwords.words("english"))


def remove_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

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
    ## Remove punctuations
    text = re.sub(
        "[%s]" % re.escape("""!"#$%&'()*+,،-./:;<=>؟?@[\]^_`{|}~"""), " ", text
    )
    text = text.replace(
        "؛",
        "",
    )

    ## remove extra whitespace
    text = re.sub("\s+", " ", text)
    text = " ".join(text.split())
    return text.strip()


def Removing_urls(text):
    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    return url_pattern.sub(r"", text)


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
    sentence = remove_stop_words(sentence)
    sentence = Removing_numbers(sentence)
    sentence = Removing_punctuations(sentence)
    sentence = Removing_urls(sentence)
    sentence = lemmatization(sentence)
    return sentence




def predict_emotion(text, tokenizer, model):
    labels = {0: "Sadness", 1: "Joy", 2: "Disgust", 3: "Anger", 4: "Fear"}
    text = normalize_text(text)
    seq = tokenizer.texts_to_sequences([text])

    padded = pad_sequences(seq, maxlen=19, padding="post", truncating="post")

    prediction = model.predict(padded, verbose=0)[0]

    emotion_id = np.argmax(prediction)

    probabilities = {labels[i]: float(prediction[i]) for i in range(len(prediction))}

    probabilities = dict(
        sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    )

    return json.dumps(
        {
            "emotion": labels[emotion_id],
            "confidence": float(prediction[emotion_id]),
            "probabilities": probabilities,
        }
    )
