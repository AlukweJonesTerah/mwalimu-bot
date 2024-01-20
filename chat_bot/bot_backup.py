@bp.route('/bot', methods=['GET'])
@login_required
def bot():
    form = ChatBotForm()
    return render_template('chatbot/chatbot.html', form=form)


@bp.route('/bot', methods=['POST'])
def predict():
    form = ChatBotForm(request.form)

    if request.method == 'POST' or form.validate_on_submit():
        if request.is_json:
            # Handling JSON data
            data = request.get_json()
            user_input = data.get('text_input', '')
        else:
            # Handling form data
            user_input = form.text_input.data


        # Spelling check correct misspelled words
        user_input_corrected = correct_spelling(user_input)

        # Find closest matches for each word in the user input
        closest_matches = [find_closest_match(word, dataset_words) for word in user_input_corrected.split()]

        # Combine the closest matches into a single string
        closest_matches_combined = ' '.join([match[0] if match else '' for match in closest_matches])

        # Preprocess user input
        processed_input = preprocess_input(user_input)

        # Tokenize and pad the input sequence
        input_sequence = tokenizer.texts_to_sequences([processed_input])
        padded_sequence = pad_sequences(input_sequence, maxlen=model.input_shape[1])

        # Make prediction
        prediction = model.predict(padded_sequence)

        # Decode the prediction
        predicted_class_index = np.argmax(prediction)
        predicted_class = le.inverse_transform([predicted_class_index])[0]

        # Print the predicted class index and tag for debugging
        print(f"Predicted Class Index: {predicted_class_index}")
        print(f"Predicted Tag: {predicted_class}")
        print("User Input:", user_input)
        print("Corrected Input:", user_input_corrected)
        print("Closest Matches:", closest_matches_combined)
        print("Tag Keywords:", tag_keywords)

        # Get the responses for the predicted class
        class_responses = responses.get(predicted_class, ["No response found"])

        # Use the corrected user input with closest matches for response matching
        model_response = random.choice(class_responses) if closest_matches else "No response found"

        # Return the model response as JSON
        return jsonify({'model_response': model_response})

    return jsonify({'error': 'Invalid form submission'})


def preprocess_input(text):
    # Perform any necessary preprocessing on the user input
    # (e.g., lowercase, remove punctuation, stop words)
    # Use the same preprocessing as in the training script
    stop_words = set(stopwords.words('english'))

    # Spell checking
    words = text.split()
    correct_words = [spell_checker.correction(word) for word in words]

    processed_text = ' '.join([ltrs.lower() for ltrs in correct_words if ltrs not in (string.punctuation, stop_words)])
    return processed_text

.html('<div>' + data.user_input + '</div>');

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'  # Use your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a simple User model for demonstration
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Create tables (you might want to do this in a separate script or using Flask-Migrate)
db.create_all()

@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        # Start a transaction
        with db.session.begin():
            # Your database operations here
            new_user = User(username=request.form['username'], email=request.form['email'])
            db.session.add(new_user)

        # Commit the transaction (not needed here due to the 'with' statement)
        # db.session.commit()

        return "User added successfully!"
    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        return f"Error: {e}"
    finally:
        # Close the session (not needed here due to the 'with' statement)
        # db.session.close()

if __name__ == '__main__':
    app.run(debug=True)
