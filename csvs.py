import pandas as pd



file_path = "./Solar_Energy_Generation.csv" 
df = pd.read_csv(file_path)

print(df.head())

print("\nDataframe info:")
print(df.info())
