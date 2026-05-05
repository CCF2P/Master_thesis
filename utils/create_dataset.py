import os
import re

import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


path_to_folder_w = "E:/Diploma_ISU/Datasets/OPTG1/w"
path_to_folder_m = "E:/Diploma_ISU/Datasets/OPTG1/m"
path = "E:/Diploma_ISU/Datasets/xrays"

dataset = pd.DataFrame(
    columns=["age", "sex", "path_to_img"]
)

pattern_id = r"\((\d+)\)"
def add_data(
    path_to_folder: str,
    dataframe: pd.DataFrame,
    pattern: str=""
):
    for file in os.listdir(path_to_folder):
        cur_file = os.path.join(path_to_folder, file)
        if os.path.isfile(cur_file):
            age = re.findall(pattern, file.split(' ')[1])[0]
            dataframe.loc[len(dataframe)] = [int(age), path_to_folder[-1], cur_file]

def add_unstructed_data(
    path: str,
    df: pd.DataFrame
):
    i = 0
    for file in os.listdir(path):
        cur_file = os.path.join(path, file)
        if os.path.isfile(cur_file):
            df.loc[i] = [None, None, cur_file]
            i += 1

add_data(path_to_folder_w, dataset, pattern_id)
add_data(path_to_folder_m, dataset, pattern_id)

print("Total number of images: ", len(dataset))
print("Total number of m: ", len(dataset[dataset["sex"] == "m"]))
print("Total number of w: ", len(dataset[dataset["sex"] == "w"]))
print(dataset.head())
print(dataset.tail())

dataset.to_csv(
    path_or_buf="./dataset/metadata_dataset.csv",
    index=True,
    index_label="id"
)
