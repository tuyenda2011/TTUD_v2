import requests

API_KEY = 'b10e32bf-7b05-4762-977b-ee3c7af85080'
url = 'https://graphhopper.com/api/1/route'
params = {
    'point': ['20.9821,105.7913', '21.0285,105.7891'],
    'vehicle': 'car',
    'locale': 'vi',
    'key': API_KEY
}

response = requests.get(url, params=params)
print('Status:', response.status_code)
data = response.json()
print('Code:', data.get('code'))
print('Has paths:', 'paths' in data)
if 'paths' in data and len(data['paths']) > 0:
    path = data['paths'][0]
    print('Distance (km):', path['distance'] / 1000)
    print('Time (min):', path['time'] / 60000)
