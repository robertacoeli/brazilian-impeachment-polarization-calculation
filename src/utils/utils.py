'''
utils.py: some useful methods
'''
import gzip
from nltk.corpus import stopwords
from nltk import wordpunct_tokenize

# open_file: allows to identify if file is gz or not and open it properly
def open_file(file):
    if ".gz" in file:
        return gzip.open(file, "r")
    else:
        return open(file, "r")

# basic methods to detect language in text
PT_STOPWORDS = set(stopwords.words('portuguese'))
NON_PT_STOPWORDS = set(stopwords.words()) - PT_STOPWORDS

STOPWORDS_DICT = {lang: set(stopwords.words(lang)) for lang in stopwords.fileids()}

def get_language(text):
    words = set(wordpunct_tokenize(text.lower()))
    return max(((lang, len(words & stopwords)) for lang, stopwords in STOPWORDS_DICT.items()), key = lambda x: x[1])[0]

def is_portuguese(text):
    text = text.lower()
    words = set(wordpunct_tokenize(text))
    return len(words & PT_STOPWORDS) > len(words & NON_PT_STOPWORDS)

# find_month: put month in written form
def find_month(month_number):
    if month_number == 1:
        return "Jan"
    elif month_number == 2:
        return "Feb"
    elif month_number == 3:
        return "Mar"
    elif month_number == 4:
        return "Apr"
    elif month_number == 5:
        return "May"
    elif month_number == 6:
        return "Jun"
    elif month_number == 7:
        return "Jul"
    elif month_number == 8:
        return "Aug"
    elif month_number == 9:
        return "Sep"
    elif month_number == 10:
        return "Oct"
    elif month_number == 11:
        return "Nov"
    else:
        return "Dec"

def find_reverse_month(month):
    if month == "Jan":
        return 1
    elif month == "Feb":
        return 2
    elif month == "Mar":
        return 3
    elif month == "Apr":
        return 4
    elif month == "May":
        return 5
    elif month == "Jun":
        return 6
    elif month == "Jul":
        return 7
    elif month == "Aug":
        return 8
    elif month == "Sep":
        return 9
    elif month == "Oct":
        return 10
    elif month == "Nov":
        return 11
    elif month == "Dec":
        return 12
    else:
        return None
