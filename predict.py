import os

import click

import numpy as np
import pandas as pd
from tensorflow import keras

@click.command()
def predict():
    os.system("ls -l /dataset/ /model/")
    df = pd.read_csv("/dataset/test.csv")
    keras.models.load_model("/model/model.h5")
    
    predictions = np.random.choice([0, 1], size=(len(df),), p=[1.0 / 3, 2.0 / 3])
    df["Survived"] = predictions
    df = df.set_index("PassengerId")
    df.to_csv(
        "/tmp/prediction.csv",
        index=True,
        columns=["Survived"],
    )
    print("predictions generated.")


if __name__ == "__main__":
    predict()

