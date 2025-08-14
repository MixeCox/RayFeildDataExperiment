import pandas as pd
import matplotlib
matplotlib.use('Agg') # Set Matplotlib backend to 'Agg' for non-GUI operation
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import numpy as np
import os
import secrets
import json
import uuid # For generating unique IDs for image caching

from flask import Flask, render_template_string, request, redirect, url_for, session

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Global in-memory cache for generated plots (fixes session size issue) ---
# In a production app, use a more robust caching solution (e.g., Redis, database)
plot_image_cache = {}

# --- Helper Functions for Anomaly Detection and Plotting ---

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def train_model(df):
    """
    Mock AI model training. In a real scenario, this would train a complex ML model.
    Here, it calculates mean and std dev for Z-score anomaly detection.
    """
    # FIX: Corrected the column name from 'output_output_kwh' to 'output_kwh'
    mean_output = df['output_kwh'].mean()
    std_output = df['output_kwh'].std()
    return {'mean': mean_output, 'std': std_output}

def predict_anomalies(model, df, threshold=3.0):
    """
    Predicts anomalies based on Z-score.
    Values with a Z-score magnitude greater than the threshold are considered anomalies.
    """
    mean_output = model['mean']
    std_output = model['std']

    if std_output == 0: # Avoid division by zero if all values are the same
        return pd.Series([False] * len(df), index=df.index)

    df['z_score'] = (df['output_kwh'] - mean_output) / std_output
    # Flag as anomaly if absolute z-score exceeds threshold
    df['anomaly'] = np.abs(df['z_score']) > threshold
    return df['anomaly']

def generate_summary(df_hourly):
    """Generates a text summary of the energy analytics."""
    anomalies_df = df_hourly[df_hourly["anomaly"]]
    anomalies_dates = anomalies_df["date"].dt.strftime('%Y-%m-%d %H:%M').tolist()
    
    # Limit anomalies displayed to avoid very long strings
    anomalies_display = ", ".join(anomalies_dates[:5])
    if len(anomalies_dates) > 5:
        anomalies_display += f"... ({len(anomalies_dates) - 5} more)"
    elif not anomalies_dates:
        anomalies_display = "None detected."

    peak_output = df_hourly["output_kwh"].max()
    avg_output = round(df_hourly["output_kwh"].mean(), 2)

    return f"Avg output: {avg_output} kWh. Anomalies detected on: {anomalies_display}. Peak output: {peak_output} kWh."

def generate_plot_base64(df, plot_type, x_col, y_col, title, xlabel, ylabel, second_y_col=None, second_ylabel=None):
    """Generates a Matplotlib plot and returns it as a Base64 encoded string."""
    # Set a custom style for better aesthetics and readability
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Define a color palette for consistency
    colors = ['#00b09b', '#96c93d', '#1a2a6c', '#2c3e50', '#ff6b6b']

    if plot_type == 'dual_axis':
        fig, ax1 = plt.subplots(figsize=(14, 6)) # Larger figure for dual axis
        ax2 = ax1.twinx()

        ax1.plot(df[x_col], df[y_col], color=colors[0], label=ylabel, linewidth=2)
        ax2.plot(df[x_col], df[second_y_col], color=colors[2], linestyle='--', label=second_ylabel, linewidth=2)

        ax1.set_xlabel(xlabel, fontsize=12)
        ax1.set_ylabel(ylabel, color=colors[0], fontsize=12)
        ax2.set_ylabel(second_ylabel, color=colors[2], fontsize=12)
        
        ax1.tick_params(axis='y', labelcolor=colors[0])
        ax2.tick_params(axis='y', labelcolor=colors[2])
        ax1.tick_params(axis='x', rotation=45) # Rotate x-axis labels for better readability
        
        plt.title(title, fontsize=14, fontweight='bold')
        
        # Add legend to dual axis plot
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, fancybox=True, shadow=True)
        
        fig.tight_layout()
    else:
        plt.figure(figsize=(10, 6)) # Adjust figure size for better web display
        
        if plot_type == 'line':
            plt.plot(df[x_col], df[y_col], color=colors[0], linewidth=2)
        elif plot_type == 'scatter':
            # Use appropriate color for humidity plot
            scatter_color = colors[3] if y_col == 'RelativeHumidity' else colors[1]
            sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.7, color=scatter_color, s=50, edgecolor='w', linewidth=0.5)
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        if x_col == 'date': # Rotate x-axis labels for time series
            plt.xticks(rotation=45)
        plt.tight_layout()

    # Save plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150) # Increased DPI for better image quality
    buffer.seek(0)
    plot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close() # Close the plot to free memory
    return plot_base64

# --- Mock analytics data for initial display ---
mock_analytics = {
    'stats': {
        'max_output': 200.5,
        'min_output': 145.2,
        'avg_output': 174.8,
        'total_output': 3496.2,
        'data_points': 20
    },
    'anomalies': [
        {'timestamp': '2023-01-06 14:30:00', 'energy_output': 95.2, 'z_score': -2.8},
        {'timestamp': '2023-01-08 09:15:00', 'energy_output': 245.7, 'z_score': 3.2}
    ]
}


# --- Flask Routes ---
@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple redirect for demo purposes; no actual validation
        return redirect(url_for('dashboard'))
    return render_template_string(login_template)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            return "No file part", 400
        file = request.files['csv_file']
        if file.filename == '':
            return "No selected file", 400
        if file and allowed_file(file.filename):
            try:
                # Read CSV directly from stream
                df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
                
                # --- Apply data processing from your scripts ---
                # Validate essential columns as per your CSV example
                required_solar_cols = {'Timestamp', 'SolarGeneration'}
                if not required_solar_cols.issubset(df.columns):
                    missing = required_solar_cols - set(df.columns)
                    return f"Missing required columns in CSV: {', '.join(missing)}. Please ensure 'Timestamp' and 'SolarGeneration' are present.", 400

                df = df.dropna(subset=["SolarGeneration", "Timestamp"]).copy()
                df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce') 
                df = df.rename(columns={"SolarGeneration": "output_kwh", "Timestamp": "date"})
                df = df.sort_values("date")
                df.dropna(subset=['output_kwh', 'date'], inplace=True) # Ensure no NaNs after datetime conversion

                # Had to average the 15-minute intervals to by the hour
                df_hourly = df.set_index("date").resample("1H").mean().dropna().reset_index()

                # --- Simulate weather data for plotting if not present ---
                # This ensures all your desired plots can be generated
                num_records = len(df_hourly)
                # Ensure reproducibility for simulated data based on a seed or consistent pattern
                np.random.seed(42) 
                if 'AirTemperature' not in df_hourly.columns:
                    df_hourly['AirTemperature'] = np.random.uniform(5, 35, num_records)
                if 'RelativeHumidity' not in df_hourly.columns:
                    df_hourly['RelativeHumidity'] = np.random.uniform(30, 100, num_records)
                if 'WindSpeed' not in df_hourly.columns:
                    df_hourly['WindSpeed'] = np.random.uniform(0, 15, num_records)
                
                # Anomaly detection
                model_params = train_model(df_hourly)
                df_hourly["anomaly"] = predict_anomalies(model_params, df_hourly)
                # Store z_score for display in anomaly table
                df_hourly['z_score'] = (df_hourly['output_kwh'] - model_params['mean']) / model_params['std']

                # Generate summary
                weekly_summary = generate_summary(df_hourly)

                # Generate plots as base64 images and store in plot_image_cache
                plots_keys = {}
                
                # Plot 1: Solar Generation Over Time
                plot_id = str(uuid.uuid4())
                plot_image_cache[plot_id] = generate_plot_base64(
                    df_hourly, 'line', 'date', 'output_kwh',
                    'Solar Energy Generation Over Time', 'Timestamp', 'Solar Generation (kWh)'
                )
                plots_keys['time_series_plot'] = plot_id

                # Plot 2: Solar Generation vs Air Temperature
                plot_id = str(uuid.uuid4())
                plot_image_cache[plot_id] = generate_plot_base64(
                    df_hourly, 'scatter', 'AirTemperature', 'output_kwh',
                    'Solar Generation vs Air Temperature', 'Air Temperature (°C)', 'Solar Generation (kWh)'
                )
                plots_keys['temp_scatter_plot'] = plot_id
                
                # Plot 3: Solar Generation vs Relative Humidity
                plot_id = str(uuid.uuid4())
                plot_image_cache[plot_id] = generate_plot_base64(
                    df_hourly, 'scatter', 'RelativeHumidity', 'output_kwh',
                    'Solar Generation vs Relative Humidity', 'Relative Humidity (%)', 'Solar Generation (kWh)'
                )
                plots_keys['humidity_scatter_plot'] = plot_id

                # Plot 4: Dual-axis Plot for Wind Speed and Solar Generation
                plot_id = str(uuid.uuid4())
                plot_image_cache[plot_id] = generate_plot_base64(
                    df_hourly, 'dual_axis', 'date', 'output_kwh',
                    'Solar Generation vs Wind Speed Over Time', 'Timestamp', 'Solar Generation (kWh)',
                    'WindSpeed', 'Wind Speed (m/s)'
                )
                plots_keys['wind_dual_axis_plot'] = plot_id

                # Anomalies data for dashboard table
                anomalies_for_display = df_hourly[df_hourly['anomaly']].to_dict(orient='records')
                # Format for display (Timestamp, energy_output, deviation)
                formatted_anomalies = []
                for a in anomalies_for_display:
                    formatted_anomalies.append({
                        'timestamp': a['date'].strftime('%Y-%m-%d %H:%M:%S'),
                        'energy_output': a['output_kwh'],
                        'z_score': a.get('z_score', 0) # Use actual z_score if available
                    })
                
                # Update session with *keys* to processed data for dashboard display
                session['processed_data_keys'] = {
                    'plot_ids': plots_keys,
                    'summary': weekly_summary,
                    'stats': {
                        'max_output': df_hourly['output_kwh'].max(),
                        'min_output': df_hourly['output_kwh'].min(),
                        'avg_output': df_hourly['output_kwh'].mean(),
                        'total_output': df_hourly['output_kwh'].sum(),
                        'data_points': len(df_hourly)
                    },
                    'anomalies': formatted_anomalies
                }
                
                return redirect(url_for('dashboard'))

            except Exception as e:
                # Log the exception for debugging
                app.logger.error(f"Error processing file: {e}")
                return f"Error processing file: {e}", 500
        else:
            return "Invalid file type. Please upload a CSV file.", 400
    
    return render_template_string(upload_template, name="Sarah Johnson")

@app.route('/dashboard')
def dashboard():
    # Retrieve processed data *keys* from session
    processed_data_keys = session.get('processed_data_keys', None)

    # Initialize analytics_to_display with placeholders
    analytics_to_display = {
        'stats': mock_analytics['stats'],
        'anomalies': mock_analytics['anomalies'],
        'time_series_plot': None, 
        'temp_scatter_plot': None,
        'humidity_scatter_plot': None,
        'wind_dual_axis_plot': None,
    }
    summary_text = "Upload your data to see real-time analytics and anomaly detection!"

    if processed_data_keys:
        # Retrieve actual plot data from plot_image_cache using keys
        retrieved_plots = {}
        for plot_name, plot_id in processed_data_keys['plot_ids'].items():
            if plot_id in plot_image_cache:
                retrieved_plots[plot_name] = plot_image_cache.pop(plot_id) # Pop to clear cache after use
        
        analytics_to_display = {
            'stats': processed_data_keys['stats'],
            'anomalies': processed_data_keys['anomalies'],
            'time_series_plot': retrieved_plots.get('time_series_plot'),
            'temp_scatter_plot': retrieved_plots.get('temp_scatter_plot'),
            'humidity_scatter_plot': retrieved_plots.get('humidity_scatter_plot'),
            'wind_dual_axis_plot': retrieved_plots.get('wind_dual_axis_plot'),
        }
        summary_text = processed_data_keys['summary']
        # Clear session keys after use (optional, but good for single-upload apps)
        session.pop('processed_data_keys', None) 
    else:
        # Generate mock plots dynamically for initial display if no data uploaded
        mock_df_plot = pd.DataFrame({
            'date': pd.to_datetime(pd.date_range(start='2023-01-01', periods=24, freq='H')),
            'output_kwh': np.random.uniform(100, 200, 24),
            'AirTemperature': np.random.uniform(10, 30, 24),
            'RelativeHumidity': np.random.uniform(40, 90, 24),
            'WindSpeed': np.random.uniform(0, 10, 24)
        })

        analytics_to_display['time_series_plot'] = generate_plot_base64(
            mock_df_plot, 'line', 'date', 'output_kwh',
            'Energy Output Over Time (Mock)', 'Time', 'Energy Output (kWh)'
        )
        analytics_to_display['temp_scatter_plot'] = generate_plot_base64(
            mock_df_plot, 'scatter', 'AirTemperature', 'output_kwh',
            'Energy Output vs Temperature (Mock)', 'Temperature (°C)', 'Energy Output (kWh)'
        )
        analytics_to_display['humidity_scatter_plot'] = generate_plot_base64(
            mock_df_plot, 'scatter', 'RelativeHumidity', 'output_kwh',
            'Energy Output vs Humidity (Mock)', 'Relative Humidity (%)', 'Energy Output (kWh)'
        )
        analytics_to_display['wind_dual_axis_plot'] = generate_plot_base64(
            mock_df_plot, 'dual_axis', 'date', 'output_kwh',
            'Energy Output vs Wind Speed (Mock)', 'Time', 'Energy Output (kWh)',
            'WindSpeed', 'Wind Speed (m/s)'
        )


    return render_template_string(
        dashboard_template, 
        name="Sarah Johnson",
        company="Rayfield Systems",
        role="Energy Analyst",
        analytics=analytics_to_display,
        summary_text=summary_text
    )

@app.route('/logout')
def logout():
    # Clear session data and any corresponding plot cache entries
    if 'processed_data_keys' in session:
        for plot_id in session['processed_data_keys']['plot_ids'].values():
            plot_image_cache.pop(plot_id, None) # Remove from cache if still there
        session.pop('processed_data_keys', None) 
    return redirect(url_for('login'))

# HTML Templates as strings
login_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rayfield Systems - Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Roboto', sans-serif; 
            background: linear-gradient(135deg, #1a2a6c, #2c3e50);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container { 
            background-color: rgba(255, 255, 255, 0.95); 
            border-radius: 12px; 
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); 
            width: 100%; 
            max-width: 400px; 
            overflow: hidden; 
        }
        .header { 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            color: white; 
            padding: 25px 20px; 
            text-align: center; 
        }
        .header h1 { 
            font-size: 24px; 
            font-weight: 700; 
            margin-bottom: 5px; 
        }
        .header p { 
            font-size: 14px; 
            opacity: 0.9; 
        }
        .logo { 
            font-size: 36px; 
            margin-bottom: 15px; 
            display: block; 
        }
        .form-container { 
            padding: 30px; 
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        .form-group label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 500; 
            color: #2c3e50; 
        }
        .form-group input { 
            width: 100%; 
            padding: 12px 15px; 
            border: 1px solid #ddd; 
            border-radius: 6px; 
            font-size: 16px; 
            transition: border-color 0.3s; 
        }
        .form-group input:focus { 
            border-color: #00b09b; 
            outline: none; 
            box-shadow: 0 0 0 2px rgba(0, 176, 155, 0.2); 
        }
        .btn { 
            width: 100%; 
            padding: 14px; 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            color: white; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px; 
            font-weight: 500; 
            cursor: pointer; 
            transition: all 0.3s; 
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 15px rgba(0, 176, 155, 0.3); 
        }
        .footer { 
            text-align: center; 
            padding: 20px 0; 
            color: #7f8c8d; 
            font-size: 14px; 
            border-top: 1px solid #eee; 
        }
        .demo-note {
            background-color: #e8f4f3;
            color: #00b09b;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">⚡</div>
            <h1>Rayfield Energy Automation</h1>
            <p>AI-powered energy workflow solutions</p>
        </div>
        
        <div class="form-container">
            <div class="demo-note">
                UI Demo Mode - Click Login to Continue
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" placeholder="your.email@company.com" value="analyst@rayfield.com">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter your password" value="demo">
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
        </div>
        
        <div class="footer">
            &copy; 2023 Rayfield Systems. All rights reserved.
        </div>
    </div>
</body>
</html>
'''

upload_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Energy Data | Rayfield Systems</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Roboto', sans-serif; 
            background: linear-gradient(135deg, #1a2a6c, #2c3e50);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
        }
        .header { 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            color: white; 
            padding: 20px; 
            border-radius: 12px 12px 0 0; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .logo { 
            font-size: 32px; 
            display: flex; 
            align-items: center; 
        }
        .logo span { 
            margin-right: 15px; 
        }
        .user-info { 
            text-align: right; 
        }
        .user-info .name { 
            font-size: 18px; 
            font-weight: 500; 
        }
        .user-info .role { 
            font-size: 14px; 
            opacity: 0.9; 
        }
        .nav { 
            background-color: #2c3e50; 
            padding: 0 20px; 
            display: flex; 
        }
        .nav a { 
            color: white; 
            text-decoration: none; 
            padding: 15px 20px; 
            display: block; 
            transition: background 0.3s; 
        }
        .nav a:hover { 
            background-color: #1a2a6c; 
        }
        .nav a.active { 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            font-weight: 500; 
        }
        .content { 
            background-color: white; 
            padding: 30px; 
            border-radius: 0 0 12px 12px; 
            min-height: 400px; 
        }
        .page-title { 
            color: #2c3e50; 
            margin-bottom: 20px; 
            padding-bottom: 10px; 
            border-bottom: 2px solid #00b09b; 
        }
        .upload-card { 
            background-color: #f8f9fa; 
            border-radius: 8px; 
            padding: 30px; 
            text-align: center; 
            border: 2px dashed #00b09b; 
        }
        .upload-icon { 
            font-size: 48px; 
            color: #00b09b; 
            margin-bottom: 15px; 
        }
        .instructions { 
            margin: 20px 0; 
            padding: 15px; 
            background-color: #e8f4f3; 
            border-radius: 8px; 
            text-align: left; 
        }
        .instructions h3 { 
            color: #00b09b; 
            margin-bottom: 10px; 
        }
        .instructions ul { 
            padding-left: 20px; 
        }
        .instructions li { 
            margin-bottom: 8px; 
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        .form-group label { 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 500; 
            color: #2c3e50; 
        }
        .form-group input[type="file"] {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            width: 100%;
        }
        .btn { 
            padding: 12px 30px; 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            color: white; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px; 
            font-weight: 500; 
            cursor: pointer; 
            transition: all 0.3s; 
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 15px rgba(0, 176, 155, 0.3); 
        }
        .footer { 
            text-align: center; 
            padding: 20px 0; 
            color: #7f8c8d; 
            font-size: 14px; 
            margin-top: 30px; 
        }
        .demo-note {
            background-color: #e8f4f3;
            color: #00b09b;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <span>⚡</span>
                <div>
                    <h1>Rayfield Energy Automation</h1>
                    <p>AI-powered energy workflow solutions</p>
                </div>
            </div>
            <div class="user-info">
                <div class="name">{{ name }}</div>
                <div class="role">Operations Analyst</div>
            </div>
        </div>
        
        <div class="nav">
            <a href="{{ url_for('dashboard') }}">Dashboard</a>
            <a href="{{ url_for('upload') }}" class="active">Upload Data</a>
            <a href="#">Reports</a>
            <a href="#">Settings</a>
            <a href="{{ url_for('logout') }}" style="margin-left: auto;">Logout</a>
        </div>
        
        <div class="content">
            <h2 class="page-title">Upload Energy Data</h2>
            
            <div class="demo-note">
                Upload your Solar Energy Generation CSV to view real-time analytics.
            </div>
            
            <div class="upload-card">
                <div class="upload-icon">📊</div>
                <h2>Upload Your Energy Data CSV</h2>
                <p>Analyze energy production, efficiency, and detect anomalies</p>
                
                <form method="POST" enctype="multipart/form-data" style="margin-top: 30px;">
                    <div class="form-group">
                        <input type="file" name="csv_file" accept=".csv" required>
                    </div>
                    <button type="submit" class="btn">Upload & Analyze</button>
                </form>
            </div>
            
            <div class="instructions">
                <h3>Data Format Requirements</h3>
                <ul>
                    <li>Upload a CSV file with energy production data</li>
                    <li>Required columns: <code>Timestamp</code>, <code>SolarGeneration</code> (in kWh)</li>
                    <li>Timestamp format for <code>Timestamp</code> column: YYYY-MM-DD HH:MM:SS</li>
                    <li>Maximum file size: 10MB</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            &copy; 2023 Rayfield Systems. All rights reserved. | AI-powered Energy Automation
        </div>
    </div>
</body>
</html>
'''

dashboard_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Energy Dashboard | Rayfield Systems</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Roboto', sans-serif; 
            background: linear-gradient(135deg, #1a2a6c, #2c3e50);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        .header { 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            color: white; 
            padding: 20px; 
            border-radius: 12px 12px 0 0; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .logo { 
            font-size: 32px; 
            display: flex; 
            align-items: center; 
        }
        .logo span { 
            margin-right: 15px; 
        }
        .user-info { 
            text-align: right; 
        }
        .user-info .name { 
            font-size: 18px; 
            font-weight: 500; 
        }
        .user-info .role { 
            font-size: 14px; 
            opacity: 0.9; 
        }
        .nav { 
            background-color: #2c3e50; 
            padding: 0 20px; 
            display: flex; 
        }
        .nav a { 
            color: white; 
            text-decoration: none; 
            padding: 15px 20px; 
            display: block; 
            transition: background 0.3s; 
        }
        .nav a:hover { 
            background-color: #1a2a6c; 
        }
        .nav a.active { 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            font-weight: 500; 
        }
        .content { 
            background-color: white; 
            padding: 30px; 
            border-radius: 0 0 12px 12px; 
            min-height: 400px; 
        }
        .page-title { 
            color: #2c3e50; 
            margin-bottom: 20px; 
            padding-bottom: 10px; 
            border-bottom: 2px solid #00b09b; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .btn { 
            padding: 8px 20px; 
            background: linear-gradient(90deg, #00b09b, #96c93d); 
            color: white; 
            border: none; 
            border-radius: 6px; 
            font-size: 14px; 
            font-weight: 500; 
            cursor: pointer; 
            transition: all 0.3s; 
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 15px rgba(0, 176, 155, 0.3); 
        }
        .dashboard-grid { 
            display: grid; 
            grid-template-columns: repeat(2, 1fr); 
            gap: 25px; 
            margin-top: 20px; 
        }
        .card { 
            background-color: #f8f9fa; 
            border-radius: 10px; 
            padding: 20px; 
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); 
        }
        .card.full-width { 
            grid-column: span 2; 
        }
        .card-header { 
            color: #2c3e50; 
            margin-bottom: 15px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .chart-container { 
            height: 350px; 
            width: 100%; 
            display: flex; /* Use flexbox to center image */
            justify-content: center;
            align-items: center;
        }
        .chart-container img {
            max-width: 100%; /* Ensure image fits within container */
            max-height: 100%;
            object-fit: contain; /* Maintain aspect ratio */
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(4, 1fr); 
            gap: 15px; 
            margin-bottom: 25px; 
        }
        .stat-card { 
            background: linear-gradient(135deg, #00b09b, #96c93d); 
            color: white; 
            border-radius: 8px; 
            padding: 20px; 
            text-align: center; 
        }
        .stat-card .value { 
            font-size: 28px; 
            font-weight: 700; 
            margin: 10px 0; 
        }
        .stat-card .label { 
            font-size: 14px; 
            opacity: 0.9; 
        }
        .anomalies-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 15px; 
        }
        .anomalies-table th, 
        .anomalies-table td { 
            padding: 12px 15px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }
        .anomalies-table th { 
            background-color: #2c3e50; 
            color: white; 
        }
        .anomalies-table tr:nth-child(even) { 
            background-color: #f2f2f2; 
        }
        .anomalies-table tr:hover { 
            background-color: #e8f4f3; 
        }
        .footer { 
            text-align: center; 
            padding: 20px 0; 
            color: #7f8c8d; 
            font-size: 14px; 
            margin-top: 30px; 
        }
        .demo-note {
            background-color: #e8f4f3;
            color: #00b09b;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 6px;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
        }
        .badge {
            background-color: #ff6b6b;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .summary-box {
            background-color: #e0f2f7;
            border-left: 5px solid #007bff;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 5px;
            color: #0056b3;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <span>⚡</span>
                <div>
                    <h1>Rayfield Energy Automation</h1>
                    <p>AI-powered energy workflow solutions</p>
                </div>
            </div>
            <div class="user-info">
                <div class="name">{{ name }}</div>
                <div class="role">{{ role }}</div>
            </div>
        </div>
        
        <div class="nav">
            <a href="{{ url_for('dashboard') }}" class="active">Dashboard</a>
            <a href="{{ url_for('upload') }}">Upload Data</a>
            <a href="#">Reports</a>
            <a href="#">Settings</a>
            <a href="{{ url_for('logout') }}" style="margin-left: auto;">Logout</a>
        </div>
        
        <div class="content">
            <div class="demo-note">
                Displaying analytics based on uploaded data (or mock data if no upload).
            </div>
            
            <div class="page-title">
                <h2>Energy Production Dashboard</h2>
                <a href="{{ url_for('upload') }}" class="btn">Upload New Data</a>
            </div>

            <div class="summary-box">
                <strong>Weekly Summary:</strong> {{ summary_text }}
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Max Output</div>
                    <div class="value">{{ "%.1f"|format(analytics.stats.max_output) }} kWh</div>
                </div>
                <div class="stat-card">
                    <div class="label">Min Output</div>
                    <div class="value">{{ "%.1f"|format(analytics.stats.min_output) }} kWh</div>
                </div>
                <div class="stat-card">
                    <div class="label">Avg Output</div>
                    <div class="value">{{ "%.1f"|format(analytics.stats.avg_output) }} kWh</div>
                </div>
                <div class="stat-card">
                    <div class="label">Total Output</div>
                    <div class="value">{{ "%.1f"|format(analytics.stats.total_output) }} kWh</div>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <div class="card">
                    <div class="card-header">
                        <h3>Energy Output Over Time</h3>
                    </div>
                    <div class="chart-container">
                        {% if analytics.time_series_plot %}
                        <img src="data:image/png;base64,{{ analytics.time_series_plot }}" alt="Time Series Chart">
                        {% else %}
                        <p>Upload data to see this chart.</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Energy Output vs. Air Temperature</h3>
                    </div>
                    <div class="chart-container">
                        {% if analytics.temp_scatter_plot %} 
                        <img src="data:image/png;base64,{{ analytics.temp_scatter_plot }}" alt="Temperature Scatter Chart">
                        {% else %}
                        <p>Upload data to see this chart.</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Energy Output vs. Relative Humidity</h3>
                    </div>
                    <div class="chart-container">
                        {% if analytics.humidity_scatter_plot %} 
                        <img src="data:image/png;base64,{{ analytics.humidity_scatter_plot }}" alt="Humidity Scatter Chart">
                        {% else %}
                        <p>Upload data to see this chart.</p>
                        {% endif %}
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3>Solar Generation vs Wind Speed Over Time</h3>
                    </div>
                    <div class="chart-container">
                        {% if analytics.wind_dual_axis_plot %}
                        <img src="data:image/png;base64,{{ analytics.wind_dual_axis_plot }}" alt="Wind Speed Dual Axis Chart">
                        {% else %}
                        <p>Upload data to see this chart.</p>
                        {% endif %}
                    </div>
                </div>
                
                <div class="card full-width">
                    <div class="card-header">
                        <h3>Detected Anomalies</h3>
                        <span class="badge">{{ analytics.anomalies | length }} anomalies found</span>
                    </div>
                    {% if analytics.anomalies %}
                    <table class="anomalies-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Energy Output (kWh)</th>
                                <th>Deviation (Z-score)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for anomaly in analytics.anomalies %}
                            <tr>
                                <td>{{ anomaly.timestamp }}</td>
                                <td>{{ "%.1f"|format(anomaly.energy_output) }}</td>
                                <td>{{ "%.2f"|format(anomaly.z_score|abs) }}σ</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <p>No anomalies detected for the current dataset, or no data uploaded.</p>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <div class="footer">
            &copy; 2023 Rayfield Systems. All rights reserved. | AI-powered Energy Automation
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)