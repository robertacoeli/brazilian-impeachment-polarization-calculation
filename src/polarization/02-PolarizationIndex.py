'''
    Computes the polarization index and its related variables for each month

    input: file containing the distribution of the individual polarities --> ex.: "DadosKDE_GranMensal.json" (google drive: https://drive.google.com/drive/folders/1LivGb9Nddbl2FByLqq6yPezBHxRzfBpT?usp=sharing)

    output: csv and json files containing the polarization metrics for each month --> ex.: "Metricas_Polarizacao_GranMensal.json" and "Metricas_Polarizacao_GranMensal.csv" (google drive, same link above)
'''

from scipy.integrate import quad
from sklearn.neighbors.kde import KernelDensity
import numpy as np
import os
import json
import csv

# Obtém o dicionário com os conjuntos de dados
def get_dictionary(filename):
    with open(filename, "r") as jfile:
        file_dict = json.load(jfile)
    return file_dict

# Computa o KDE do conjunto de dados
def compute_kernel(x, bandwidth):
    kde_skl = KernelDensity(bandwidth=bandwidth)
    kde_skl.fit(x[:, np.newaxis])
    return kde_skl

# Computa os valores
def run(filename, output_filename):
    print("Loading data...")
    data_dict = get_dictionary(filename)

    total_sets = len(data_dict.items())
    count = 0

    result_dict = dict()

    print("Computing values...")
    for key, vals in data_dict.items():
        count += 1
        print("Reading %s --> %d of %f items" % (key, count, total_sets))

        bandwidth = vals["bandwidth"]
        diff_array = np.array(vals["diff_array"])

        x_min = min(diff_array)
        x_max = max(diff_array)

        pdf = compute_kernel(diff_array, bandwidth)

        def kde_func(x):
            return np.exp(pdf.score_samples(x))

        def expect_kde(x):
            return np.exp(pdf.score_samples(x)) * x

        pop_neg, err = quad(kde_func, -1, 0) # densidade de individuos da populacao negativa -> A-
        pop_pos, err = quad(kde_func, 0, 1) # densidade de individuos da populacao positiva -> A+
        diff_pops = abs(pop_pos - pop_neg) # diferenca de densidade -> delta A

        exp_neg, err = quad(expect_kde, -1, 0) # esperanca de polaridade para pop negativa
        gc_neg = exp_neg/pop_neg               # centro de gravidade da pop negativa
        exp_pos, err = quad(expect_kde, 0, 1) # esperanca de polaridade para pop positiva
        gc_pos = exp_pos/pop_pos             # centro de gravidade da pop positiva

        dist_gc = abs(gc_pos - gc_neg) / abs(x_max - x_min) # distancia entre os centros de gravidade

        pol_index = (1 - diff_pops) * dist_gc       # polarization index

        result_dict[key] = dict()
        result_dict[key]["pop_neg"] = pop_neg
        result_dict[key]["pop_pos"] = pop_pos
        result_dict[key]["diff_pops"] = diff_pops
        result_dict[key]["gc_neg"] = gc_neg
        result_dict[key]["gc_pos"] = gc_pos
        result_dict[key]["dist_gc"] = dist_gc
        result_dict[key]["pol_index"] = pol_index

    # Salva no JSON
    print("Saving to JSON file...")
    with open(output_filename + ".json", "w") as jfile:
        json.dump(result_dict, jfile)

    # Salva no CSV
    print("Saving to CSV file...")
    with open(output_filename + ".csv", "w", newline="") as csvfile:
        fieldnames = ["key", "pop_neg", "pop_pos", "diff_pops", "gc_neg", "gc_pos", "dist_gc", "pol_index"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        sorted_result_dict = sorted(result_dict.items())
        for key, vals in sorted_result_dict:
            obj_write = vals
            obj_write["key"] = key
            writer.writerow(obj_write)

    print("Finished!")


if __name__ == "__main__":
    filename = "/home/robertacoeli/Documents/Pesquisa/Results/DadosReais/Deputados/Metrica_Polarizacao/Experimento_Todas_Maio2019/" \
               "Percentual_Polaridades/KDE/DadosKDE_GranMensal.json"
    rootfolder = os.path.dirname(filename)
    gran_output = os.path.splitext(os.path.basename(filename))[0].strip().split("_")
    gran = gran_output[-1]

    output_filename = os.path.join(rootfolder, "Metricas_Polarizacao_GranMensal.json")

    run(filename, output_filename)