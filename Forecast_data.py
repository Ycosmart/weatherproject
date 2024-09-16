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
    url_current_call = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    response = requests.get(url_current_call)
    return response.json()  

#Function to extract the intended data from the JSON response
def save_main_dicts(data):
    combined_dicts = []
    for i in range(40):  
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

        combined_dict = {**main_dict, **weather_dict, **clouds_dict, **wind_dict, **sys_dict, **city_dict}

        combined_dicts.append(combined_dict)
        
    return combined_dicts


coordenadas = obter_coordenadas(cidades, api_key)

#Loop to iterate over all cities and make API calls to combine the data
all_data = []

for cidade, coords in coordenadas.items():
    lat = coords['latitude']
    lon = coords['longitude']
        
    dados_clima = Api_call(lat, lon, api_key)
    
    dados_finais = save_main_dicts(dados_clima)
    
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

df.rename(columns={'all': 'cloudiness', 'pod': 'part_of_the_day', 'pop': 'probability_of_precipitation'}, inplace=True)


df['visibility'] = df['visibility'] / 1000
#df.to_excel('weather.xlsx', index=False)
df = df.drop(columns=['temp_kf', 'id', 'icon', 'name', 'coord', 'population', 'deg', 'gust', 'timezone'])
#df.to_excel('weather.xlsx', index=False)
df['dt'] = pd.to_datetime(df['dt'], unit='s')
df['sunrise'] = pd.to_datetime(df['sunrise'], unit='s')
df['sunset'] = pd.to_datetime(df['sunset'], unit='s')
df['description'] = df['description'].str.upper()

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

city_map = {
    'PT': 'Lisbon, Portugal',
    'AT': 'Vienna, Austria',
    'ES': 'Madrid, Espanha',
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
df['date_only'] = pd.to_datetime(df['dt_txt']).dt.date
df['probability_of_precipitation'] = df['probability_of_precipitation']*100
df['probability_of_precipitation'] = df['probability_of_precipitation'].apply(lambda x: f"{int(x)}%")

def moda(grupo):
    return grupo.mode().iloc[0]


moda_df = df.groupby(['country', 'date_only'])['clouds_code'].apply(moda).reset_index()


moda_df.rename(columns={'clouds_code': 'clouds_code_mode'}, inplace=True)


df = df.merge(moda_df, on=['country', 'date_only'], how='left')





    
    



