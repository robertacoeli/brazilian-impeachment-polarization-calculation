'''
preprocessing_tweet.py: contains methods to preprocess a tweet
'''
from nltk.corpus import stopwords
from nltk.stem.snowball import PortugueseStemmer
from nltk.tokenize import word_tokenize
import re
from unidecode import unidecode
import string
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
stemming_allowed = False

# punctuation translator: remove punctuations from text
special_punctuation_translator = str.maketrans({key: None for key in "-_"})
punctuation_translator = str.maketrans({key: " " for key in string.punctuation})

# repeated_letters_pattern: regular expression to remove repeated letters from text
repeated_letters_pattern = re.compile(r"(.)\1{1,}", re.DOTALL)

# stop_words: load stop words' set
stop_words = set()
for line in open(os.path.join(dir_path, "stopwords_ptbr"), "r", encoding="utf-8"):
    stop_words.add(unidecode(line.strip()).lower())
for word in stopwords.words('english'):
    stop_words.add(unidecode(word).lower())

# abbreviations dictionary: get abbreviations from Internet to "translate" text
abbv_dict = dict()
abbvfile = open(os.path.join(dir_path, "abreviacoes_portugues"), "r", encoding="utf-8")
for line in abbvfile:
    lsplit = line.strip().split(":")
    abbv_dict[unidecode(lsplit[0])] = unidecode(lsplit[1])
abbvfile.close()

# stemmer: portuguese stemmer in nltk with sets of rules to process text
stemmer = PortugueseStemmer()

# replace_abbreviations: replace abbreviations from text
def replace_abbreviations(text_tokens):
    new_tokens = []
    for tt in text_tokens:
        if tt in abbv_dict:
            new_tokens.append(abbv_dict[tt])
        else:
            new_tokens.append(tt)
    return new_tokens

# remove_repeated_letters: remove letters that repeat on text
def remove_repeated_letters(text):
    return repeated_letters_pattern.sub(r"\1\1", text)

# remove_punctuation: remove punctuation from text
def remove_punctuation(text):
    cleaned_text = text.translate(special_punctuation_translator).lower()
    cleaned_text = cleaned_text.translate(punctuation_translator).lower()
    return cleaned_text

# remove_numbers: remove numbers from text
def remove_numbers(text):
    numbers_money = re.sub(r"R?\$", " dinheiro ", text)
    return re.sub(r"(?:\d*\.)?\d+", "", numbers_money)

# remove_urls: remove urls from text
def remove_urls(text):
    no_urls_text = re.sub(
        r"[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?",
        "", text)
    no_urls_text = re.sub(r"\b[http(s)?:%_\+.~#?&//=]{2,256}[\S]*", "", no_urls_text)
    return re.sub(
        r"[http(s)?:%_\+.~#?&//=]{2,256}(\.|:|\/)", "", no_urls_text)

def remove_twitter_elements(text):
    cleaned_text = re.sub(r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", " ", text) # remove hashtags
    cleaned_text = re.sub(r'(?:@[\w_]+)', " ", cleaned_text) # remove mentions
    cleaned_text = re.sub(r"(\b[vV]ia\b)+", "", cleaned_text) # remove "via"
    cleaned_text = re.sub(r"(\b[Rr][tT]\b)+", "", cleaned_text)  # remove RT
    cleaned_text = re.sub(r"\b(kk|rs|ha|hau|hua|hue)+", "risadas", cleaned_text)  # substitui risadas
    return cleaned_text

def remove_incomplete(text):
    return re.sub(r"(\w)*[(\.)]{2,}", "", text)

# remove_extra_spacing: remove additional spacing in text
def remove_extra_spacing(text):
    return re.sub("[\n\t\r ]+", " ", text)

# remove_stop_words: remove stop words from text
def remove_stop_words(text_tokens):
    return [term for term in text_tokens if (term not in stop_words) and (len(term) > 1)]

# preprocess_text: sequence of steps to preprocess text
def preprocess_text(text):
    # proc_text = remove_twitter_elements(text)
    proc_text = remove_extra_spacing(text)
    proc_text = remove_urls(proc_text)
    proc_text = remove_numbers(proc_text)
    proc_text = unidecode(proc_text).lower()
    proc_text = remove_incomplete(proc_text)
    proc_text = remove_punctuation(proc_text)
    proc_text = remove_repeated_letters(proc_text)
    proc_text = remove_twitter_elements(proc_text)
    proc_tokens = word_tokenize(proc_text)
    proc_tokens = replace_abbreviations(proc_tokens)
    proc_tokens = remove_stop_words(proc_tokens)
    if stemming_allowed:
        proc_tokens = [stemmer.stem(tt) for tt in proc_tokens]
    proc_text = " ".join(proc_tokens)
    return (proc_text, proc_tokens)