'''
Calculates the individual polarities for each unlabeled users based on the total of retweets in labeled ones.

input: spreadsheet containing the total of retweets for each unlabeled user (total and percentage of retweets in "favoravel"/"coxinhas"; total and percentage of retweets in "contrario"/"petralhas") --> example: ScatterData_UsuariosSemLabel_GranMensal.xlsx (https://drive.google.com/drive/folders/1LivGb9Nddbl2FByLqq6yPezBHxRzfBpT?usp=sharing)

output: csv and json files containing the users and the percentage of retweets, as well as the difference between the percentages (the difference is the individual polarity value!)
        --> Format of the output file (csv): Period;User Id;Pro-Impeachment Retweets (%);Anti-Impeachment Retweets (%);Percentual Difference
        --> examples: "DiffPercentual_UsuariosSemLabel_GranMensal.csv" and "DiffPercentual_UsuariosSemLabel_GranMensal.json" (google drive -- same link above)

'''

import openpyxl
import os
import json

# Generate dictionary from excel file
def genDictionary(filename):
    data_dict = dict()

    wb = openpyxl.load_workbook(filename, read_only=True)
    ws = wb.active

    count = 1

    # para cada usuario (cada linha do arquivo eh um usuario unlabeled)...
    for row in ws.iter_rows(min_row=2):
        period = row[0].value           # mes
        user_id = row[1].value          # id do usuario
        retweets_fav = row[2].value     # total de retweets em usuarios favoraveis ao impeachment/pro-impeachment ("coxinhas")
        retweets_cont = row[4].value    # total de retweets em usuarios contrarios ao impeachment/anti-impeachment ("petralhas")

        count += 1

        try:
            total_retweets = retweets_fav + retweets_cont  # total de retweets em usuarios de alguma posicao marcada
            percentual_fav = retweets_fav/total_retweets   # percentual de retweets em usuarios "favoraveis"/pro-impeachment
            percentual_cont = retweets_cont/total_retweets # percentual de retweets em usuarios "contrarios"/anti-impeachment
            diff_posicionamento = percentual_fav - percentual_cont # diferenca de percentuais

            if (period not in data_dict):
                data_dict[period] = dict()

            if (user_id not in data_dict[period]):
                data_dict[period][user_id] = dict()

            ########### IMPORTANTE! ###########
            # adiciona os percentuais de retweets pro-impeachment, anti-impeachment e a diferenca dos percentuais (a diferenca é a polaridade individual!!!)
            data_dict[period][user_id]["pro"] = dict()
            data_dict[period][user_id]["pro"]["title"] = "Pro-Impeachment Retweets (%)"
            data_dict[period][user_id]["pro"]["value"] = "%.2f" % percentual_fav

            data_dict[period][user_id]["anti"] = dict()
            data_dict[period][user_id]["anti"]["title"] = "Anti-Impeachment Retweets (%)"
            data_dict[period][user_id]["anti"]["value"] = "%.2f" % percentual_cont

            data_dict[period][user_id]["diff"] = dict()
            data_dict[period][user_id]["diff"]["title"] = "Percentual Difference"
            data_dict[period][user_id]["diff"]["value"] = "%.5f" % diff_posicionamento

        except:
            print("Problem on line {0} -> {1}".format(count, row))

    print("{0} lines were read.".format(count))
    return data_dict


# Computes Percentual and Write to Files
def run(filename, rfolder):
    # Output file name
    output_filename = os.path.join(rfolder, "DiffPercentual_UsuariosSemLabel_GranMensal")

    # Generate dict from data
    print("Reading data from worksheet and generating dictionary...")
    data_dict = genDictionary(filename)

    # Write to JSON file
    print("Writing JSON file...")
    with open(output_filename + ".json", "w") as jfile:
        json.dump(data_dict, jfile)

    # Write to csv file
    print("Writing CSV file...")
    count = 1
    tfile = open(output_filename + ".csv", "w")
    tfile.write("Period;User Id;Pro-Impeachment Retweets (%);Anti-Impeachment Retweets (%);Percentual Difference\n")
    for period in sorted(data_dict):
        for user_id in data_dict[period]:
            count += 1
            perc_fav = data_dict[period][user_id]["pro"]["value"]
            perc_cont = data_dict[period][user_id]["anti"]["value"]
            diff_perc = data_dict[period][user_id]["diff"]["value"]
            tfile.write(";".join([period, user_id, perc_fav, perc_cont, diff_perc]) + "\n")
    tfile.close()
    print("{0} lines were written to output file.".format(count))
    print("Finished!")

# Main
if __name__ == "__main__":
    filename = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/Metrica_Polarizacao_Maio2018/" \
               "TotalPolaridades/ScatterData_UsuariosSemLabel_GranMensal.xlsx"
    rfolder = "/home/robertacoeli/Documents/Pesquisa/Results/Twitter/Publico/" \
               "Metrica_Polarizacao_Maio2018/PercentualTweetsPorPolaridade"

    # if folder does not exist, create it
    if (not os.path.exists(rfolder)):
        print("Criando pasta {0}".format(rfolder))
        os.makedirs(rfolder)

    run(filename, rfolder)