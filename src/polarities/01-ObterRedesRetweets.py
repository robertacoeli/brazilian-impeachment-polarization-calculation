'''
Generate retweet networks for the users in the database.
'''
import os
import sys
import time
import json
from datetime import datetime
import dateutil.parser as dateparser
from unidecode import unidecode

# internal modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'preprocessing'))
import preprocessing_tweet as ptw
from timeout import timeout
import utils

# current folder
current_folder = os.getcwd()

# results' folder
RESULTS_FOLDER = os.path.join(current_folder, "results/")
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

# current time
current_time = time.strftime("%Y%m%d_%H%M%S")

class ObterRedesRetweets:

    def __init__(self, inputFile, outFolder):
        self.inputFile = utils.open_file(inputFile)
        if not os.path.exists(outFolder):
            os.makedirs(outFolder)
        self.outfolder = outFolder
        self.total_tweets = 0
        self.total_retweets = 0

    # write_progress: allows to write some info to a progress file
    def write_progress(self, text_to_write):
        progfile = open(os.path.join(self.outfolder, "PROGRESS.txt"), "a")
        progfile.write(text_to_write + "\n")
        progfile.close()

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

    # open_writing_files: open files that will be written during the whole execution
    def open_writing_files(self):
        self.retweet_net = open(os.path.join(self.outfolder, "retweet_net.txt"), "w",
                                encoding="utf-8")
        self.retweet_net.write("User A;User A ID;User B;User B ID;Date;Tweet ID;Original Tweet Text\n")

    # close_writing_files: close files that were written during the whole execution
    def close_writing_files(self):
        self.retweet_net.close()

    def writeStatistics(self):
        sfile = open(os.path.join(self.outfolder, "GeneralInfo.txt"), "w", encoding="utf-8")
        retweetPerc = (self.total_retweets / self.total_tweets) * 100
        sfile.write("Total of Tweets: %d\n" % self.total_tweets)
        sfile.write("Total of Retweets (edges): %d\n" % self.total_retweets)
        sfile.write("Percentual of Retweets: %.2f%%" % retweetPerc)
        sfile.close()

    # run_from_file: characterization for a unique file
    def run_from_file(self):
        if self.inputFile is None:
            print("[ERROR] Input file was not set")
        else:
            self.open_writing_files()
            self.getRetweetNetwork()
            self.writeStatistics()
            self.close_writing_files()

    # get the retweet network
    def getRetweetNetwork(self):
        for line in self.inputFile:
            if self.total_tweets % 5000 == 0:
                self.write_progress("Reading Tweet no. " + str(self.total_tweets))
            with timeout(seconds=60):
                try:
                    self.total_tweets += 1
                    tweet = json.loads(line.decode('utf-8'))

                    if "retweeted_status" in tweet:
                        self.total_retweets += 1

                        # Obtem os atributos necessarios do tweet
                        (cleaned_tweet, tweet_tokens) = ptw.preprocess_text(tweet["retweeted_status"]["text"])
                        tid = tweet["id_str"]
                        date_decoded = self.get_date_tweet(tweet["created_at"])
                        dateString = date_decoded.strftime("%Y/%m/%d")
                        userA = unidecode(tweet["retweeted_status"]["user"]["screen_name"]).lower()
                        userAId = tweet["retweeted_status"]["user"]["id_str"]
                        userB = unidecode(tweet["user"]["screen_name"]).lower()
                        userBId = tweet["user"]["id_str"]
                        self.retweet_net.write("%s;%s;%s;%s;%s;%s;%s\n" % (userA, userAId, userB, userBId, dateString, tid, cleaned_tweet))

                except TimeoutError:
                    print("[TIMEOUT-ERROR] Timeout on " + str(self.total_tweets))

# MAIN
if __name__ == "__main__":
    currentDate = datetime.today()

    # input: file containing the set of tweets to be analyzed
    inputFile = "/home/robertacoeli/Documents/Pesquisa/Databases/deputados_twitter.gz"

    # output folder: where the output file ("retweet_net.txt") is placed. It contains all the existent connections between the user and the retweeted one.
    # Example of a line of the output file: userA;userA_Id;userB;userB_Id;date_of_tweet;tweet_id;cleaned_tweet
    outputFolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Deputados/RetweetNetwork"
    
    # call the script functions
    obterRedes = ObterRedesRetweets(inputFile, outputFolder)
    obterRedes.run_from_file()