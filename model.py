import numpy as np
import pandas as pd
import tensorflow as tf

from random import randint, shuffle, choice
import random

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score, recall_score

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras import optimizers
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras import backend as K

import re

import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from nltk.corpus import stopwords, wordnet

from data_augmentation import *


df = pd.read_csv(r'tweets.csv')
tweets = df['text']
labels = df['target']

print(labels.value_counts()) # number of false tweets is wayyy higher, we have to fix that

true_tweets = df[df['target'] == 1]['text']

aug_df = pd.DataFrame()
aug_df['text'] = tweets
aug_df['target'] = labels

new_true_tweets = augment_dataset(true_tweets)
ones = pd.Series([1 for _ in range(len(new_true_tweets))])
temp_df = pd.concat([new_true_tweets, ones], axis=1).reset_index(drop=True)
temp_df.columns = ['text', 'target']

aug_df = aug_df.append(temp_df).reset_index(drop=True)
print(aug_df['target'].value_counts()) # after dataset augmentation

def preprocess_texts(tweets):
  phrases = [t.lower() for t in tweets.values]
  stw = stopwords.words('english')

  for i in range(len(phrases)):
    word_lst = phrases[i].split()
    no_stop_tok_lst = []
    for w in word_lst:
      if w not in stw and 'http' not in w:
        no_stop_tok_lst.append(w)
    s = ' '.join(no_stop_tok_lst)
    phrases[i] = s

    punctuation = re.compile("[-/#`.%^~+’“”\"*…&?!',:;()|0-9]")

  for i in range(len(phrases)):
    no_punct_str = punctuation.sub('', phrases[i])
    phrases[i] = no_punct_str
  
  lem = nltk.stem.WordNetLemmatizer()

  for i in range(len(phrases)):
    lem_lst = []
    word_lst = phrases[i].split(' ') 
    for w in word_lst:
      w = lem.lemmatize(w)
      lem_lst.append(w)
    s = ' '.join(lem_lst)
    phrases[i] = s

  return phrases

tweets = aug_df['text']
labels = aug_df['target']
phrases = preprocess_texts(tweets)
X_train, X_test, y_train, y_test = train_test_split(phrases, labels, train_size=0.7)

tokenizer = Tokenizer(num_words=10000, oov_token='<OOV>')
tokenizer.fit_on_texts(X_train)

X_train = pad_sequences(tokenizer.texts_to_sequences(X_train), padding='post')
X_test = pad_sequences(tokenizer.texts_to_sequences(X_test), padding='post')

vocab_size = len(tokenizer.word_index) + 1
embedding_dimensions = 100

def recall_metrics(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_metrics(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_metrics(y_true, y_pred):
    precision = precision_metrics(y_true, y_pred)
    recall = recall_metrics(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

n_hidden = 30
model = Sequential([
        layers.Embedding(vocab_size, embedding_dimensions), 
        layers.Conv1D(128, 3),
        layers.LeakyReLU(alpha=0.3), 
        layers.GlobalMaxPooling1D(),
        layers.Dropout(0.5), 
        layers.Dense(n_hidden), 
        layers.LeakyReLU(alpha=0.3),
        layers.Dropout(0.5),
        layers.Dense(n_hidden),
        layers.LeakyReLU(alpha=0.3),
        layers.Dense(1, activation='sigmoid')
])
optimizer = optimizers.SGD(learning_rate=0.006, momentum=0.9, nesterov=True)
model.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy', f1_metrics], )
history = model.fit(X_train, y_train, epochs=10, batch_size=10, validation_data=(X_test, y_test))

y_pred = model.predict(X_test)
y_pred_processed = [1 if i[0] > 0.5 else 0 for i in y_pred]
print(f1_score(y_test, y_pred_processed)) 
# previous - 0.6411
# 0.9454 after augmenting the dataset

