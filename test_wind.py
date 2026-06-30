from services.weather_service import WeatherService
import json

ws = WeatherService()
result = ws.get_weather('厦门')

print('=== 后端返回的完整数据 ===')
print(json.dumps(result, indent=2, ensure_ascii=False))
print()
print('wind:', result.get('wind'))
print('windSpeed:', result.get('windSpeed'))