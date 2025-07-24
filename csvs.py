import pandas as pd
import matplotlib.pyplot as plt

file_path = "./Solar_Energy_Generation.csv"
df = pd.read_csv(file_path)

print(df.head())

print("\nDataframe info:")
df.info()

print(df.columns)

# --- Visualization ---
# Downsample: plot every 1000th row
sampled_df = df.iloc[::1000, :]

plt.figure(figsize=(10, 6))
plt.plot(sampled_df['Timestamp'], sampled_df['SolarGeneration'], marker='o', linestyle='-')
plt.xlabel('Timestamp')
plt.ylabel('Solar Generation')
plt.title('Solar Energy Generation Over Time')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
