import os
import requests
import pandas as pd
from  dotenv import load_dotenv

load_dotenv()

# Load the API key from environment variables
api_key = os.getenv('WEATHER_API_KEY')

if not api_key:
    raise ValueError("API key not found. Please set the WEATHER_API_KEY environment variable.")

cities = [
    'Lisbon', 'Madrid', 'Paris', 'Berlin', 'London',
    'Zurich', 'Copenhagen', 'Brussels', 'Vienna', 'Rome'
]

# Function to get the coordinates of the cities
def get_coordinates(cities, api_key):
    coordinates = {}
    for city in cities:
        try:
            url = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={api_key}'
            response = requests.get(url)
            data = response.json()

            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']
                coordinates[city] = {'latitude': lat, 'longitude': lon}
            else:
                print(f"City {city} not found.")
        except Exception as e:
            print(f"Error fetching city {city}: {e}")
    return coordinates

# Function to call the weather API
def api_call(lat, lon, api_key):
    url = (
        f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    )
    response = requests.get(url)
    return response.json()

# Function to extract the required data from the API response
def save_main_dicts(data):
    combined_dicts = []
    for i in range(40):  # Extract data for 40 forecast entries
        main_dict = data['list'][i]['main']
        main_dict['dt'] = data['list'][i]['dt']
        main_dict['visibility'] = data['list'][i]['visibility']
        main_dict['pop'] = data['list'][i]['pop']
        main_dict['dt_txt'] = data['list'][i]['dt_txt']

        weather_dict = data['list'][i]['weather'][0]
        clouds_dict = data['list'][i]['clouds']
        wind_dict = data['list'][i]['wind']
        sys_dict = data['list'][i]['sys']
        city_dict = data['city']

        combined_dict = {
            **main_dict, **weather_dict, **clouds_dict, **wind_dict,
            **sys_dict, **city_dict
        }

        combined_dicts.append(combined_dict)
    return combined_dicts

# Get the coordinates of all cities
coordinates = get_coordinates(cities, api_key)

# Loop through all cities to fetch weather data
all_data = []
for city, coords in coordinates.items():
    lat = coords['latitude']
    lon = coords['longitude']

    weather_data = api_call(lat, lon, api_key)
    final_data = save_main_dicts(weather_data)

    all_data.extend(final_data)

# Create a DataFrame from the combined data
df = pd.DataFrame(all_data)

# Clean and process data
df['speed'] = df['speed'] * 3.6
df['speed'] = df['speed'].round(0).astype(int)
df['temp'] = df['temp'].round(0).astype(int)
df['feels_like'] = df['feels_like'].round(0).astype(int)
df['temp_min'] = df['temp_min'].round(0).astype(int)
df['temp_max'] = df['temp_max'].round(0).astype(int)

# Rename columns for clarity
df.rename(
    columns={
        'all': 'cloudiness',
        'pod': 'part_of_the_day',
        'pop': 'probability_of_precipitation'
    },
    inplace=True
)

# Convert visibility to kilometers
df['visibility'] = df['visibility'] / 1000

# Drop unnecessary columns
df.drop(columns=['temp_kf', 'id', 'icon', 'name', 'coord', 'population', 'deg', 'gust', 'timezone'], inplace=True)

# Convert timestamps to datetime
df['dt'] = pd.to_datetime(df['dt'], unit='s')
df['sunrise'] = pd.to_datetime(df['sunrise'], unit='s')
df['sunset'] = pd.to_datetime(df['sunset'], unit='s')

# Convert weather descriptions to uppercase
df['description'] = df['description'].str.upper()

# Map weather descriptions to codes
description_map = {
    'FEW CLOUDS': 1,
    'CLEAR SKY': 2,
    'LIGHT RAIN': 3,
    'BROKEN CLOUDS': 4,
    'SCATTERED CLOUDS': 4,
    'OVERCAST CLOUDS': 4,
    'LIGHT INTENSITY SHOWER RAIN': 5,
    'MODERATE RAIN': 5,
    'HEAVY INTENSITY RAIN': 5
}

# Map city codes to city-country names
city_map = {
    'PT': 'Lisbon, Portugal',
    'AT': 'Vienna, Austria',
    'ES': 'Madrid, Spain',
    'FR': 'Paris, France',
    'DE': 'Berlin, Germany',
    'GB': 'London, UK',
    'CH': 'Zurich, Switzerland',
    'DK': 'Copenhagen, Denmark',
    'BE': 'Brussels, Belgium',
    'IT': 'Rome, Italy'
}

df['city_country'] = df['country'].map(city_map)
df['clouds_code'] = df['description'].map(description_map)

# Extract date from datetime
df['date_only'] = pd.to_datetime(df['dt_txt']).dt.date

# Adjust probability of precipitation to percentages
df['probability_of_precipitation'] = df['probability_of_precipitation'] * 100
df['probability_of_precipitation'] = df['probability_of_precipitation'].apply(lambda x: f"{int(x)}%")

# Function to get the mode of cloud codes for each day
def get_mode(group):
    return group.mode().iloc[0]

# Calculate the mode of clouds for each country and date
mode_df = df.groupby(['country', 'date_only'])['clouds_code'].apply(get_mode).reset_index()

# Rename the column
mode_df.rename(columns={'clouds_code': 'clouds_code_mode'}, inplace=True)

# Merge the mode data back into the main DataFrame
df = df.merge(mode_df, on=['country', 'date_only'], how='left')

print(df)
