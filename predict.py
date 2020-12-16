import os
import joblib
import numpy as np
import pandas as pd

model_dir = "/model"

def predict():
    test_df = pd.read_csv(os.path.join(model_dir, "test.csv"))
    test_df = pd.DataFrame(test_df).fillna(test_df.mean())
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    predictions = model.predict(test_df)
    df = pd.DataFrame({'PassengerId': test_df.index, 'Survived': predictions})
    df.to_csv(
        "/tmp/prediction.csv",
        index=True,
        columns=["Survived"],
    )
    print("predictions generated.")


if __name__ == "__main__":
    predict()