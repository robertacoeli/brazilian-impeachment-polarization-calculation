import networkx as nx
from datetime import datetime
import os
from bisect import bisect_left
import json

outfolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/Experimentos_Redes_Retweets_v2/" \
             "Arquivos_Redes/RedesRetweets_Atualizadas_Maio2018"
infolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/Experimentos_Redes_Retweets_v2/" \
           "Arquivos_Redes/RedesRetweets_Antigas"
polarityFolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/" \
                 "Publico/Experimentos_Redes_Retweets_v2/PolaridadeUsuariosAmostra/AmostrasIguais/" \
                 "TweetsPublico2016_CentralHashtagsOnly_%s.json"
polaridades = ["CONTRARIO", "FAVORAVEL"]

polarityArray = dict()
for pol in polaridades:
    with open(polarityFolder % pol, "r") as pfile:
        polarityArray[pol] = json.load(pfile)
        polarityArray[pol].sort()

def buscarPolaridade(userId):
    for pol in polaridades:
        (isfound, pos) = binary_search(polarityArray[pol], userId)
        if isfound > 0:
            return pol
    return "None"

# binary_search: busca binária de ids de tweets (para verificar se nenhum se repete)
def binary_search(array_search, x, lo=0, hi=None):  # can't use a to specify default for hi
    hi = hi if hi is not None else len(array_search)  # hi defaults to len(a)
    pos = bisect_left(array_search, x, lo, hi)  # find insertion position
    isfound = (pos if pos != hi and array_search[pos] == x else -1)
    return (isfound, pos)  # don't walk off the end

def modificar_polaridades_grafo(arquivo_grafo):
    grafo = nx.read_gml(arquivo_grafo)

    for (id_usuario, props_usuario) in grafo.nodes(data=True):
        polaridade_usuario = buscarPolaridade(int(id_usuario))
        grafo.node[id_usuario]["polaridade"] = polaridade_usuario

    return grafo

def regerarGML(rootfolder):
    for root, subdirs, files in os.walk(rootfolder):
        for monthFolder in subdirs:
            print(monthFolder)
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

if __name__ == "__main__":
    print("Iniciando...")
    regerarGML(infolder)