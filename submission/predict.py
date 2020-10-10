import click
import numpy as np
import pandas as pd
import requests


@click.command()
def predict():
    test_data_url = (
        "https://raw.githubusercontent.com/deepio-oc/titanic/master/test/test.csv"
    )
    r = requests.get(test_data_url)
    with open("/tmp/test.csv", "wb") as f:
        f.write(r.content)

    df = pd.read_csv("/tmp/test.csv")
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
