import os
import pickle

from dotenv import load_dotenv
from tensorflow.keras.models import load_model

load_dotenv()

MODEL_PATH = os.getenv("MODEL")
TOKENIZER_PATH = os.getenv("PKL")

print("Loading emotion model...")

model = load_model(MODEL_PATH)

print("Loading tokenizer...")

with open(TOKENIZER_PATH, "rb") as file:
    tokenizer = pickle.load(file)

print("Model and tokenizer loaded successfully.")