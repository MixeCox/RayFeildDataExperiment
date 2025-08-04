
import pandas as pd
from ai_module import train_model, predict_anomalies

# Load and preprocess data
df = pd.read_csv("solar_data/Solar_Energy_Generation.csv")
df = df.dropna(subset=["SolarGeneration"]).copy()
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.rename(columns={"SolarGeneration": "output_kwh", "Timestamp": "date"})
df = df.sort_values("date")

# Downsample to hourly
df_hourly = df.set_index("date").resample("1H").mean().dropna().reset_index()

# Train model and detect anomalies
model = train_model(df_hourly)
df_hourly["anomaly"] = predict_anomalies(model, df_hourly)

# Generate a summary
def generate_mock_summary(df):
    anomalies = df[df["anomaly"]]["date"].astype(str).str[:10].unique().tolist()
    peak = df["output_kwh"].max()
    avg = round(df["output_kwh"].mean(), 2)
    return f"Avg output: {avg} kWh. Anomalies detected on: {', '.join(anomalies[:5])}... Peak output: {peak} kWh."

summary = generate_mock_summary(df_hourly)
with open("weekly_summary.txt", "w") as f:
    f.write(summary)

df_hourly["summary"] = summary
df_hourly.to_csv("final_output_with_summary.csv", index=False)
