import pandas as pd


# CONSTANTS

DATA_PATH  = "CyberNova_Web_Logs.csv"
DIVIDER    = "=" * 40


# MAIN

def main() -> None:

    #  Load
    df = pd.read_csv(DATA_PATH)

    #  Dataset Overview
    print(f"\n{DIVIDER} DATASET OVERVIEW {DIVIDER}")
    print(df.head())

    print("\nFirst 5 rows:")
    print(df.head(5))

    print("\nLast 5 rows:")
    print(df.tail(5))

    #  Structure
    print(f"\n{DIVIDER} DATA INFO {DIVIDER}")
    df.info()

    #  Missing Values
    print(f"\n{DIVIDER} MISSING VALUES {DIVIDER}")
    print(df.isnull().sum())

    #  Duplicates
    print(f"\n{DIVIDER} DUPLICATES {DIVIDER}")
    print("Duplicate rows:", df.duplicated().sum())

    # Remove duplicates
    df = df.drop_duplicates()

    #  DateTime Parsing
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")

    print(f"\n{DIVIDER} DATETIME CHECK {DIVIDER}")
    print("Invalid DateTime values:", df["DateTime"].isnull().sum())

    #  Basic Validation
    print(f"\n{DIVIDER} BASIC VALIDATION {DIVIDER}")
    print("Negative Bytes:", (df["Bytes"] < 0).sum())

    # Feature Engineering
    df["Hour"] = df["DateTime"].dt.hour
    df["Day"]  = df["DateTime"].dt.day_name()

    # Final Shape
    print(f"\n{DIVIDER} FINAL SHAPE {DIVIDER}")
    print(df.shape)

    print("\nData is cleaned and ready for analysis.")


if __name__ == "__main__":
    main()