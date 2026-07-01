import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://trendlyne.com/'
}

url = 'https://trendlyne.com/stock-search/autocomplete/'
response = requests.get(url, params={'q': 'TCS'}, headers=headers)
print(response.status_code)
try:
    print(response.json())
except:
    print(response.text[:200])
