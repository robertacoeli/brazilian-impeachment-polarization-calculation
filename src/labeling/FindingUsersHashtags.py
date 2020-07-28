''' 
    Finds users that posted the selected hashtags (see "central_hashtags.txt" and "hashtags_groups.txt" --> folder "files").

    input:

    output:
'''

# imports.
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import bigrams
from unidecode import unidecode
from collections import Counter
import gzip
import json
import time
import string
import os
from urllib.parse import urlparse
import pickle
import re
from datetime import datetime
import dateutil.parser as dateparser
import detect_language as dlang
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
import utils
from timeout import timeout
import numpy as np
from bisect import bisect_left

current_time = time.strftime("%Y%m%d_%H%M%S")
SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

# class that cleans and processes the tweets
class ProcessingText:

    def __init__(self, input_file, filesfolder, filename):
        self.input_filename = input_file
        self.filesfolder = filesfolder
        self.filename = filename

        self.punctuation_translator = str.maketrans({key: None for key in string.punctuation})
        self.stop_words = [unidecode(word).lower() for word in stopwords.words('portuguese') +  stopwords.words('english')]
        self.repeated_letters_pattern = re.compile(r"(.)\1{1,}", re.DOTALL)

        #self.specificfiles = ["TweetsPublico2016_CentralHashtagsOnly.gz"]

        self.most_common_terms = 100
        self.most_common_bigrams = 100
        self.most_common_hashtags = 100
        self.most_common_mentions = 100
        self.most_common_url_domains = 200
        self.most_common_locations = 40

        # hashtags / group
        self.hashtags_groups = dict()
        self.hashtags_groups["favoravel"], self.hashtags_groups["contrario"], \
        self.hashtags_groups["incerto"]= [], [], []
        group_mode = "nada"
        hgfile = open(os.path.join(SCRIPT_FOLDER, "hashtags_groups.txt"), "r")
        for line in hgfile:
            l = line.strip()
            if l == "::favoravel::":
                group_mode = "favoravel"
            elif l == "::contrario::":
                group_mode = "contrario"
            elif l == "::incerto::":
                group_mode = "incerto"
            else:
                self.hashtags_groups[group_mode].append(l)

    def print_results(self, outfile):
        outfile.write("-------------- Final Data -------------\n")
        outfile.write("Total of Tweets: " + str(self.total_tweets) + "\n")
        outfile.write("Total of Users: " + str(self.total_users) + "\n")
        outfile.write("\n\nStart Period: " + self.start_date.strftime("%B %d, %Y"))
        outfile.write("\nFinal Period: " + self.final_date.strftime("%B %d, %Y"))
        cf = len(self.users_groups["favoravel"].items())
        cc = len(self.users_groups["contrario"].items())
        cfc = len(self.users_groups["favcont"].items())
        ci = len(self.users_groups["incerto"].items())
        ctotal_users = cf + cc + cfc + ci
        outfile.write("\n\n**** Number of users / hashtag group ****\n")
        outfile.write("Favoravel users: " + str(cf) + "\n")
        outfile.write("Contrario users: " + str(cc) + "\n")
        outfile.write("FavCont users: " + str(cfc) + "\n")
        outfile.write("Incerto users: " + str(ci) + "\n")
        outfile.write("Total: " + str(ctotal_users) + "\n")
        # outfile.write("\n\nMost Common Hashtags:")
        # for mc in self.count_hashtags.most_common(self.most_common_hashtags):
        #     outfile.write(str(mc) + "\n")

    def remove_repeated_letters(self, text):
        return self.repeated_letters_pattern.sub(r"\1\1", text)

    def remove_numbers(self, text):
        return re.sub(r"(?:\d*\.)?\d+", "", text)

    def remove_urls(self, text):
        no_urls_text = re.sub(
            r"[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?",
            "", text)
        return re.sub(
            r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[\-;:&=\+\$,\w]+@)?[A-Za-z0-9\.\-]+|(?:www\.|[\-;:&=\+\$,\w]+@)[A-Za-z0-9\.\-]+)((?:\/[\+~%\/\.\w\-_]*)?\??(?:[\-\+=&;%@\.\w_]*)#?(?:[\.\!\/\\\w]*))?)",
            "", no_urls_text)

    def remove_stop_words(self, tweet_tokens):
        return [unidecode(term).lower() for term in tweet_tokens if unidecode(term).lower() not in self.stop_words]

    def remove_extra_spacing(self, text):
        return re.sub(" +", " ", text)

    def clean_tweet(self, tweet_text):
        # proc_text = p.clean(tweet_text)
        proc_text = self.remove_urls(proc_text)
        cleaned_tweet = self.remove_extra_spacing(proc_text)
        cleaned_tweet = cleaned_tweet.translate(self.punctuation_translator).lower()
        cleaned_tweet = re.sub(r"[\n\t\r]+", "", cleaned_tweet)
        cleaned_tweet = re.sub(r"(\b[vV]ia\b)+", "", cleaned_tweet)
        return unidecode(cleaned_tweet.strip())

    def check_central_term(self, tt_tokens, terms):
        if len(tt_tokens) <= 0:
            return False

        for checked_tweet_word in tt_tokens:
            for tm in terms:
                if tm in checked_tweet_word:
                    return True
        return False

    # check for hashtags in the tweet
    def check_special_feature(self, hashtags, checked_hashtags):
        for htg in hashtags:
            htg_proc = unidecode(htg).lower()
            for checked_htg in checked_hashtags:
                if checked_htg in htg_proc:
                    return True
        return False

    def check_in_text(self, text_to_check, checked_terms):
        for tm in checked_terms:
            if tm in text_to_check:
                return True
        return False

    # get_date_tweet: return the date from the tweet
    def get_date_tweet(self, tweet_date):
        date_decoded = datetime(1980, 1, 1)
        if tweet_date is not None:
            if type(tweet_date) == str:
                date_decoded = datetime.strptime(tweet_date, "%a %b %d %H:%M:%S +0000 %Y")
            elif "$date" in tweet_date:
                if type(tweet_date["$date"]) == str:
                    date_decoded = dateparser.parse(tweet_date["$date"])
                    date_decoded.replace(tzinfo=None)
                else:
                    date_decoded = datetime.fromtimestamp(tweet_date["$date"] / 1000)
        return date_decoded

    def binary_search(self, array_search, x, lo=0, hi=None):  # can't use a to specify default for hi
        hi = hi if hi is not None else len(array_search)  # hi defaults to len(a)
        pos = bisect_left(array_search, x, lo, hi)  # find insertion position
        isfound = (pos if pos != hi and array_search[pos] == x else -1)
        return (isfound, pos)  # don't walk off the end

    ''' MAIN FUNCTION'''
    def run(self):
        # counters
        # self.total_tweets = 0
        # self.count_hashtags = Counter()
        # self.total_users = 0
        # self.count_users = Counter()   # number of tweets per user
        # self.start_date = datetime.now()
        # self.final_date = datetime(1980,1,1)
        # self.users = np.array([], dtype=object)
        self.users_groups = dict()
        self.users_groups["favoravel"], self.users_groups["contrario"], \
        self.users_groups["incerto"], self.users_groups["favcont"] = Counter(), Counter(), \
                                                                      Counter(), Counter()

        # reading the database
        data_file = utils.open_file(self.input_filename)
        for line in data_file:
            # loads the tweet
            tweet = json.loads(line.decode('utf-8'))

            # find tweet date
            #date_decoded = self.get_date_tweet(tweet["created_at"])

            # identifies the hashtags
            tweet_hashtags = []
            if "entities" in tweet:
                if "hashtags" in tweet["entities"]:
                    tweet_hashtags = [htg["text"] for htg in tweet["entities"]["hashtags"]]
            
            # updates counter for hashtags (if there is any hashtag for the tweet)
            if len(tweet_hashtags) > 0:

                # checks if the tweet contains hashtags from any of the FAVORAVEL, CONTRARIO or INCERTO groups
                tuserid = tweet["user"]["id_str"]
                contains_favoravel = self.check_special_feature(tweet_hashtags, self.hashtags_groups["favoravel"])
                contains_contrario = self.check_special_feature(tweet_hashtags, self.hashtags_groups["contrario"])
                contains_incerto = self.check_special_feature(tweet_hashtags, self.hashtags_groups["incerto"])

                # if:
                # a) the tweet contains both FAVORAVEL and CONTRARIO hashtags, the author/user is counted as "favcont" for this tweet (counter increases +1 for the user "tuserid" in the label "favcont")
                # b) the tweet contains only FAVORAVEL, the author/user is counted as "favoravel" for this tweet (counter increases +1 for the user "tuserid" in the label "favoravel")
                # c) the tweet contains only CONTRARIO, the author/user is counted as "contrario" for this tweet (counter increases +1 for the user "tuserid" in the label "contrario")
                # d) the tweet contains INCERTO (hashtags incertas da posicao), the author/user is counted as "incerto" for this tweet (counter increases +1 for the user "tuserid" in the label "incerto")
                if contains_favoravel and contains_contrario:
                    self.users_groups["favcont"].update([tuserid]) # a
                elif contains_favoravel and (not contains_contrario):
                    self.users_groups["favoravel"].update([tuserid]) # b
                elif contains_contrario and (not contains_favoravel):
                    self.users_groups["contrario"].update([tuserid]) # c
                elif contains_incerto:
                    self.users_groups["incerto"].update([tuserid]) # d

        # check users per hashtag group (PAREI AQUI NA REVISAO)
        favoravel_users, contrario_users, incerto_users, favcont_users = set(), set(), \
                                                                         set(), set()
        favoravel_users.update([u for (u,_) in self.users_groups["favoravel"].items()])
        contrario_users.update([u for (u,_) in self.users_groups["contrario"].items()])
        incerto_users.update([u for (u,_) in self.users_groups["incerto"].items()])
        favcont_users.update([u for (u,_) in self.users_groups["favcont"].items()])

        check_group = favoravel_users.intersection(contrario_users)
        for u in check_group:
            cf = self.users_groups["favoravel"][u]
            cc = self.users_groups["contrario"][u]
            cfc = self.users_groups["favcont"][u]

            if ((cfc > cf) and (cfc > cc)) or (cf == cc):
                favoravel_users.remove(u)
                contrario_users.remove(u)
                del self.users_groups["favoravel"][u]
                del self.users_groups["contrario"][u]
            elif (cf > cc):
                if u in favcont_users:
                    favcont_users.remove(u)
                contrario_users.remove(u)
                del self.users_groups["favcont"][u]
                del self.users_groups["contrario"][u]
            else:
                if u in favcont_users:
                    favcont_users.remove(u)
                favoravel_users.remove(u)
                del self.users_groups["favcont"][u]
                del self.users_groups["favoravel"][u]

        check_group = favoravel_users.intersection(favcont_users)
        for u in check_group:
            favcont_users.remove(u)
            del self.users_groups["favcont"][u]

        check_group = contrario_users.intersection(favcont_users)
        for u in check_group:
            favcont_users.remove(u)
            del self.users_groups["favcont"][u]

        check_group = favoravel_users.intersection(incerto_users)
        for u in check_group:
            incerto_users.remove(u)
            del self.users_groups["incerto"][u]

        check_group = contrario_users.intersection(incerto_users)
        for u in check_group:
            incerto_users.remove(u)
            del self.users_groups["incerto"][u]

        outfile = open(self.filename + "_RESULTS_" + current_time + ".txt", "w",
                       encoding="utf-8")
        self.print_results(outfile)
        outfile.close()

        favoravel_users = list(favoravel_users)
        contrario_users = list(contrario_users)
        incerto_users = list(incerto_users)
        favcont_users = list(favcont_users)

        favoravel_users = [int(item) for item in favoravel_users]
        contrario_users = [int(item) for item in contrario_users]
        incerto_users = [int(item) for item in incerto_users]
        favcont_users = [int(item) for item in favcont_users]

        print("Ordenando arrays...")
        favoravel_users.sort()
        contrario_users.sort()
        incerto_users.sort()
        favcont_users.sort()
        print("Ordenação finalizada.")

        # write to json files
        print("Escrevendo em arquivos...")
        with open(self.filename + "_FAVORAVEL_" + current_time + ".json", "w") as FFile:
            json.dump(favoravel_users, FFile)

        with open(self.filename + "_CONTRARIO_" + current_time + ".json", "w") as CFile:
            json.dump(contrario_users, CFile)

        with open(self.filename + "_INCERTO_" + current_time + ".json", "w") as IFile:
            json.dump(incerto_users, IFile)

        with open(self.filename + "_FAVCONT_" + current_time + ".json", "w") as FCFile:
            json.dump(favcont_users, FCFile)

        print("FINISHED!")

''' ------------------------------------------------------ 
    MAIN : calls the main class method!
    ------------------------------------------------------ 
'''
if __name__ == "__main__":
    # filesfolder = "/Volumes/Roberta/Mestrado/Databases"
    filesfolder = "/Users/robertacoeli/Documents/Mestrado/Pesquisa/Databases/"
    input_file = "arquivo_de_tweets_base.gz"
    filename = "/Users/robertacoeli/Documents/Mestrado/Pesquisa/Results/Twitter/Publico/PorGrupo_2017_07/TweetsPublico2016_CentralHashtagsOnly"
    pt = ProcessingText(input_file, filesfolder, filename)
    pt.run()