# credit to Jason Wei and Kai Zou for data augmentation code

import random
from random import choice, shuffle
import re
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet
import pandas as pd


stop_words = ['i', 'me', 'my', 'myself', 'we', 'our', 
			'ours', 'ourselves', 'you', 'your', 'yours', 
			'yourself', 'yourselves', 'he', 'him', 'his', 
			'himself', 'she', 'her', 'hers', 'herself', 
			'it', 'its', 'itself', 'they', 'them', 'their', 
			'theirs', 'themselves', 'what', 'which', 'who', 
			'whom', 'this', 'that', 'these', 'those', 'am', 
			'is', 'are', 'was', 'were', 'be', 'been', 'being', 
			'have', 'has', 'had', 'having', 'do', 'does', 'did',
			'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
			'because', 'as', 'until', 'while', 'of', 'at', 
			'by', 'for', 'with', 'about', 'against', 'between',
			'into', 'through', 'during', 'before', 'after', 
			'above', 'below', 'to', 'from', 'up', 'down', 'in',
			'out', 'on', 'off', 'over', 'under', 'again', 
			'further', 'then', 'once', 'here', 'there', 'when', 
			'where', 'why', 'how', 'all', 'any', 'both', 'each', 
			'few', 'more', 'most', 'other', 'some', 'such', 'no', 
			'nor', 'only', 'own', 'same', 'so', 'than', 'too', 
			'very', 's', 't', 'can', 'will', 'just', 'don', 
			'should', 'now']

def get_only_chars(line):
    clean_line = ''

    line = line.replace("’", "")
    line = line.replace("'", "")
    line = line.replace("-", " ")
    line = line.replace("\t", " ")
    line = line.replace("\n", " ")
    line = line.lower()

    for char in line:
        if char in 'qwertyuiopasdfghjklzxcvbnm ':
            clean_line += char
        else:
            clean_line += ' '

    clean_line = re.sub(' +',' ',clean_line)
    if clean_line[0] == ' ':
        clean_line = clean_line[1:]
        
    return clean_line

def random_swap(words, n):
    new_words = words
    for _ in range(n):
    	new_words = swap_word(new_words)

    return new_words

def swap_word(new_words):
    random_idx_1 = random.randint(0, len(new_words)-1)
    random_idx_2 = random_idx_1
    counter = 0
    while random_idx_2 == random_idx_1:
    	random_idx_2 = random.randint(0, len(new_words)-1)
    	counter += 1
    	if counter > 3:
    		return new_words
    new_words[random_idx_1], new_words[random_idx_2] = new_words[random_idx_2], new_words[random_idx_1] 

    return new_words

def random_deletion(words, p):
    if len(words) <= 2:
        return words
        
    #randomly delete words with probability p
    new_words = []
    for word in words:
        r = random.uniform(0, 1)
    if r > p:
            new_words.append(word)

    #if you end up deleting all words, just return a random word
    if len(new_words) == 0:
    	rand_int = random.randint(0, len(words)-1)
    	return [words[rand_int]]

    return new_words

def get_synonyms(word):
  synonyms = set()

  for syn in wordnet.synsets(word):
    for l in syn.lemmas():
      synonym = l.name().replace("_", "").replace("-", "").lower()
      synonym = "".join([char for char in synonym if char in 'qwertyuiopasdfghjklzxcvbnm'])
      synonyms.add(synonym)
  if word in synonyms:
    synonyms.remove(word)

  return list(synonyms)

def synonym_replacement(words, n):
    new_words = words
    random_word_list = list(set([word for word in words if word not in stop_words]))
    random.shuffle(random_word_list)
    num_replaced = 0
    for random_word in random_word_list:
        synonyms = get_synonyms(random_word)
        if len(synonyms) >= 1:
            synonym = random.choice(list(synonyms))
            new_words = [synonym if word == random_word else word for word in new_words]
            num_replaced += 1
            if num_replaced >= n: 
                break

    sentence = ' '.join(new_words)
    new_words = sentence.split(' ')

    return new_words

def eda(sentence, alpha_sr=0.1, alpha_ri=0.1, alpha_rs=0.1, p_rd=0.1, num_aug=8):
    sentence = get_only_chars(sentence)
    words = sentence.split(' ')
    words = [word for word in words if word is not '']
    num_words = len(words)
    augmented_sentences = []
    num_new_per_technique = int(num_aug/4)+1

    #sr
    if (alpha_sr > 0):
        n_sr = max(1, int(alpha_sr*num_words))
        for _ in range(num_new_per_technique):
            a_words = synonym_replacement(words, n_sr)
            augmented_sentences.append(' '.join(a_words))

    #ri
    # if (alpha_ri > 0):
	    # n_ri = max(1, int(alpha_ri*num_words))
    	# for _ in range(num_new_per_technique):
	    # a_words = random_insertion(words, n_ri)
	    # augmented_sentences.append(' '.join(a_words))

    #rs
    if (alpha_rs > 0):
        n_rs = max(1, int(alpha_rs*num_words))
        for _ in range(num_new_per_technique):
            a_words = random_swap(words, n_rs)
            augmented_sentences.append(' '.join(a_words))

    #rd
    if (p_rd > 0):
        for _ in range(num_new_per_technique):
            a_words = random_deletion(words, p_rd)
            augmented_sentences.append(' '.join(a_words))

    augmented_sentences = [get_only_chars(sentence) for sentence in augmented_sentences]
    shuffle(augmented_sentences)

    #trim so that we have the desired number of augmented sentences
    if num_aug >= 1:
    	augmented_sentences = augmented_sentences[:num_aug]
    else:
        keep_prob = num_aug / len(augmented_sentences)
        augmented_sentences = [s for s in augmented_sentences if random.uniform(0, 1) < keep_prob]

    #append the original sentence
    augmented_sentences.append(sentence)

    return augmented_sentences

def augment_dataset(true_tweets):
  new_true_tweets = pd.Series()
  for sentence in true_tweets:
    aug_sentences = eda(sentence, num_aug=4)
    new_true_tweets = new_true_tweets.append(pd.Series(aug_sentences))
  return new_true_tweets.reset_index(drop=True)
