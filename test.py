import json
with open('glav_cities.json', 'r', encoding='utf-8') as g:
    GLAV_CITIES = json.load(g)
der = [city['id'] for city in GLAV_CITIES if city.get('name', '').lower() == ('ерЕван').lower()] 
print(der[0])