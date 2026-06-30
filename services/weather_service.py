import requests
import json
import os
from datetime import datetime, timedelta
from database import get_db_connection

class WeatherService:
    def __init__(self):
        self.api_url = os.getenv('WEATHER_API_URL', 'http://shanhe.kim/api/za/tianqi.php')
        self.cache_ttl = int(os.getenv('WEATHER_CACHE_TTL', 300))
    
    def get_weather(self, city='厦门'):
        cached = self._get_from_cache(city)
        if cached:
            return cached
        
        weather_data = self._fetch_from_api(city)
        if weather_data:
            self._save_to_cache(city, weather_data)
            return weather_data
        
        return self._get_fallback_data(city)
    
    def _get_from_cache(self, city):
        conn = get_db_connection()
        try:
            cache = conn.execute('''
                SELECT * FROM weather_cache 
                WHERE city = ? AND expires_at > ?
            ''', (city, datetime.now().isoformat())).fetchone()
            
            if cache:
                return json.loads(cache['data'])
            return None
        finally:
            conn.close()
    
    def _save_to_cache(self, city, data):
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM weather_cache WHERE city = ?', (city,))
            conn.execute('''
                INSERT INTO weather_cache (city, data, expires_at)
                VALUES (?, ?, ?)
            ''', (city, json.dumps(data), (datetime.now() + timedelta(seconds=self.cache_ttl)).isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def _fetch_from_api(self, city):
        try:
            response = requests.get(
                self.api_url,
                params={'city': city, 'type': 'json'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 1:
                    return self._normalize_weather_data(data['data'])
            
            return None
        except Exception as e:
            print(f"Weather API error: {e}")
            return None
    
    def _normalize_weather_data(self, raw_data):
        current_temp = raw_data.get('current', {}).get('temp', 'N/A')
        real_time_temp = current_temp if current_temp not in ('999', 'N/A', 'null', '') else 'N/A'
        
        def safe_int(val, default=None):
            try:
                if val in ('N/A', '999', 'null', ''):
                    return default
                return int(float(val))
            except (ValueError, TypeError):
                return default
        
        temp_high = raw_data.get('tempn', 'N/A')
        temp_high_int = safe_int(temp_high)
        real_temp_int = safe_int(real_time_temp)
        
        if temp_high_int is not None:
            if real_temp_int is not None and temp_high_int < real_temp_int:
                display_temp_high = str(real_temp_int + 2) + '°'
            else:
                display_temp_high = str(temp_high_int) + '°'
        else:
            display_temp_high = str(real_temp_int + 2) + '°' if real_temp_int is not None else '暂无'
        
        temp_low = raw_data.get('temp', 'N/A')
        temp_low_int = safe_int(temp_low)
        
        if temp_low_int is not None:
            if real_temp_int is not None and temp_low_int > real_temp_int:
                display_temp_low = str(real_temp_int - 2) + '°'
            else:
                display_temp_low = str(temp_low_int) + '°'
        else:
            display_temp_low = str(real_temp_int - 2) + '°' if real_temp_int is not None else '暂无'   
        
        living = raw_data.get('living', [])
        living_sorted = sorted(living, key=lambda x: 0 if x.get('name') == '旅游指数' else 1)
        
        return {
            'city': raw_data.get('city', '未知'),
            'weather': raw_data.get('weather', '未知'),
            'temp_high': display_temp_high,
            'temp_low': display_temp_low,
            'wind': raw_data.get('wind', ''),
            'windSpeed': raw_data.get('windSpeed', ''),
            'current': {
                'temp': real_time_temp,
                'humidity': raw_data.get('current', {}).get('humidity', 'N/A'),
                'weather': raw_data.get('current', {}).get('weather', '未知'),
                'air': raw_data.get('current', {}).get('air', 'N/A')
            },
            'living': living_sorted,
            'fetched_at': datetime.now().isoformat(),
            'is_fallback': real_time_temp == 'N/A'
        }
    
    def is_good_for_outdoor(self, weather_data):
        if not weather_data:
            return True
        
        weather = weather_data.get('weather', '')
        bad_weather = ['雨', '雪', '雷', '雹']
        
        for bad in bad_weather:
            if bad in weather:
                return False
        
        return True
    
    def _get_fallback_data(self, city='厦门'):
        return {
            'city': city,
            'weather': '晴',
            'temp': '28',
            'temp_high': '32',
            'temp_low': '25',
            'current': {
                'temp': '28',
                'humidity': '65%',
                'weather': '晴',
                'air': '45'
            },
            'living': [
                {'name': '旅游指数', 'index': '较适宜', 'tips': '天气条件较好，适合外出旅游。'},
                {'name': '穿衣指数', 'index': '热', 'tips': '建议穿轻薄衣物。'}
            ],
            'fetched_at': datetime.now().isoformat(),
            'is_fallback': True
        }
    
    def clear_cache(self, city=None):
        conn = get_db_connection()
        try:
            if city:
                conn.execute('DELETE FROM weather_cache WHERE city = ?', (city,))
            else:
                conn.execute('DELETE FROM weather_cache')
            conn.commit()
        finally:
            conn.close()
