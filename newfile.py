from flask import Flask, render_template_string, request, redirect, url_for
import os
import secrets
import json
import numpy as np

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mock data for demonstration
mock_analytics = {
    'time_series': json.dumps({
        'data': [{
            'x': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
            'y': [150, 180, 165, 200, 175],
            'type': 'scatter',
            'mode': 'lines+markers',
            'name': 'Energy Output'
        }],
        'layout': {
            'title': 'Energy Output Over Time',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Energy Output (kWh)'},
            'template': 'plotly_white'
        }
    }),
    'distribution': json.dumps({
        'data': [{
            'x': [150, 160, 165, 170, 175, 180, 185, 190, 195, 200],
            'type': 'histogram',
            'name': 'Energy Distribution'
        }],
        'layout': {
            'title': 'Energy Output Distribution',
            'xaxis': {'title': 'Energy Output (kWh)'},
            'yaxis': {'title': 'Frequency'},
            'template': 'plotly_white'
        }
    }),
    'efficiency': json.dumps({
        'data': [{
            'x': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
            'y': [85, 88, 82, 90, 87],
            'type': 'scatter',
            'mode': 'markers',
            'name': 'Efficiency'
        }],
        'layout': {
            'title': 'System Efficiency Over Time',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Efficiency (%)'},
            'template': 'plotly_white'
        }
    }),
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

# Routes
@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Just redirect to dashboard on any POST - no validation
        return redirect(url_for('dashboard'))
    
    return render_template_string(login_template)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Just redirect to dashboard on any POST - no file processing
        return redirect(url_for('dashboard'))
    
    return render_template_string(upload_template, name="Sarah Johnson")

@app.route('/dashboard')
def dashboard():
    return render_template_string(
        dashboard_template, 
        name="Sarah Johnson",
        company="Rayfield Systems",
        role="Energy Analyst",
        analytics=mock_analytics
    )

@app.route('/logout')
def logout():
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
                UI Demo Mode - File upload will redirect to dashboard with mock data
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
                    <li>Required columns: <code>timestamp</code>, <code>energy_output</code> (in kWh)</li>
                    <li>Optional columns: <code>solar_irradiance</code>, <code>temperature</code>, <code>wind_speed</code></li>
                    <li>Timestamp format: YYYY-MM-DD HH:MM:SS</li>
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
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
                UI Demo Mode - Displaying mock energy analytics data
            </div>
            
            <div class="page-title">
                <h2>Energy Production Dashboard</h2>
                <a href="{{ url_for('upload') }}" class="btn">Upload New Data</a>
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
                    <div class="chart-container" id="time-series-chart"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Energy Output Distribution</h3>
                    </div>
                    <div class="chart-container" id="distribution-chart"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>System Efficiency</h3>
                    </div>
                    <div class="chart-container" id="efficiency-chart"></div>
                </div>
                
                <div class="card full-width">
                    <div class="card-header">
                        <h3>Detected Anomalies</h3>
                        <span class="badge">{{ analytics.anomalies | length }} anomalies found</span>
                    </div>
                    <table class="anomalies-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Energy Output (kWh)</th>
                                <th>Deviation</th>
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
                </div>
            </div>
        </div>
        
        <div class="footer">
            &copy; 2023 Rayfield Systems. All rights reserved. | AI-powered Energy Automation
        </div>
    </div>
    
    <script>
        // Render the time series chart
        var timeSeriesData = {{ analytics.time_series | safe }};
        Plotly.newPlot('time-series-chart', timeSeriesData.data, timeSeriesData.layout);
        
        // Render the distribution chart
        var distributionData = {{ analytics.distribution | safe }};
        Plotly.newPlot('distribution-chart', distributionData.data, distributionData.layout);
        
        // Render the efficiency chart
        var efficiencyData = {{ analytics.efficiency | safe }};
        Plotly.newPlot('efficiency-chart', efficiencyData.data, efficiencyData.layout);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)