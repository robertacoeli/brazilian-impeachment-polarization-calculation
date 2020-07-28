'''
Generates the GML and Pajek files from the retweet network

input: file "retweet_net.txt".

output: .gml and .net files. The output files will be placed in the same folder of the input file.

'''
import networkx as nx
from datetime import datetime
import os
from bisect import bisect_left
import json

# Method to generate the GML
def getRetweetNetworkGML(filename):
    outfolder = os.path.dirname(filename)
    newFilename = os.path.basename(filename).split(".")[0]
    rowCount = 0
    graph = nx.DiGraph()

    # open "retweet_net.txt" and generates the graph from it.
    netfile = open(filename, "r")
    for line in netfile:
        if (rowCount % 5000) == 0:
            print("Reading line %d of file %s" % (rowCount, newFilename))
        
        # example of line of the input file:
        # userA;userA_Id;userB;userB_Id;date_of_tweet;tweet_id;cleaned_tweet

        edge = line.strip().split(";")
        userAId = edge[1]
        userBId = edge[3]

        # Add the new nodes if they do not exist
        if not graph.has_node(userAId):
            graph.add_node(userAId)
        if not graph.has_node(userBId):
            graph.add_node(userBId)

        # If the edge exists, updates it (add + 1 to its weight). Otherwise, creates a new edge having weight 1.
        if graph.has_edge(userAId, userBId):
            graph[userAId][userBId]['weight'] += 1
        else:
            graph.add_edge(userAId, userBId, weight=1)
        rowCount += 1

    netfile.close()

    # outputs the graph to a GML and a Pajek file
    print("Writing to the GML output file")
    gmlFilename = os.path.join(outfolder, "%s.gml" % newFilename)
    nx.write_gml(graph, gmlFilename)

    print("Writing to the Pajek output file")
    netFilename = os.path.join(outfolder, "%s.net" % newFilename)
    nx.write_pajek(graph, netFilename)

if __name__ == "__main__":
    filename = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Deputados/" \
               "RetweetNetwork/retweet_net.txt"
    getRetweetNetworkGML(filename)