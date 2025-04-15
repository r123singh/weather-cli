# app to create a weather streaming
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Union, Tuple
import pytz
import csv
import time
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import folium
from folium import plugins
import webbrowser
import tempfile
import branca.colormap as cm

API_KEY = "a0242384be8001994698f59649a78da7"
FAVORITES_FILE = "favorites.json"
HISTORY_FILE = "weather_history.json"
NOTIFICATION_FILE = "notifications.json"
MAPS_DIR = "weather_maps"

PREMIUM_FEATURES = {
    'advanced_maps': True,
    'historical_data': True,
    'multiple_cities': True,
    'export_data': True,
    'notifications': True,
    'custom_alerts': True
}

def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9/5) + 32

def format_temperature(temp_c: float) -> str:
    temp_f = celsius_to_fahrenheit(temp_c)
    return f"{temp_c:.1f}°C ({temp_f:.1f}°F)"

def get_aqi_description(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def get_uv_description(uv: float) -> str:
    if uv <= 2:
        return "Low"
    elif uv <= 5:
        return "Moderate"
    elif uv <= 7:
        return "High"
    elif uv <= 10:
        return "Very High"
    else:
        return "Extreme"

def load_favorites() -> List[str]:
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_favorites(favorites: List[str]):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f)

def load_history() -> Dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history(history: Dict):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def load_notifications() -> Dict:
    if os.path.exists(NOTIFICATION_FILE):
        with open(NOTIFICATION_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_notifications(notifications: Dict):
    with open(NOTIFICATION_FILE, 'w') as f:
        json.dump(notifications, f)

def check_premium_access(user_id: str) -> bool:
    """Check if user has premium access"""
    try:
        with open('subscriptions.json', 'r') as f:
            subscriptions = json.load(f)
            return user_id in subscriptions and subscriptions[user_id]['active']
    except FileNotFoundError:
        return False

def get_subscription_status(user_id: str) -> Dict:
    """Get user's subscription status"""
    try:
        with open('subscriptions.json', 'r') as f:
            subscriptions = json.load(f)
            return subscriptions.get(user_id, {'active': False, 'expiry_date': None})
    except FileNotFoundError:
        return {'active': False, 'expiry_date': None}

def format_weather_data(data: Dict, include_forecast: bool = False, user_id: str = None) -> str:
    """Format weather data with premium features"""
    is_premium = check_premium_access(user_id) if user_id else False
    
    if not data:
        return "No weather data available"
    
    try:
        # Basic weather info (free)
        weather_info = f"""
Weather Report for {data['name']} ({data['coord']['lat']}°N, {data['coord']['lon']}°E)
Time: {datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S')}

🌡️ Temperature
   Current: {format_temperature(data['main']['temp'])}
   Feels like: {format_temperature(data['main']['feels_like'])}
   Min: {format_temperature(data['main']['temp_min'])}
   Max: {format_temperature(data['main']['temp_max'])}
"""
        
        # Premium features
        if is_premium:
            # Air quality
            if 'air_quality' in data:
                aqi = data['air_quality']['aqi']
                weather_info += f"\n🌫️ Air Quality Index: {aqi} ({get_aqi_description(aqi)})"
            
            # UV index
            if 'uv_index' in data:
                uv = data['uv_index']
                weather_info += f"\n☀️ UV Index: {uv:.1f} ({get_uv_description(uv)})"
            
            # Detailed forecast
            if include_forecast and 'forecast' in data:
                weather_info += "\n\n📅 Detailed 5-Day Forecast:"
                for item in data['forecast']:
                    dt = datetime.fromtimestamp(item['dt'])
                    weather_info += f"\n   {dt.strftime('%Y-%m-%d %H:%M')}: {format_temperature(item['main']['temp'])} - {item['weather'][0]['description']}"
        else:
            weather_info += "\n\n🔒 Premium Features Available:"
            weather_info += "\n   - Air Quality Index"
            weather_info += "\n   - UV Index"
            weather_info += "\n   - Detailed 5-Day Forecast"
            weather_info += "\n   - Historical Data"
            weather_info += "\n   - Multiple City Comparison"
            weather_info += "\n   - Data Export"
            weather_info += "\n   - Custom Alerts"
            weather_info += "\n\nUpgrade to Premium for full access!"
        
        return weather_info
    except KeyError as e:
        return f"Error formatting weather data: Missing field {str(e)}"

def get_weather(city: str, include_forecast: bool = False) -> Union[str, Dict]:
    """Get weather data for a given city"""
    try:
        # Current weather
        url = f"http://148.113.8.166/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        print(f"Fetching weather data for {city}...")
        
        session = create_session()
        response = session.get(
            url,
            headers={
                'Host': 'api.openweathermap.org',
                'User-Agent': 'Mozilla/5.0'
            },
            timeout=10
        )
        
        if response.status_code == 404:
            return f"Error: City '{city}' not found"
        elif response.status_code != 200:
            return f"Error: Unable to fetch weather data (Status code: {response.status_code})"
            
        data = response.json()
        
        # Get air quality data
        aqi_url = f"http://148.113.8.166/data/2.5/air_pollution?lat={data['coord']['lat']}&lon={data['coord']['lon']}&appid={API_KEY}"
        aqi_response = session.get(aqi_url, headers={'Host': 'api.openweathermap.org'})
        if aqi_response.status_code == 200:
            aqi_data = aqi_response.json()
            data['air_quality'] = aqi_data['list'][0]['main']
        
        # Get UV index
        uv_url = f"http://148.113.8.166/data/2.5/uvi?lat={data['coord']['lat']}&lon={data['coord']['lon']}&appid={API_KEY}"
        uv_response = session.get(uv_url, headers={'Host': 'api.openweathermap.org'})
        if uv_response.status_code == 200:
            uv_data = uv_response.json()
            data['uv_index'] = uv_data['value']
        
        if include_forecast:
            # Get 5-day forecast
            forecast_url = f"http://148.113.8.166/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
            forecast_response = session.get(
                forecast_url,
                headers={
                    'Host': 'api.openweathermap.org',
                    'User-Agent': 'Mozilla/5.0'
                },
                timeout=10
            )
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                data['forecast'] = forecast_data['list']
        
        return data
    
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error: Connection failed - {str(e)}"
    except json.JSONDecodeError:
        return "Error: Invalid response from weather service"
    except Exception as e:
        return f"Error: Unexpected error occurred - {str(e)}"

def format_forecast(forecast_data: List[Dict]) -> str:
    """Format forecast data"""
    if not forecast_data:
        return "No forecast data available"
    
    forecast_info = "\n📅 5-Day Forecast:\n"
    current_date = None
    
    for item in forecast_data:
        dt = datetime.fromtimestamp(item['dt'])
        date_str = dt.strftime('%Y-%m-%d')
        
        if date_str != current_date:
            current_date = date_str
            forecast_info += f"\n{date_str}:\n"
        
        time_str = dt.strftime('%H:%M')
        forecast_info += f"   {time_str}: {format_temperature(item['main']['temp'])} - {item['weather'][0]['description']}\n"
    
    return forecast_info

def compare_cities(cities: List[str]) -> str:
    """Compare weather between multiple cities"""
    comparison = "\n🌍 Weather Comparison:\n"
    comparison += "City".ljust(15) + "Temp".ljust(15) + "Conditions".ljust(20) + "Humidity".ljust(10) + "Wind\n"
    comparison += "-" * 60 + "\n"
    
    for city in cities:
        result = get_weather(city)
        if isinstance(result, str):
            comparison += f"{city}: {result}\n"
        else:
            comparison += f"{city.ljust(15)}{format_temperature(result['main']['temp']).ljust(15)}"
            comparison += f"{result['weather'][0]['description'].ljust(20)}"
            comparison += f"{str(result['main']['humidity'])}%".ljust(10)
            comparison += f"{result['wind']['speed']} m/s\n"
    
    return comparison

def export_weather_data(city: str, format: str = 'csv') -> str:
    """Export weather data to CSV or JSON"""
    result = get_weather(city, include_forecast=True)
    if isinstance(result, str):
        return result
    
    filename = f"weather_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    
    if format.lower() == 'csv':
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Time', 'Temperature (°C)', 'Temperature (°F)', 
                           'Conditions', 'Humidity', 'Wind Speed'])
            
            for item in result['forecast']:
                dt = datetime.fromtimestamp(item['dt'])
                writer.writerow([
                    dt.strftime('%Y-%m-%d'),
                    dt.strftime('%H:%M'),
                    item['main']['temp'],
                    celsius_to_fahrenheit(item['main']['temp']),
                    item['weather'][0]['description'],
                    item['main']['humidity'],
                    item['wind']['speed']
                ])
    else:  # JSON
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
    
    return f"Weather data exported to {filename}"

def plot_weather_trends(city: str):
    """Plot temperature trends for a city"""
    result = get_weather(city, include_forecast=True)
    if isinstance(result, str):
        return result
    
    dates = []
    temps = []
    
    for item in result['forecast']:
        dt = datetime.fromtimestamp(item['dt'])
        dates.append(dt)
        temps.append(item['main']['temp'])
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, temps, marker='o')
    plt.title(f'Temperature Trends for {city}')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    filename = f"weather_trend_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename)
    plt.close()
    
    return f"Weather trend plot saved to {filename}"

def check_notifications():
    """Check for weather notifications for favorite cities"""
    notifications = load_notifications()
    favorites = load_favorites()
    
    if not notifications or not favorites:
        return "No notifications set up"
    
    alerts = []
    for city in favorites:
        if city in notifications:
            result = get_weather(city)
            if isinstance(result, dict):
                temp = result['main']['temp']
                if 'temp_threshold' in notifications[city]:
                    if temp > notifications[city]['temp_threshold']:
                        alerts.append(f"{city}: Temperature above threshold ({temp}°C)")
                
                if 'conditions' in notifications[city]:
                    current_condition = result['weather'][0]['main'].lower()
                    if current_condition in notifications[city]['conditions']:
                        alerts.append(f"{city}: {current_condition} conditions detected")
    
    if alerts:
        return "\n".join(alerts)
    return "No weather alerts to report"

def save_weather_history(city: str, data: Dict):
    """Save weather history for a city"""
    history = load_history()
    history[city] = data
    save_history(history)

def get_weather_history() -> str:
    """Get weather history for all cities"""
    history = load_history()
    if not history:
        return "No weather history available"
    history_info = "\n🌐 Weather History:\n"
    for city, data in history.items():
        history_info += f"\n{city}:\n"
        history_info += f"   Date: {data['date']}\n"
        history_info += f"   Temperature: {data['temperature']}°C\n"
        history_info += f"   Conditions: {data['conditions']}\n"
    
    return history_info

def create_map_directory():
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)

def create_weather_popup(data: Dict) -> str:
    """Create detailed weather popup content"""
    return f"""
    <div style="width: 200px;">
        <h4>{data['name']}</h4>
        <p><b>Temperature:</b> {format_temperature(data['main']['temp'])}</p>
        <p><b>Feels like:</b> {format_temperature(data['main']['feels_like'])}</p>
        <p><b>Conditions:</b> {data['weather'][0]['description']}</p>
        <p><b>Humidity:</b> {data['main']['humidity']}%</p>
        <p><b>Wind:</b> {data['wind']['speed']} m/s, {data['wind']['deg']}°</p>
        <p><b>Pressure:</b> {data['main']['pressure']} hPa</p>
        <p><b>Visibility:</b> {data['visibility']/1000:.1f} km</p>
    </div>
    """

def get_weather_map(city: str, map_type: str = 'temperature') -> str:
    """Generate weather map for a city"""
    try:
        # Get city coordinates
        url = f"http://148.113.8.166/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, headers={'Host': 'api.openweathermap.org'})
        if response.status_code != 200:
            return f"Error: Could not get city coordinates for {city}"
        
        data = response.json()
        lat, lon = data['coord']['lat'], data['coord']['lon']
        
        # Create map with more zoom levels
        m = folium.Map(location=[lat, lon], zoom_start=10, control_scale=True)
        
        # Add measurement tools
        plugins.MeasureControl(position='topleft').add_to(m)
        
        # Add fullscreen control
        plugins.Fullscreen(position='topleft').add_to(m)
        
        # Add minimap
        plugins.MiniMap().add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Create feature group for markers
        fg = folium.FeatureGroup(name="Weather Markers")
        
        # Get forecast data for animation
        forecast_url = f"http://148.113.8.166/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        forecast_data = requests.get(forecast_url, headers={'Host': 'api.openweathermap.org'}).json()
        
        # Create color scale based on data type
        if map_type == 'temperature':
            temps = [item['main']['temp'] for item in forecast_data['list']]
            colormap = cm.LinearColormap(
                ['blue', 'yellow', 'red'],
                vmin=min(temps),
                vmax=max(temps),
                caption='Temperature (°C)'
            )
            colormap.add_to(m)
        elif map_type == 'precipitation':
            rains = [item['rain']['3h'] if 'rain' in item else 0 for item in forecast_data['list']]
            colormap = cm.LinearColormap(
                ['white', 'lightblue', 'blue', 'darkblue'],
                vmin=0,
                vmax=max(rains),
                caption='Precipitation (mm)'
            )
            colormap.add_to(m)
        elif map_type == 'wind':
            winds = [item['wind']['speed'] for item in forecast_data['list']]
            colormap = cm.LinearColormap(
                ['lightgreen', 'green', 'darkgreen'],
                vmin=min(winds),
                vmax=max(winds),
                caption='Wind Speed (m/s)'
            )
            colormap.add_to(m)
        
        # Create time slider data
        time_slider_data = []
        
        for item in forecast_data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            if map_type == 'temperature':
                value = item['main']['temp']
                color = colormap(value)
            elif map_type == 'precipitation':
                value = item['rain']['3h'] if 'rain' in item else 0
                color = colormap(value)
            elif map_type == 'wind':
                value = item['wind']['speed']
                color = colormap(value)
            
            # Create marker with detailed popup
            popup = create_weather_popup(item)
            marker = folium.CircleMarker(
                [lat, lon],
                radius=10,
                popup=popup,
                color=color,
                fill=True,
                fill_opacity=0.7
            )
            
            time_slider_data.append({
                'time': dt.strftime('%Y-%m-%d %H:%M'),
                'popup': popup,
                'coordinates': [lat, lon],
                'value': value,
                'color': color
            })
        
        # Add time slider
        plugins.TimeSliderChoropleth(
            time_slider_data,
            period='PT3H',  # 3-hour intervals
            name='Weather Animation'
        ).add_to(m)
        
        # Add title with more information
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50%;
                    transform: translateX(-50%);
                    z-index:9999;
                    background-color:white;
                    padding:5px;
                    border:2px solid grey;
                    border-radius:5px;
                    box-shadow: 2px 2px 2px grey;">
            <h3>{map_type.title()} Map - {city}</h3>
            <p>Use the time slider to see weather changes</p>
            <p>Click markers for detailed information</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save map
        create_map_directory()
        filename = f"{MAPS_DIR}/weather_map_{city}_{map_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        m.save(filename)
        
        # Open in browser
        webbrowser.open(f'file://{os.path.abspath(filename)}')
        
        return f"Weather map saved to {filename}"
    
    except Exception as e:
        return f"Error generating weather map: {str(e)}"

def get_radar_map(city: str) -> str:
    """Generate radar map for a city"""
    try:
        # Get city coordinates
        url = f"http://148.113.8.166/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, headers={'Host': 'api.openweathermap.org'})
        if response.status_code != 200:
            return f"Error: Could not get city coordinates for {city}"
        
        data = response.json()
        lat, lon = data['coord']['lat'], data['coord']['lon']
        
        # Create map with more features
        m = folium.Map(location=[lat, lon], zoom_start=8, control_scale=True)
        
        # Add measurement tools
        plugins.MeasureControl(position='topleft').add_to(m)
        
        # Add fullscreen control
        plugins.Fullscreen(position='topleft').add_to(m)
        
        # Add minimap
        plugins.MiniMap().add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Get radar data
        radar_url = f"http://148.113.8.166/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        radar_data = requests.get(radar_url, headers={'Host': 'api.openweathermap.org'}).json()
        
        # Create color scale for precipitation
        rains = [item['rain']['3h'] if 'rain' in item else 0 for item in radar_data['list']]
        colormap = cm.LinearColormap(
            ['white', 'lightblue', 'blue', 'darkblue'],
            vmin=0,
            vmax=max(rains) if rains else 10,
            caption='Precipitation (mm)'
        )
        colormap.add_to(m)
        
        # Create time slider data
        time_slider_data = []
        
        for item in radar_data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            rain = item['rain']['3h'] if 'rain' in item else 0
            color = colormap(rain)
            
            # Create detailed popup
            popup = create_weather_popup(item)
            
            time_slider_data.append({
                'time': dt.strftime('%Y-%m-%d %H:%M'),
                'popup': popup,
                'coordinates': [lat, lon],
                'value': rain,
                'color': color
            })
        
        # Add time slider
        plugins.TimeSliderChoropleth(
            time_slider_data,
            period='PT3H',  # 3-hour intervals
            name='Radar Animation'
        ).add_to(m)
        
        # Add title with more information
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50%;
                    transform: translateX(-50%);
                    z-index:9999;
                    background-color:white;
                    padding:5px;
                    border:2px solid grey;
                    border-radius:5px;
                    box-shadow: 2px 2px 2px grey;">
            <h3>Radar Map - {city}</h3>
            <p>Use the time slider to see precipitation changes</p>
            <p>Click markers for detailed information</p>
            <p>Use measurement tools to measure distances</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save map
        create_map_directory()
        filename = f"{MAPS_DIR}/radar_map_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        m.save(filename)
        
        # Open in browser
        webbrowser.open(f'file://{os.path.abspath(filename)}')
        
        return f"Radar map saved to {filename}"
    
    except Exception as e:
        return f"Error generating radar map: {str(e)}"

def main():
    favorites = load_favorites()
    history = load_history()
    
    while True:
        print("\n=== Weather Information System ===")
        print("1. Check weather for a city")
        print("2. Check weather for multiple cities (Premium)")
        print("3. View favorites")
        print("4. Add to favorites")
        print("5. Remove from favorites")
        print("6. Compare cities (Premium)")
        print("7. Export weather data (Premium)")
        print("8. Plot weather trends (Premium)")
        print("9. Set up notifications (Premium)")
        print("10. Check notifications")
        print("11. Get weather history (Premium)")
        print("12. View weather maps (Premium)")
        print("13. View radar maps (Premium)")
        print("14. Manage subscription")
        print("15. Quit")
        
        choice = input("\nEnter your choice (1-15): ").strip()
        
        if choice == '15':
            print("Thank you for using the Weather Information System!")
            break
            
        # Check for premium features
        if choice in ['2', '6', '7', '8', '9', '11', '12', '13']:
            user_id = input("Enter your user ID (or press Enter to continue as free user): ").strip()
            if not check_premium_access(user_id):
                print("\n🔒 This is a premium feature!")
                print("Upgrade to Premium to access:")
                if choice == '2':
                    print("- Check weather for multiple cities simultaneously")
                elif choice == '6':
                    print("- Compare weather between multiple cities")
                elif choice == '7':
                    print("- Export weather data in CSV/JSON format")
                elif choice == '8':
                    print("- Plot weather trends and generate visualizations")
                elif choice == '9':
                    print("- Set up custom weather notifications")
                elif choice == '11':
                    print("- Access historical weather data")
                elif choice in ['12', '13']:
                    print("- View interactive weather and radar maps")
                
                upgrade = input("\nWould you like to upgrade to Premium? (y/n): ").strip().lower()
                if upgrade == 'y':
                    print("\nPremium Subscription Options:")
                    print("1. Monthly: $4.99/month")
                    print("2. Yearly: $49.99/year (Save 16%)")
                    print("3. Lifetime: $99.99 (One-time payment)")
                    
                    plan = input("\nSelect a plan (1-3): ").strip()
                    if plan in ['1', '2', '3']:
                        # In a real implementation, you would integrate with a payment processor here
                        print("\nThank you for choosing Premium!")
                        print("Please complete the payment process to activate your subscription.")
                        continue
                    else:
                        print("Invalid plan selection.")
                        continue
                else:
                    continue
        
        if choice == '1':
            city = input("Enter city name: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
                
            result = get_weather(city, include_forecast=True)
            if isinstance(result, str):
                print(result)
            else:
                print(format_weather_data(result))
                if 'forecast' in result:
                    print(format_forecast(result['forecast']))
                    
        elif choice == '2':
            cities = input("Enter city names (comma-separated): ").strip()
            if not cities:
                print("Error: Please enter city names")
                continue
                
            for city in [c.strip() for c in cities.split(',')]:
                result = get_weather(city)
                if isinstance(result, str):
                    print(f"\n{city}: {result}")
                else:
                    print(f"\n{format_weather_data(result)}")
                    
        elif choice == '3':
            if not favorites:
                print("No favorite cities saved yet.")
            else:
                print("\nFavorite Cities:")
                for city in favorites:
                    result = get_weather(city)
                    if isinstance(result, str):
                        print(f"\n{city}: {result}")
                    else:
                        print(f"\n{format_weather_data(result)}")
                        
        elif choice == '4':
            city = input("Enter city name to add to favorites: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
                
            if city not in favorites:
                favorites.append(city)
                save_favorites(favorites)
                print(f"{city} added to favorites!")
            else:
                print(f"{city} is already in favorites.")
                
        elif choice == '5':
            if not favorites:
                print("No favorite cities to remove.")
            else:
                print("\nCurrent favorites:")
                for i, city in enumerate(favorites, 1):
                    print(f"{i}. {city}")
                    
                try:
                    index = int(input("Enter the number of the city to remove: ")) - 1
                    if 0 <= index < len(favorites):
                        removed = favorites.pop(index)
                        save_favorites(favorites)
                        print(f"{removed} removed from favorites.")
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Please enter a valid number.")
                    
        elif choice == '6':
            cities = input("Enter city names to compare (comma-separated): ").strip()
            if not cities:
                print("Error: Please enter city names")
                continue
            print(compare_cities([c.strip() for c in cities.split(',')]))
            
        elif choice == '7':
            city = input("Enter city name to export data: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
            format = input("Enter format (csv/json): ").strip().lower()
            if format not in ['csv', 'json']:
                print("Error: Invalid format. Please enter 'csv' or 'json'")
                continue
            print(export_weather_data(city, format))
            
        elif choice == '8':
            city = input("Enter city name to plot trends: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
            print(plot_weather_trends(city))
            
        elif choice == '9':
            city = input("Enter city name for notifications: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
                
            notifications = load_notifications()
            if city not in notifications:
                notifications[city] = {}
                
            try:
                temp_threshold = float(input("Enter temperature threshold (leave empty to skip): ").strip() or 0)
                if temp_threshold:
                    notifications[city]['temp_threshold'] = temp_threshold
                
                conditions = input("Enter weather conditions to alert (comma-separated, leave empty to skip): ").strip()
                if conditions:
                    notifications[city]['conditions'] = [c.strip().lower() for c in conditions.split(',')]
                
                save_notifications(notifications)
                print(f"Notifications set up for {city}")
            except ValueError:
                print("Error: Invalid temperature threshold")
                
        elif choice == '10':
            print(check_notifications())
            
        elif choice == '11':
            print(get_weather_history())
            
        elif choice == '12':
            city = input("Enter city name for weather map: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
            map_type = input("Enter map type (temperature/precipitation/wind): ").strip().lower()
            if map_type not in ['temperature', 'precipitation', 'wind']:
                print("Error: Invalid map type")
                continue
            print(get_weather_map(city, map_type))
            
        elif choice == '13':
            city = input("Enter city name for radar map: ").strip()
            if not city:
                print("Error: Please enter a city name")
                continue
            print(get_radar_map(city))
            
        elif choice == '14':
            # Implement subscription management
            print("Subscription management feature not implemented yet.")
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

print(f"\nPython version: {sys.version}")
print(f"Requests version: {requests.__version__}")
