'''
    Get the best distribution of the individual polarities for each month. The distribution is used to compute the polarization index.

    input: "DiffPercentual_UsuariosSemLabel_GranMensal.json" (google drive: https://drive.google.com/drive/folders/1LivGb9Nddbl2FByLqq6yPezBHxRzfBpT?usp=sharing)

    output: json file containing the distributions of individual polarities for each month ("DadosKDE_GranMensal.json" - google drive, same link above)
'''
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors.kde import KernelDensity
import argparse
import numpy as np
import json
import timeit
import traceback, sys
import os

# Constantes
sample_size = 1000

# Obtém dicionário do arquivo
def get_dictionary(filename):
    print("Loading data...")
    start = timeit.default_timer()

    with open(filename, "r") as jfile:
        data_dict = json.load(jfile)

    stop = timeit.default_timer()
    print("Time to load: {0} s".format(stop - start))

    return data_dict

# Obtém array contendo um tipo de valor do conjunto de dados de usuários
def get_data_array(user_dict, val_type):
    values_array = []
    for u, uvals in user_dict:
        diff_value = float(uvals[val_type]["value"])
        values_array.append(diff_value)
    return values_array

# Computa o KDE do conjunto de dados
def compute_kernel(x, x_grid, bandwidth):
    kde_skl = KernelDensity(bandwidth=bandwidth)
    kde_skl.fit(x[:, np.newaxis])
    log_pdf = kde_skl.score_samples(x_grid[:, np.newaxis])
    return np.exp(log_pdf)

# Encontra o melhor bandwidth via grid search -> x = amostra dos dados
def find_best_bandwidth(x):
    grid = GridSearchCV(KernelDensity(),
                        {'bandwidth': np.linspace(0.1, 1.0, 30)},
                        cv=20)
    grid.fit(x[:, None])
    return grid.best_params_["bandwidth"]

# Obtém bandwidth para cada conjunto de dados (cada conjunto de polaridades a cada mês)
def run(filename, output_filename):
    print("Obter bandwith para conjunto de dados...")
    data_dict = get_dictionary(filename)
    result_dict = dict()

    conjunto_dados = data_dict.items()
    total_dados = len(conjunto_dados)
    count = 0

    for key, val in conjunto_dados:
        count += 1
        try:
            start = timeit.default_timer()

            print("Processing %s ... %d of %d" % (key, count, total_dados))
            if key not in result_dict:
                result_dict[key] = dict()

            uvals = val.items()
            total_usuarios = len(uvals)
            diff_array = get_data_array(uvals, "diff")
            if (sample_size > total_usuarios):
                diff_array_sample = np.array(diff_array.copy())
            else:
                diff_array_sample = np.random.choice(diff_array, size=sample_size, replace=False)
            bandwidth = find_best_bandwidth(diff_array_sample)
            val_min = min(diff_array)
            val_max = max(diff_array)

            if (val_min < 0):
                val_min_scale = 1.2*val_min
            else:
                val_min_scale = 0.8*val_min

            if (val_max > 0):
                val_max_scale = 1.2*val_max
            else:
                val_max_scale = 0.8*val_max

            diff_grid = np.linspace(val_min_scale, val_max_scale, total_usuarios * 10)
            pdf = compute_kernel(np.array(diff_array), diff_grid, bandwidth)

            # Adiciona ao dicionario
            result_dict[key]["bandwidth"] = bandwidth
            result_dict[key]["total_usuarios"] = total_usuarios
            result_dict[key]["diff_array"] = diff_array
            result_dict[key]["pdf_array"] = pdf.tolist()

            # Tempo para rodar
            stop = timeit.default_timer()
            print("Time elapsed: {0} s".format(stop - start))
        except:
            error_file = open(output_filename + "_ERROR.txt", "a")
            error_file.write("Error on key %s\n" % key)
            error_file.close()

    # Resumo dos Dados
    print("Total: %d data sets" % total_dados)

    # Salva no arquivo
    print("Saving to JSON file...")
    with open(output_filename + ".json", "w") as rfile:
        json.dump(result_dict, rfile)

    print("Finished!")

# MAIN
if __name__ == "__main__":
    # file names
    rootfolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/Metrica_Polarizacao_Maio2018/PercentualTweetsPorPolaridade"
    filename = os.path.join(rootfolder, "DiffPercentual_UsuariosSemLabel_GranMensal.json")

    output_folder = os.path.join(rootfolder, "KDE")
    if (not os.path.exists(output_folder)):
        os.makedirs(output_folder)
    output_filename = os.path.join(output_folder, "DadosKDE_GranMensal")

    run(filename, output_filename)