# Polarization Calculation

Scripts for calculating the individual polarities and the polarization index. The scripts included in this repository were used in the analyses that are described in the following article:

**Elite versus mass polarization on the Brazilian impeachment proceedings of 2016** <br/>
**Authors**: Roberta C. N. Moreira, Pedro O. S. Vaz-de-Melo, Gisele L. Pappa <br/>
**Published in**: Social Network Analysis and Mining | Issue 1/2020  <br/>

## Folders

* src
    * **labeling**: scripts to label users according to the selected hashtags and to generate the retweet networks.
    * **polarities**: scripts used to the calculate of individual polarities.
    * **polarization**: scripts to calculate the variables related to the polarization and the polarization index.
    * **utils**: some useful scripts that are used over the code.
    * **preprocessing**: scripts to execute a basic text preprocessing.

* files: contains some important files that are used by the scripts. Ex.: the files containing the list of hashtags of each group (pro-impeachment, anti-impeachment, etc).

## Files

For the most part of the scripts, the "main" function is located at the end of the file, i.e., after the methods and class definitions. It contains the inputs and outputs, as well as it calls the function that executes the task for the script.

# Output Examples

If you may find it useful to check some output files to understand how the scripts operate, you can check some of them by this [Google Drive folder](https://drive.google.com/drive/folders/1LivGb9Nddbl2FByLqq6yPezBHxRzfBpT?usp=sharing).
