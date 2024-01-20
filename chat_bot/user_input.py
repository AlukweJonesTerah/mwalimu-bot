# chat_bot/user_input.py
# This module handles user input processing and model prediction in the chatbot application.
# It includes functions for spelling correction, keyword matching, and response generation.

import json
import os
import pickle
import logging
import random
from fuzzywuzzy import fuzz
import nltk
import string
from chat_bot.config import tokenizer_file_path, label_encoder_file_path, model_file_path
from nltk.corpus import stopwords
import numpy as np
from difflib import SequenceMatcher
from spellchecker import SpellChecker
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from flask import (
    request, render_template, flash, jsonify, Blueprint
)
from chat_bot.forms import ChatBotForm
from flask_login import LoginManager, login_required, current_user
from chat_bot.models import db, User, Conversation, SQLAlchemyError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
login_manager = LoginManager()
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


nltk.download('vader_lexicon', quiet=True)
nltk.download('stopwords', quiet=True)
spell_checker = SpellChecker()
stop_words = set(stopwords.words('english'))

try:
    # Load tokenizer, label encoder, and model
    with open(tokenizer_file_path, 'rb') as token_file:
        tokenizer = pickle.load(token_file)
    with open(label_encoder_file_path, 'rb') as label_file:
        le = pickle.load(label_file)

    if os.path.exists(model_file_path):
        with open(model_file_path, 'rb') as trained_model:
            model = tf.keras.models.load_model(model_file_path)
    else:
        print(f"Error: Model file '{model_file_path}' not found.")
        logging.error(f"Model file '{model_file_path}' not found")
        raise FileNotFoundError(f"Error: Model file '{model_file_path}' not found.")
    try:
        with open('chat_bot/mwalimu_sacco.json') as content:
            data1 = json.load(content)

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        print(f"Error on line {e.lineno}, column {e.colno}: {e.msg}")
        logging.error(f"JSON decoding error: {e}")
        logging.error(f"Error on line {e.lineno}, column {e.colno}: {e.msg}")
        raise ValueError(f"JSON decoding error: {e}") from None
except FileNotFoundError as e:
    print(e)
    logging.error(e)
except Exception as e:
    print(f"Error during initialization: {e}")
    logging.error(f"Error during initialization: {e}")

data = data1
responses = {}
for intent in data["intents"]:
    responses[intent['tag']] = intent['responses']

# Combine all responses into a single string
all_responses_combined = ' '.join([' '.join(response) for response in responses.values()])

# Split the combine responses into individual words
dataset_words = all_responses_combined.split()

bp = Blueprint('user_input', __name__, url_prefix='/user_input')

tag_keywords = {
    "loan_inquiry": ["loan", "apply", "requirements", "interest rates", "options", "types"],
    "greeting": ["hello", "hi", "howdy", "hey"],
}


def find_closest_keyword(user_input, keywords):
    """
    Find the closest keyword(s) based on fuzzy matching with the user input.
    :param keywords:
    :param user_input: The user's input
    :param keywords:  A dictionary where keys are tags, and values are lists of keywords associated with
                each tag.
    :return: - closest_keyword  (list or none): A list of closest matching keyword(s) or None if not match
    is found
    """
    user_input_lower = set(user_input.lower().split())
    closest_keyword = []
    max_similarity = 0.0

    for tag, tag_keywords in keywords.items():
        tag_keyword_set = set(tag_keywords)
        common_words = user_input_lower.intersection(tag_keyword_set)

        if not common_words:
            continue  # No common words, skip to the next tag
        # Calculate similarity based on the common words
        # similarity = fuzz.ratio(" ".join(common_words), " ".join(tag_keyword_set))
        similarity = SequenceMatcher(None, " ".join(common_words), " ".join(tag_keyword_set)).ratio()

        if similarity > max_similarity:
            max_similarity = similarity
            closest_keyword = list(tag_keyword_set)

        # Early exit if a perfect match is found
        if similarity == 100:
            return closest_keyword
    # Threshold for considering a match
    threshold = 70
    return closest_keyword if max_similarity >= threshold else None


keyword_responses = {
    "prorate": [
        "Prorate is the monthly share contribution a member would be required\
            to save each month based on the amount of loan given to him/her.",

    ],
    "loan_inquiry": [
        "We have various loan options available. How can I assist you with loans?",
    ],
    "greeting": [
        "Hello! How can i help you today?"
    ]
}


def keyword_match(user_input, keyword_responses):
    """
    Perform keyword matching and return the appropriate response. :param user_input (str): The user's input. :param
    keyword_responses (dict): A dictionary where keys are tags, and values are list of responses associated with each
    tag :return (str): The response based on keyword matching or default response if no match is found.
    """
    # Check for keyword matches
    for keyword, responses in keyword_responses.items():
        if keyword in user_input.lower():
            return random.choice(responses)
    # Use the optimizer find_closest_keyword function

    # If no keyword matches, return a default response or trigger further processing
    return "I'm not sure I understand. Could you please provide more details?"


def correct_spelling(input_text):
    corrected_text = [spell_checker.correction(word) for word in input_text.split()]
    return ' '.join(corrected_text)


def find_closest_match(word, dataset_words):
    closest_match, max_similarity = spell_checker.correction(word), 0
    for dataset_word in dataset_words:
        similarity = fuzz.ratio(word, dataset_word)
        if similarity > max_similarity:
            max_similarity = similarity
            closest_match = dataset_word
    return closest_match


def preprocess_input(user_input):
    processed_text = ' '.join(
        [ltrs.lower() for ltrs in user_input.split() if ltrs not in (string.punctuation, stop_words)])
    return processed_text


@bp.route('/bot', methods=['GET'])
@login_required
def chatbot():
    form = ChatBotForm()
    return render_template('chatbot/chatbot.html', form=form)

@bp.route('/bot', methods=['POST'])
@login_required
def chatbot_response():
    form = ChatBotForm(request.form)

    if request.method == 'POST' or request.is_json:
        if request.is_json:
            data = request.get_json()
            user_input = data.get('user_input', '')
        else:
            user_input = form.user_input.data

        # Preprocess user input
        processed_input = preprocess_input(user_input)

        # Tokenize and pad the input
        input_sequence = tokenizer.texts_to_sequences([processed_input])
        padded_input = pad_sequences(input_sequence, maxlen=model.input_shape[1])

        # Make a prediction
        predictions = model.predict(padded_input)
        predicted_class = np.argmax(predictions)

        # Convert the predicted class back to the original tag using the label encoder
        predicted_tag = le.inverse_transform([predicted_class])[0]

        # Get a random response for the predicted tag
        response = random.choice(responses.get(predicted_tag, ['Sorry, I don\'t understand.']))

        try:
            conversation = Conversation(user=current_user, user_input=user_input, bot_response=response)
            db.session.add(conversation)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f'Error saving user conversation: {str(e)}')
            flash(f'Error saving user conversation: {str(e)}', 'danger')
            return jsonify({'error': 'Database error'}), 500
        except Exception as e:
            db.session.rollback()
            logging.error(f'Unexpected error during conversation saving: {str(e)}')
            flash('An unexpected error occurred during conversation saving.', 'danger')
            return jsonify({'error': 'Unexpected error'}), 500

        # Check if the client expects JSON (Accept header contains 'application/json')
        # if 'application/json' in request.headers.get('Accept', ''):
        if request.is_json:  # check if request is AJAX request
            print(user_input)
            return jsonify({'user_input': user_input, 'response': response})
        else:
            return render_template('chatbot/chatbot.html', form=form, user_input=user_input, response=response)
    if request.is_json:
        return jsonify({'error': 'Invalid form submission'}), 400  # HTTP 400 Bad Request
    else:
        flash('Invalid form submission', 'danger')
        return render_template('chatbot/chatbot.html', form=form)

# @bp.route('/bot', methods=['GET', 'POST'])
# def bot():
#     form = ChatBotForm()
#
#     if form.validate_on_submit():
#         user_input = form.text_input.data
#
#         # Preprocess user input
#         processed_input = preprocess_input(user_input)
#
#         # Tokenize and pad the input
#         input_sequence = tokenizer.texts_to_sequences([processed_input])
#         padded_input = pad_sequences(input_sequence, maxlen=model.input_shape[1])
#
#         # Make a prediction
#         predictions = model.predict(padded_input)
#         predicted_class = np.argmax(predictions)
#
#         # Convert the predicted class back to the original tag using the label encoder
#         predicted_tag = le.inverse_transform([predicted_class])[0]
#
#         # Get a random response for the predicted tag
#         response = random.choice(responses.get(predicted_tag, ['Sorry, I don\'t understand.']))
#         print(response)
#
#         # Check if the client expects JSON (Accept header contains 'application/json')
#         if 'application/json' in request.headers.get('Accept', ''):
#             print(user_input)
#             print(response)
#             return jsonify({'response': response})
#         else:
#             return render_template('chatbot/chatbot.html', form=form, response=response, user_input=user_input)
#
#     return render_template('chatbot/chatbot.html', form=form, response=None)
