import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- File paths (update for macOS) ---
solar_path = "./Solar_Energy_Generation.csv"
weather_path = "./Weather_Data_reordered_all.csv"

# --- File paths ---
#solar_path = r"C:\Users\brind\Downloads\yessirksi\RayFeildDataExperiment\Solar_Energy_Generation.csv"
#weather_path = r"C:\Users\brind\Downloads\yessirksi\RayFeildDataExperiment\Weather_Data_reordered_all.csv"  # <-- FIXED: added closing quote

if not os.path.exists(solar_path):
    raise FileNotFoundError(f"Solar data file not found at: {solar_path}")
if not os.path.exists(weather_path):
    raise FileNotFoundError(f"Weather data file not found at: {weather_path}")

solar_df = pd.read_csv(solar_path)
weather_df = pd.read_csv(weather_path)

solar_df['Timestamp'] = pd.to_datetime(solar_df['Timestamp'], errors='coerce')
weather_df['Timestamp'] = pd.to_datetime(weather_df['Timestamp'], errors='coerce')

solar_df.dropna(subset=['SolarGeneration', 'Timestamp'], inplace=True)
weather_df.dropna(subset=['Timestamp'], inplace=True)

merged_df = pd.merge(solar_df, weather_df, on=['CampusKey', 'Timestamp'], how='inner')

# --- Filter for one site (optional but helps for clear plots) ---
site_df = merged_df[(merged_df['CampusKey'] == 2) & (merged_df['SiteKey'] == 1)].copy()

# --- Downsample for performance ---
site_df = site_df.iloc[::1000, :]  # Plot every 1000th row

# --- Sort chronologically ---
site_df = site_df.sort_values("Timestamp")

# --- Plot 1: Solar Generation Over Time ---
plt.figure(figsize=(14, 5))
plt.plot(site_df['Timestamp'], site_df['SolarGeneration'], color='orange')
plt.title('Solar Energy Generation Over Time (Site 1, Campus 2)')
plt.xlabel('Timestamp')
plt.ylabel('Solar Generation (kWh)')
plt.grid(True)
plt.tight_layout()
plt.show()

# --- Plot 2: Solar Generation vs Air Temperature ---
if 'AirTemperature' in site_df.columns:
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=site_df, x='AirTemperature', y='SolarGeneration', alpha=0.6)
    plt.title('Solar Generation vs Air Temperature')
    plt.xlabel('Air Temperature (°C)')
    plt.ylabel('Solar Generation (kWh)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Plot 3: Solar Generation vs Relative Humidity ---
if 'RelativeHumidity' in site_df.columns:
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=site_df, x='RelativeHumidity', y='SolarGeneration', alpha=0.6, color='purple')
    plt.title('Solar Generation vs Relative Humidity')
    plt.xlabel('Relative Humidity (%)')
    plt.ylabel('Solar Generation (kWh)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- Plot 4: Dual-axis Plot for Wind Speed and Solar Generation ---
if 'WindSpeed' in site_df.columns:
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax2 = ax1.twinx()

    ax1.plot(site_df['Timestamp'], site_df['SolarGeneration'], 'g-', label='Solar Generation')
    ax2.plot(site_df['Timestamp'], site_df['WindSpeed'], 'b--', label='Wind Speed')

    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Solar Generation (kWh)', color='g')
    ax2.set_ylabel('Wind Speed (m/s)', color='b')

    plt.title("Solar Generation vs Wind Speed Over Time")
    fig.tight_layout()
    plt.grid(True)
    plt.show()