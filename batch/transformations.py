import pandas as pd

def transform_data(df):

    df = df.copy()

    df.columns = [c.lower() for c in df.columns]

    df = df.drop_duplicates()

    df["fecha"] = pd.to_datetime(df["fecha"])

    return df


def validate_dataframe(df, table_type="sales"):

    df = transform_data(df)

    df = df.dropna()

    col = "total" if table_type == "sales" else "stock"

    df = df[df[col] >= 0]

    return df