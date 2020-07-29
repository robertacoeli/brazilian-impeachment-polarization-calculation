''' 
    Finds users that posted the selected hashtags (see "hashtags_groups.txt" --> folder "files").

    input: the dataset of tweets.

    output: files containing an array of the users of each hashtag group (favoravel, contrario, favcont, incerto)
'''

# imports.
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

    def __init__(self, input_file, output_basic_filename):
        self.input_filename = input_file
        self.output_basic_filename = output_basic_filename

        # hashtags for each group
        self.hashtags_groups = dict()
        self.hashtags_groups["favoravel"], self.hashtags_groups["contrario"], \
        self.hashtags_groups["incerto"]= [], [], []
        group_mode = ""
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

    # check for hashtags in the tweet
    def check_special_feature(self, hashtags, checked_hashtags):
        for htg in hashtags:
            htg_proc = unidecode(htg).lower()
            for checked_htg in checked_hashtags:
                if checked_htg in htg_proc:
                    return True
        return False

    ''' MAIN FUNCTION'''
    def run(self):
        self.users_groups = dict()
        self.users_groups["favoravel"], self.users_groups["contrario"], \
        self.users_groups["incerto"], self.users_groups["favcont"] = Counter(), Counter(), \
                                                                      Counter(), Counter()

        # reading the database
        data_file = utils.open_file(self.input_filename)
        for line in data_file:
            # loads the tweet
            tweet = json.loads(line.decode('utf-8'))

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

        # check users per hashtag group
        favoravel_users, contrario_users, incerto_users, favcont_users = set(), set(), \
                                                                         set(), set()
        favoravel_users.update([u for (u,_) in self.users_groups["favoravel"].items()])
        contrario_users.update([u for (u,_) in self.users_groups["contrario"].items()])
        incerto_users.update([u for (u,_) in self.users_groups["incerto"].items()])
        favcont_users.update([u for (u,_) in self.users_groups["favcont"].items()])

        # check the intersections: users that are in more than one group
        check_group = favoravel_users.intersection(contrario_users)
        for u in check_group:
            cf = self.users_groups["favoravel"][u]
            cc = self.users_groups["contrario"][u]
            cfc = self.users_groups["favcont"][u]

            # if the counter in "favcont" > "favoravel" or "favcont" > "contrario" or "favoravel" = "contrario", remove the user from the "favoravel" and "contrario" groups
            # in other words: a user is "favoravel" or "contrario" if their total of hashtags of these "extreme" groups are greater than the other ones
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

        # after the previous verification...
        # "favoravel" users that are also in "favcont" group are removed from "favcont"
        check_group = favoravel_users.intersection(favcont_users)
        for u in check_group:
            favcont_users.remove(u)
            del self.users_groups["favcont"][u]

        # "contrario" users that are also in "favcont" group are removed from "favcont"
        check_group = contrario_users.intersection(favcont_users)
        for u in check_group:
            favcont_users.remove(u)
            del self.users_groups["favcont"][u]

        # "favoravel" users that are also in "incerto" group are removed from "incerto"
        check_group = favoravel_users.intersection(incerto_users)
        for u in check_group:
            incerto_users.remove(u)
            del self.users_groups["incerto"][u]

        # "contrario" users that are also in "incerto" group are removed from "incerto"
        check_group = contrario_users.intersection(incerto_users)
        for u in check_group:
            incerto_users.remove(u)
            del self.users_groups["incerto"][u]

        favoravel_users = list(favoravel_users)
        contrario_users = list(contrario_users)
        incerto_users = list(incerto_users)
        favcont_users = list(favcont_users)

        # write to json files
        print("Writing to output files...")
        with open(self.output_basic_filename + "_FAVORAVEL_" + current_time + ".json", "w") as FFile:
            json.dump(favoravel_users, FFile)

        with open(self.output_basic_filename + "_CONTRARIO_" + current_time + ".json", "w") as CFile:
            json.dump(contrario_users, CFile)

        with open(self.output_basic_filename + "_INCERTO_" + current_time + ".json", "w") as IFile:
            json.dump(incerto_users, IFile)

        with open(self.output_basic_filename + "_FAVCONT_" + current_time + ".json", "w") as FCFile:
            json.dump(favcont_users, FCFile)

        print("FINISHED!")

''' ------------------------------------------------------ 
    MAIN : calls the main class method!
    ------------------------------------------------------ 
'''
if __name__ == "__main__":
    input_file = "/home/robertacoelineves/TwitterDatabases/TweetsFiltradosPublico/tweets_2016.gz"
    output_basic_filename = "/Users/robertacoeli/Documents/Mestrado/Pesquisa/Results/Twitter/Publico/PorGrupo_2017_07/TweetsPublico2016_CentralHashtagsOnly"
    pt = ProcessingText(input_file, output_basic_filename)
    pt.run()