import os
import shutil

import pandas as pd


if not os.path.exists("./dataset/images"):
    os.mkdir("./dataset/images")

metadata = pd.read_csv(
    filepath_or_buffer="./dataset/metadata_dataset.csv",
    sep=','
)

for id, path in metadata["path_to_img"].items():
    shutil.copy(path, f"./dataset/images/{id}.jpg")
