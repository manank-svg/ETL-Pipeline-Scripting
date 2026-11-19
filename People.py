import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parent

print("Libraries imported successfully.")

# Extract
file_path = BASE_DIR / "people-100.csv"

if not file_path.exists():
    raise FileNotFoundError(
        f"people-100.csv was not found at {file_path}. "
        "Place it beside People.py or update file_path with its full path."
    )

df = pd.read_csv(file_path)

print("Data extracted successfully.")
print("Rows and columns:", df.shape)
print(df.head())

print(df)

# Explore the dataset
print("Dataset information:")
df.info()

print("\nMissing values in each column:")
print(df.isna().sum())

print("\nExact duplicate rows:", df.duplicated().sum())

# Transform and clean
clean_df = df.copy()

# Standardize column names, for example: 'Date of birth' -> 'date_of_birth'
clean_df.columns = [
    re.sub(
        r"_+",
        "_",
        re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()),
    ).strip("_")
    for column in clean_df.columns
]

# Trim whitespace and convert empty strings to missing values
for column in clean_df.select_dtypes(include=["object", "string"]).columns:
    clean_df[column] = clean_df[column].astype("string").str.strip()
    clean_df[column] = clean_df[column].replace("", pd.NA)

# Remove exact duplicate rows
clean_df = clean_df.drop_duplicates()

# Keep records with a user_id and remove repeated user IDs
if "user_id" in clean_df.columns:
    clean_df = clean_df.dropna(subset=["user_id"])
    clean_df = clean_df.drop_duplicates(subset=["user_id"], keep="first")

# Standardize email addresses
if "email" in clean_df.columns:
    clean_df["email"] = clean_df["email"].str.lower()

# Convert date of birth to date values
if "date_of_birth" in clean_df.columns:
    clean_df["date_of_birth"] = pd.to_datetime(
        clean_df["date_of_birth"], errors="coerce"
    ).dt.date

# Remove rows that are completely empty
clean_df = clean_df.dropna(how="all").reset_index(drop=True)

print("Transformation completed.")
print("Original rows:", len(df))
print("Cleaned rows:", len(clean_df))
print(clean_df.head())

print("Cleaned dataset shape:", clean_df.shape)
print("\nCleaned column names:")
print(clean_df.columns.tolist())

print("\nMissing values after cleaning:")
print(clean_df.isna().sum())

print("\nDuplicate rows after cleaning:", clean_df.duplicated().sum())

# Load and save data into SQLite
database_path = BASE_DIR / "people.db"
database_url = f"sqlite:///{database_path}"
engine = create_engine(database_url)

clean_df.to_sql(
    name="people",
    con=engine,
    if_exists="replace",
    index=False,
)

print(f"Data loaded successfully into {database_path} (table: people).")

# Verify the data loaded into the database
with engine.connect() as connection:
    total_rows = connection.execute(
        text("SELECT COUNT(*) FROM people")
    ).scalar()

    result = pd.read_sql(
        text("SELECT * FROM people LIMIT 5"),
        connection,
    )

print("Total rows loaded:", total_rows)
print(result)

engine.dispose()

# Export the cleaned data to CSV
cleaned_csv_path = BASE_DIR / "cleaned_people.csv"
clean_df.to_csv(cleaned_csv_path, index=False)
print(f"Cleaned data exported to '{cleaned_csv_path}'.")
