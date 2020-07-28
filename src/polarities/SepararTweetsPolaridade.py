'''
    Script para separar tweets de acordo com os usuários que foram previamente
    classificados como favoráveis, contrários, incertos ou "neutros" ao impeachment
'''
# Módulos Externos
import os
import sys
import json
from datetime import datetime
from bisect import bisect_left
import gzip

# Módulos Internos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'preprocessing'))
import preprocessing_tweet as ptw
from timeout import timeout
import utils

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))

currentDate = datetime.today()
LIMIT_PURE_TWEETS = 5000

# Classe Principal
class SepararTweetsPolaridade:

    def __init__(self, inputFile, outputFolder, polaridades, usersFiles):
        self.inputFilename = inputFile
        self.inputFile = utils.open_file(inputFile)
        self.outputFolder = outputFolder
        self.polaridades = polaridades

        # Carrega as listas de usuários nos respectivos arrays
        self.usersIds = dict()
        for (polId, uFilename) in usersFiles.items():
            with open(uFilename, "r") as uFile:
                self.usersIds[polId] = json.load(uFile)

        # Variáveis para Computar Estatísticas:
        self.total_tweets = 0
        self.positionCounter = dict()
        for pol in self.polaridades:
            self.positionCounter["TWEETS_%s" % pol] = 0

    def openWritingFiles(self):
        self.positionFiles = dict()
        self.pureTweetsFiles = dict()
        for pol in self.polaridades:
            self.positionFiles["TWEETS_%s" % pol] = gzip.open(os.path.join(self.outputFolder,
                                                                           "tweets_%s.gz" % pol.capitalize()), "w")
            # self.pureTweetsFiles["TWEETS_%s" % pol] = open(os.path.join(self.outputFolder,
            #                                                                "sample_tweets_%s.txt" % pol.capitalize()), "w")
            # self.pureTweetsFiles["TWEETS_%s" % pol].write("TWEET_ID;USER_ID;USER_SCREEN_NAME;TWEET_TXT\n")

    def closeWritingFiles(self):
        for pol in self.polaridades:
            self.positionFiles["TWEETS_%s" % pol].close()

    def writeStatistics(self):
        outfile = open(os.path.join(self.outputFolder, "STATISTICS.txt"), "w", encoding="utf-8")
        outfile.write("-------------- Final Data -------------\n")
        outfile.write("Total of Tweets: %d\n" % self.total_tweets)
        for pol in self.polaridades:
            outfile.write("Total de Tweets de Usuários de Posição %s: %d\n" %
                          (pol.capitalize(), self.positionCounter["TWEETS_%s" % pol]))
        outfile.close()

    # write_progress: permite verificar o progresso do processamento do arquivo
    def write_progress(self, text_to_write):
        progfile = open(os.path.join(self.outputFolder, "PROGRESS.txt"), "a")
        progfile.write(text_to_write + "\n")
        progfile.close()

    # binary_search: busca binária de ids de tweets (para verificar se nenhum se repete)
    def binary_search(self, array_search, x, lo=0, hi=None):  # can't use a to specify default for hi
        hi = hi if hi is not None else len(array_search)  # hi defaults to len(a)
        pos = bisect_left(array_search, x, lo, hi)  # find insertion position
        isfound = (pos if pos != hi and array_search[pos] == x else -1)
        return (isfound, pos)  # don't walk off the end

    # writeToPureFile: escreve no arquivo mais simples de tweets
    def writeToPureFile(self, pol, text):
        if self.positionCounter["TWEETS_%s" % pol] == 5000:
            self.pureTweetsFiles["TWEETS_%s" % pol].close()
        elif self.positionCounter["TWEETS_%s" % pol] < 5000:
            self.pureTweetsFiles["TWEETS_%s" % pol].write(text)

    # processTweets: filtra base de acordo com os usuários de cada
    # polaridade e obtem estatísticas
    def processTweets(self):
        for line in self.inputFile:
            if self.total_tweets % 5000 == 0:
                self.write_progress("Leitura de tweet # %d" % self.total_tweets)
            with timeout(seconds=60):
                try:
                    tweet = json.loads(line.decode('utf-8'))
                    (cleaned_tweet, _) = ptw.preprocess_text(tweet["text"])

                    # verifica os tweets de cada polaridade
                    tuserid = tweet["user"]["id_str"]
                    for pol in self.polaridades:
                        (isfound, pos) = self.binary_search(self.usersIds[pol], int(tuserid))
                        if isfound > 0:
                            self.positionCounter["TWEETS_%s" % pol] += 1
                            self.positionFiles["TWEETS_%s" % pol].write(line)
                            # self.writeToPureFile(pol, "%s;%s;%s;%s\n" % (tweet["id_str"], tuserid,
                            #                                              tweet["user"]["screen_name"],
                            #                                              cleaned_tweet))
                            break

                    self.total_tweets += 1

                except TimeoutError:
                    print("[TIMEOUT-ERROR] Timeout on %d" % self.total_tweets)
                    self.write_progress("[TIMEOUT-ERROR] Timeout on %d" % self.total_tweets)

    def run(self):
        self.openWritingFiles()
        self.processTweets()
        self.writeStatistics() # apenas para mostrar algumas características dos tweets removidos
        self.closeWritingFiles()
        self.write_progress("FINISHED!")

# Fim de SepararTweetsPolaridade

#
# FUNÇÃO PRINCIPAL
#
if __name__ == "__main__":

    # polaridades = ["FAVCONT", "FAVORAVEL", "CONTRARIO", "INCERTO"]
    polaridades = ["FAVORAVEL", "CONTRARIO"]

    # base de dados para investigar:
    # databaseFile = "/Volumes/Roberta/Mestrado/Databases/tweets_2016_central_hashtags_only.gz"
    databaseFile = "/home/robertacoelineves/TwitterDatabases/" \
                   "TweetsFiltradosPublico/tweets_2016.gz"

    # arquivo de saída:
    # outfolder = os.path.join(os.path.dirname(databaseFile), "Analise_%s" % currentDate.strftime("%d%b%Y"))
    outfolder = os.path.join("/home/robertacoelineves/TwitterDatabases/TweetsFiltradosPublico",
                             "TweetsAmostraUsuariosPolaridade_%s" % currentDate.strftime("%d%b%Y"))
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    # arrays de usuários de cada polaridade:
    rootFolder = "/home/robertacoelineves/TwitterDatabases/PolaridadeUsuariosAmostra"
    usersFiles = dict()
    fileBasename = "TweetsPublico2016_CentralHashtagsOnly_"
    for pol in polaridades:
        usersFiles[pol] = os.path.join(rootFolder, "%s%s.json" % (fileBasename, pol))

    # separa os arquivos
    separarPolaridade = SepararTweetsPolaridade(databaseFile, outfolder, polaridades, usersFiles)
    separarPolaridade.run()