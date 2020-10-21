import os

import click

import numpy as np
import pandas as pd


@click.command()
def predict():
    os.system("ls -l /titanic-test/")

    df = pd.read_csv("/titanic-test/test.csv")
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
