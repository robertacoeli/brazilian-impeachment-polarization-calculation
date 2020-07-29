''' 
    Script to add the polarity data for the users that were labeled by the hashtags in the retweet networks

    Here we regenerate the .gml files so that it contains the polarity/label for the users that were labeled by the hashtags. 
    This is done in order to calculate the individual polarity for the "unlabeled" users afterwards.
'''
import networkx as nx
from datetime import datetime
import os
from bisect import bisect_left
import json

# output folder
outfolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/Experimentos_Redes_Retweets_v2/" \
             "Arquivos_Redes/RedesRetweets_Atualizadas_Maio2018"

# folder containing the .gml files (input)
infolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/Experimentos_Redes_Retweets_v2/" \
           "Arquivos_Redes/RedesRetweets_Antigas"

# folder having the files containing the users labeled for each hashtag group --> example: folder "hashtag_labeled_users" (https://drive.google.com/drive/folders/1LivGb9Nddbl2FByLqq6yPezBHxRzfBpT?usp=sharing)
polarityFolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/" \
                 "Publico/Experimentos_Redes_Retweets_v2/PolaridadeUsuariosAmostra/AmostrasIguais/" \
                 "TweetsPublico2016_CentralHashtagsOnly_%s.json"

# we only consider the "extreme" positions ("favoravel" and "contrario")
polaridades = ["CONTRARIO", "FAVORAVEL"]

polarityArray = dict()
for pol in polaridades:
    with open(polarityFolder % pol, "r") as pfile:
        polarityArray[pol] = json.load(pfile)
        polarityArray[pol].sort()

# to optimize the search of users
def binary_search(array_search, x, lo=0, hi=None):  # can't use a to specify default for hi
    hi = hi if hi is not None else len(array_search)  # hi defaults to len(a)
    pos = bisect_left(array_search, x, lo, hi)  # find insertion position
    isfound = (pos if pos != hi and array_search[pos] == x else -1)
    return (isfound, pos)  # don't walk off the end

# find it the user was labeled by hashtag
def buscarPolaridade(userId):
    for pol in polaridades:
        (isfound, pos) = binary_search(polarityArray[pol], userId)
        if isfound > 0:
            return pol
    return "None"

# add the "polarity"/label information for the users (nodes) that were labeled by the selected hashtags
# this information is added to the graph in order to calculate the individual polarity for the "unlabeled" users afterwards
def modificar_polaridades_grafo(arquivo_grafo):
    grafo = nx.read_gml(arquivo_grafo)

    for (id_usuario, props_usuario) in grafo.nodes(data=True):
        polaridade_usuario = buscarPolaridade(int(id_usuario))
        grafo.node[id_usuario]["polaridade"] = polaridade_usuario

    return grafo

# regenerate the .gml files containing the polarity/label for the users that were labeled by the hashtags
def regerarGML(input_folder):
    # for each .gml file in the input folder...
    for root, subdirs, files in os.walk(input_folder):
        for monthFolder in subdirs:
            pasta_mensal_nova = os.path.join(outfolder, monthFolder)
            if (not os.path.exists(pasta_mensal_nova)):
                os.makedirs(pasta_mensal_nova)

            for filename in os.listdir(os.path.join(root, monthFolder)):
                print("Processando {0}/{1}".format(monthFolder, filename))
                completeFilename = os.path.join(root, monthFolder, filename)
                nome_novo_arquivo = os.path.join(pasta_mensal_nova, filename)
                grafo_novo = modificar_polaridades_grafo(completeFilename)
                nx.write_gml(grafo_novo, nome_novo_arquivo)

            print("\n" * 3)

    print("Finalizado!")

### MAIN
if __name__ == "__main__":
    print("Iniciando...")
    regerarGML(infolder)