from flask import Blueprint, jsonify, request
import uuid
from services.weather_service import WeatherService

weather_bp = Blueprint('weather', __name__)
weather_service = WeatherService()

@weather_bp.route('/xiamen', methods=['GET'])
def get_weather():
    try:
        city = request.args.get('city', '厦门')
        weather_data = weather_service.get_weather(city)
        
        message = 'success (cached)' if weather_data.get('is_fallback') is False and weather_data.get('fetched_at') else 'success'
        
        return jsonify({
            'code': 200,
            'message': message,
            'data': weather_data,
            'request_id': str(uuid.uuid4())
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': weather_service._get_fallback_data(),
            'request_id': str(uuid.uuid4())
        }), 500

@weather_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    try:
        city = request.args.get('city')
        weather_service.clear_cache(city)
        
        return jsonify({
            'code': 200,
            'message': 'Weather cache cleared',
            'data': None,
            'request_id': str(uuid.uuid4())
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
            'data': None,
            'request_id': str(uuid.uuid4())
        }), 500