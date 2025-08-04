
import pandas as pd
from ai_module import train_model, predict_anomalies

df = pd.read_csv("solar_data/Solar_Energy_Generation.csv")
df = df.dropna(subset=["SolarGeneration"]).copy()
df["Time"] = pd.to_datetime(df["Time"])
df = df.rename(columns={"SolarGeneration": "output_kwh", "Time": "date"})
df = df.sort_values("date")

# Had to average the 15-minute intervals to by the hour
df_hourly = df.set_index("date").resample("1H").mean().dropna().reset_index()

# model
model = train_model(df_hourly)
df_hourly["anomaly"] = predict_anomalies(model, df_hourly)

# summary for the .csv
def generate_summary(df):
    anomalies = df[df["anomaly"]]["date"].astype(str).str[:10].unique().tolist()
    peak = df["output_kwh"].max()
    avg = round(df["output_kwh"].mean(), 2)
    return f"Avg output: {avg} kWh. Anomalies detected on: {', '.join(anomalies[:5])}... Peak output: {peak} kWh."

summary = generate_summary(df_hourly)
with open("weekly_summary.txt", "w") as f:
    f.write(summary)

df_hourly["summary"] = summary
df_hourly.to_csv("anomaly_check.csv", index=False)
