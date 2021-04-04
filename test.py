import json
with open('shiptor_cities.json', 'r', encoding='utf-8') as g:
    shiptor_cities = json.load(g)
derival_shiptor = [city['kladr_id'] for city in shiptor_cities if city.get('name', '').lower() == ('Луховицы').lower()] 
#for item in GLAV_CITIES:
 #   del item['parents']
#with open('a.json', 'w', encoding='utf-8') as f:
 #   json.dump(GLAV_CITIES, f, indent=4, ensure_ascii=False,)
print(derival_shiptor[0])