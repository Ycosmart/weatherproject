import requests
import pandas as pd

api_key = 'fc438aca992dd0f30dc812e036439b2e' 
cidades = ['Lisboa', 'Madrid', 'Paris', 'Berlim', 'Londres', 'Zurique', 'Copenhaga', 'Bruxelas', 'Viena', 'Roma']


#Function to get all the coordinates of the cities
def obter_coordenadas(cidades, api_key):
    coordenadas = {}
    
    for cidade in cidades:
        try:
            url = f'http://api.openweathermap.org/geo/1.0/direct?q={cidade}&appid={api_key}'
            response = requests.get(url)
            data = response.json()
            
            if len(data) > 0:
                lat = data[0]['lat']  
                lon = data[0]['lon'] 
                coordenadas[cidade] = {'latitude': lat, 'longitude': lon}
            else:
                print(f"Cidade {cidade} não encontrada.")
        
        except Exception as e:
            print(f"Ocorreu um erro ao buscar a cidade {cidade}: {e}")
    
    return coordenadas

#Function to call the API and get JSON response
def Api_call(lat, lon, api_key):
    url_current_call = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    response = requests.get(url_current_call)
    return response.json()  

#Function to extract the intended data from the JSON response
def save_dicts(data):
    combined_dicts = []

    weather_dict = data['weather'][0]
    main_dict = data['main']
    main_dict['visibility'] = data['visibility']
    main_dict['dt'] = data['dt']
    main_dict['timezone'] = data['timezone']
    wind_dict = data['wind']
    rain_dict = data.get('rain', {})
    sys_dict = data['sys']
    
    combined_dict = {**weather_dict, **main_dict, **wind_dict, **sys_dict, **rain_dict}

    combined_dicts.append(combined_dict)

    return combined_dicts


coordenadas = obter_coordenadas(cidades, api_key)

#Loop to iterate over all cities and make API calls to combine the data
all_data = []

for cidade, coords in coordenadas.items():
    lat = coords['latitude']
    lon = coords['longitude']
        
    dados_clima = Api_call(lat, lon, api_key)
    
    dados_finais = save_dicts(dados_clima)
    
    all_data.extend(dados_finais)

#Creating dataframe
df = pd.DataFrame(all_data)

#Cleaning data
df['speed'] = df['speed'] * 3.6
df['speed'] = df['speed'].round(0).astype(int)
df['temp'] = df['temp'].round(0).astype(int)
df['feels_like'] = df['feels_like'].round(0).astype(int)
df['temp_min'] = df['temp_min'].round(0).astype(int)
df['temp_max'] = df['temp_max'].round(0).astype(int)
df['visibility'] = df['visibility'] / 1000
df['dt'] = pd.to_datetime(df['dt'], unit='s')
df['sunrise'] = pd.to_datetime(df['sunrise'], unit='s')
df['sunset'] = pd.to_datetime(df['sunset'], unit='s')
df['dt'] = df['dt'].dt.tz_localize('UTC').dt.tz_convert('Europe/Lisbon')
df['sunrise'] = df['sunrise'].dt.tz_localize('UTC').dt.tz_convert('Europe/Lisbon')
df['sunset'] = df['sunset'].dt.tz_localize('UTC').dt.tz_convert('Europe/Lisbon')
df['dt'] = df['dt'].dt.tz_localize(None)
df['sunrise'] = df['sunrise'].dt.tz_localize(None)
df['sunset'] = df['sunset'].dt.tz_localize(None)
df['description'] = df['description'].str.upper()

description_map = {
    'FEW CLOUDS': 1,
    'CLEAR SKY': 2,
    'LIGHT RAIN': 3,
    'BROKEN CLOUDS': 4,
    'SCATTERED CLOUDS': 4,
    'OVERCAST CLOUDS': 4,
    'LIGHT INTENSITY SHOWER RAIN': 5,
    'MODERATE RAIN': 5 
}

df['clouds_code'] = df['description'].map(description_map)

print(df[['country', 'temp', 'main', 'description', 'clouds_code',]])




    
    



