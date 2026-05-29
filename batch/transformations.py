import pandas as pd

def transform_data(df):

    df = df.copy()

    df.columns = [c.lower() for c in df.columns]

    df = df.drop_duplicates()

    df["fecha"] = pd.to_datetime(df["fecha"])

    return df