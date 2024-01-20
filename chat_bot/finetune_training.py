import json
import os
import pickle
import string
from zipfile import ZipFile

import numpy as np
import pandas as pd
import requests
from nltk.corpus import stopwords
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Input, Embedding, LSTM, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

# Download embeddings
url = 'http://nlp.stanford.edu/data/glove.6B.zip'
file = 'glove.6B.100d.txt'

if not os.path.exists(file):
    with requests.get(url) as r:
        with open('glove.zip', 'wb') as f:
            f.write(r.content)

    with ZipFile('glove.zip') as z:
        z.extract(file)

    os.remove('glove.zip')

# Load data
with open('mwalimu_sacco.json') as f:
    data = json.load(f)

inputs = []
tags = []
for intent in data['intents']:
    inputs.extend(intent['inputs'])
    tags.extend([intent['tag']] * len(intent['inputs']))

df = pd.DataFrame({'inputs': inputs, 'tags': tags})

# Add more examples
extra = [["When is AGM?", "agm"],
         ["What is bonus criteria?", "bonus"],
         ["How to transfer shares?", "transfer"]]

extra_df = pd.DataFrame(extra, columns=['inputs', 'tags'])
df = pd.concat([df, extra_df]).reset_index(drop=True)

# Preprocess
stop_words = stopwords.words('english')
df['inputs'] = df['inputs'].apply(
    lambda x: ' '.join([word.lower() for word in x.split() if word not in (stop_words, string.punctuation)]))

# Encode labels
le = LabelEncoder()
y_train = le.fit_transform(df['tags'])

# Tokenize
tokenizer = Tokenizer(num_words=5000)
tokenizer.fit_on_texts(df['inputs'])

X_train = tokenizer.texts_to_sequences(df['inputs'])
X_train = pad_sequences(X_train)

# Load embeddings
embeddings_index = {}
with open(file, encoding='utf8') as f:
    for line in f:
        values = line.rstrip().rsplit(' ')
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs

embedding_matrix = np.zeros((len(tokenizer.word_index) + 1, 100))
for word, i in tokenizer.word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector

# Define model
input_shape = X_train.shape[1]
vocab_size = len(tokenizer.word_index) + 1
output_dim = len(set(y_train))

i = Input(shape=(input_shape,))
x = Embedding(vocab_size, 100, weights=[embedding_matrix], trainable=False)(i)
x = LSTM(64, return_sequences=True)(x)
x = LSTM(64)(x)
x = Dense(64, activation='relu')(x)
x = Dense(output_dim, activation='softmax')(x)

model = Model(i, x)

# Compile and train
model.compile(loss='sparse_categorical_crossentropy',
              optimizer=Adam(learning_rate=0.001),
              metrics=['accuracy'])

es = EarlyStopping(monitor='val_loss', patience=5)

model.fit(X_train, y_train,
          validation_split=0.2,
          epochs=30,
          callbacks=[es])

# Save encoder
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

# Reload encoder
with open('label_encoder.pkl', 'rb') as f:
    le = pickle.load(f)

# Retrain with class weights
class_weights = {
    le.transform(['prorata'])[0]: 10,
    le.transform(['agm'])[0]: 5,
    le.transform(['bonus'])[0]: 3,
    le.transform(['transfer'])[0]: 2
}

# Retrain top layers
for layer in model.layers[:-2]:
    layer.trainable = False

model.compile(loss='sparse_categorical_crossentropy',
              optimizer=Adam(lr=1e-3),
              metrics=['accuracy'])

model.fit(X_train, y_train,
          class_weight=class_weights,
          epochs=10)

# Save model
model.save('refined_model.h5')
with open('tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)
