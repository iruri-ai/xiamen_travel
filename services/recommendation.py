import os
import json
import math
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

LLM_TIMEOUT = 15
LLM_MAX_RETRIES = 1

class RecommendationService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_base = os.getenv('LLM_API_BASE', 'https://api.deepseek.com')
        self.model_name = os.getenv('LLM_MODEL_NAME', 'deepseek-v4-flash')
        self.use_mock = not self.api_key or self.api_key == 'your_api_key_here'
        self.attraction_data = {}
        self._load_attractions_from_db()

    def _load_attractions_from_db(self):
        try:
            from database import get_db_connection
            conn = get_db_connection()
            attractions = conn.execute('SELECT * FROM attractions').fetchall()
            
            for attr in attractions:
                tags = conn.execute('''
                    SELECT t.name FROM tags t
                    JOIN attraction_tags at ON t.id = at.tag_id
                    WHERE at.attraction_id = ?
                ''', (attr['id'],)).fetchall()
                
                tag_names = [t['name'] for t in tags]
                
                intensity = '低'
                duration = attr['recommended_duration']
                if duration >= 300:
                    intensity = '中'
                if duration >= 480:
                    intensity = '高'
                
                duration_minutes = attr['recommended_duration']
                formatted_duration = f"约{duration_minutes // 60}小时" if duration_minutes >= 60 else f"约{duration_minutes}分钟"
                
                self.attraction_data[attr['id']] = {
                    'id': attr['id'],
                    'name': attr['name'],
                    'image': attr['image_url'],
                    'desc': attr['description'],
                    'open_time': attr['open_time'],
                    'recommended_duration': attr['recommended_duration'],
                    'formatted_duration': formatted_duration,
                    'area': attr['area'],
                    'tags': tag_names,
                    'intensity': intensity,
                    'location': {'lat': attr['latitude'], 'lng': attr['longitude']},
                    'ticket_info': '免费' if attr['price'] == 0 else f'¥{attr["price"]}',
                    'rating': attr['rating'],
                    'popularity': attr['popularity']
                }
            
            conn.close()
        except Exception as e:
            print(f"Failed to load attractions from database: {e}")
            self._load_fallback_data()

    def _format_duration(self, minutes):
        return f"约{minutes // 60}小时" if minutes >= 60 else f"约{minutes}分钟"
    
    def _load_fallback_data(self):
        self.attraction_data = {
            1: {
                'id': 1,
                'name': '鼓浪屿',
                'image': '/static/images/gulangyu.jpg',
                'desc': '海岛风光、世界文化遗产',
                'open_time': '全天开放',
                'recommended_duration': 360,
                'formatted_duration': self._format_duration(360),
                'area': '思明区',
                'tags': ['摄影', '人文', '海边', '历史'],
                'intensity': '中',
                'location': {'lat': 24.4446, 'lng': 118.0666},
                'ticket_info': '需乘船',
                'rating': 4.8,
                'popularity': 98
            },
            2: {
                'id': 2,
                'name': '厦门大学',
                'image': '/static/images/xiamen_university.jpg',
                'desc': '中国最美大学',
                'open_time': '12:00-14:00, 17:00后',
                'recommended_duration': 180,
                'formatted_duration': self._format_duration(180),
                'area': '思明区',
                'tags': ['摄影', '人文', '自然风光'],
                'intensity': '低',
                'location': {'lat': 24.4346, 'lng': 118.0819},
                'ticket_info': '免费',
                'rating': 4.7,
                'popularity': 95
            },
            3: {
                'id': 3,
                'name': '环岛路',
                'image': '/static/images/huan_dao_road.jpg',
                'desc': '海滨骑行、沙滩休闲',
                'open_time': '全天开放',
                'recommended_duration': 240,
                'formatted_duration': self._format_duration(240),
                'area': '思明区',
                'tags': ['亲子', '摄影', '海边', '低强度', '自然风光'],
                'intensity': '低',
                'location': {'lat': 24.4423, 'lng': 118.1066},
                'ticket_info': '免费',
                'rating': 4.6,
                'popularity': 90
            },
            4: {
                'id': 4,
                'name': '南普陀寺',
                'image': '/static/images/nanputuo_temple.jpg',
                'desc': '千年古刹，人文历史景点',
                'open_time': '8:00-17:30',
                'recommended_duration': 120,
                'formatted_duration': self._format_duration(120),
                'area': '思明区',
                'tags': ['人文', '历史', '自然风光'],
                'intensity': '低',
                'location': {'lat': 24.4396, 'lng': 118.0789},
                'ticket_info': '免费',
                'rating': 4.5,
                'popularity': 85
            },
            5: {
                'id': 5,
                'name': '曾厝垵',
                'image': '/static/images/zengcuoan.jpg',
                'desc': '文艺渔村，美食聚集地',
                'open_time': '全天开放',
                'recommended_duration': 180,
                'formatted_duration': self._format_duration(180),
                'area': '思明区',
                'tags': ['亲子', '美食', '海边'],
                'intensity': '低',
                'location': {'lat': 24.4646, 'lng': 118.1166},
                'ticket_info': '免费',
                'rating': 4.4,
                'popularity': 88
            },
            6: {
                'id': 6,
                'name': '沙坡尾',
                'image': '/static/images/shapowei.jpg',
                'desc': '网红文艺创意园区',
                'open_time': '全天开放',
                'recommended_duration': 150,
                'formatted_duration': self._format_duration(150),
                'area': '思明区',
                'tags': ['摄影', '美食', '自然风光'],
                'intensity': '低',
                'location': {'lat': 24.4316, 'lng': 118.0689},
                'ticket_info': '免费',
                'rating': 4.3,
                'popularity': 82
            },
            7: {
                'id': 7,
                'name': '中山路',
                'image': '/static/images/zhongshan_road.jpg',
                'desc': '百年老街，繁华商业街',
                'open_time': '全天开放',
                'recommended_duration': 180,
                'formatted_duration': self._format_duration(180),
                'area': '思明区',
                'tags': ['购物', '美食', '人文', '历史'],
                'intensity': '低',
                'location': {'lat': 24.4566, 'lng': 118.0819},
                'ticket_info': '免费',
                'rating': 4.5,
                'popularity': 92
            }
        }

    def _calculate_distance(self, loc1, loc2):
        if not loc1 or not loc2:
            return float('inf')
        lat1, lng1 = loc1['lat'], loc1['lng']
        lat2, lng2 = loc2['lat'], loc2['lng']
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlng/2) * math.sin(dlng/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _get_attractions_by_preference(self, themes):
        if not themes:
            return sorted(self.attraction_data.keys(), key=lambda aid: -self.attraction_data[aid]['popularity'])
        
        scored = []
        for aid, attr in self.attraction_data.items():
            score = attr['popularity'] * 0.1
            for theme in themes:
                if theme in attr['tags']:
                    score += 5
                if theme == '低强度' and attr['intensity'] == '低':
                    score += 3
                if theme == '亲子' and attr['intensity'] in ('低', '中'):
                    score += 2
            scored.append((aid, score))
        
        scored.sort(key=lambda x: -x[1])
        return [aid for aid, _ in scored]

    def _filter_by_weather(self, attraction_ids, weather_info):
        if not weather_info:
            return attraction_ids
        
        weather = weather_info.get('weather', '')
        bad_weather = ['雨', '雪', '雷', '雹']
        has_bad_weather = any(bad in weather for bad in bad_weather)
        
        if not has_bad_weather:
            return attraction_ids
        
        def is_all_day(open_time):
            if open_time == '全天开放':
                return True
            if open_time.strip() == '全天':
                return True
            if '周末全天' in open_time or '节假日全天' in open_time:
                return True
            return False
        
        filtered = []
        for aid in attraction_ids:
            attr = self.attraction_data[aid]
            if is_all_day(attr['open_time']):
                filtered.append(aid)
        
        if filtered:
            return filtered
        
        fallback_ids = [aid for aid in self.attraction_data.keys() 
                        if is_all_day(self.attraction_data[aid]['open_time'])]
        
        return fallback_ids if fallback_ids else list(self.attraction_data.keys())[:3]

    def _parse_open_time(self, open_time_str):
        if not open_time_str:
            return [(9 * 60, 18 * 60)]
        
        if open_time_str == '全天开放':
            return [(0, 24 * 60)]
        
        pure_all_day = open_time_str.strip() == '全天'
        has_weekend_all_day = '周末全天' in open_time_str or '节假日全天' in open_time_str
        
        if pure_all_day and not has_weekend_all_day:
            return [(0, 24 * 60)]
        
        windows = []
        temp_str = open_time_str.replace('后', '-24:00')
        
        for keyword in ['周一', '周二', '周三', '周四', '周五', '周六', '周日', '周末', '节假日', '；']:
            temp_str = temp_str.replace(keyword, ',')
        
        parts = [p.strip() for p in temp_str.split(',') if p.strip()]
        
        for part in parts:
            if '-' in part:
                times = part.split('-')
                if len(times) == 2:
                    try:
                        start = times[0].strip()
                        end = times[1].strip()
                        
                        if not start or not end:
                            continue
                        
                        start_parts = start.split(':')
                        end_parts = end.split(':')
                        
                        start_minutes = int(start_parts[0]) * 60 + (int(start_parts[1]) if len(start_parts) > 1 else 0)
                        end_minutes = int(end_parts[0]) * 60 + (int(end_parts[1]) if len(end_parts) > 1 else 0)
                        
                        if end_minutes <= start_minutes:
                            end_minutes += 24 * 60
                        
                        windows.append((start_minutes, end_minutes))
                    except:
                        pass
        
        if windows:
            return windows
        elif has_weekend_all_day:
            return [(0, 24 * 60)]
        else:
            return [(9 * 60, 18 * 60)]
    
    def _find_next_valid_start(self, current_time, open_windows):
        for start, end in open_windows:
            if current_time < start:
                return start
            if current_time < end:
                return current_time
        
        next_day_start = open_windows[0][0] + 24 * 60
        return next_day_start
    
    def _build_time_schedule(self, attraction_ids):
        schedule = []
        current_time = 9 * 60
        
        for i, aid in enumerate(attraction_ids):
            attr = self.attraction_data[aid]
            open_windows = self._parse_open_time(attr['open_time'])
            
            adjusted_start = self._find_next_valid_start(current_time, open_windows)
            
            start_hour = adjusted_start // 60
            start_min = adjusted_start % 60
            start_str = f"{start_hour:02d}:{start_min:02d}"
            
            end_time = adjusted_start + attr['recommended_duration']
            end_hour = end_time // 60
            end_min = end_time % 60
            end_str = f"{end_hour:02d}:{end_min:02d}"
            
            schedule.append({
                'attraction_id': aid,
                'order': i + 1,
                'start_time': start_str,
                'end_time': end_str,
                'duration': attr['recommended_duration']
            })
            
            current_time = end_time + 30
        
        return schedule

    def _generate_reason_for_attraction(self, attr, themes, weather_info):
        reasons = []
        
        if '亲子' in themes:
            reasons.append('适合亲子互动')
        if '摄影' in themes:
            reasons.append('拍照出片率高')
        if '人文' in themes:
            reasons.append('文化底蕴深厚')
        if '历史' in themes:
            reasons.append('历史悠久')
        if '海边' in themes:
            reasons.append('海滨风光优美')
        if '美食' in themes:
            reasons.append('周边美食丰富')
        if '低强度' in themes:
            reasons.append('游玩强度低')
        
        if weather_info:
            weather = weather_info.get('weather', '')
            if '雨' in weather:
                if attr['open_time'] == '全天开放' or '全天' in attr['open_time']:
                    reasons.append('雨天也可游玩')
        
        if not reasons:
            reasons.append(f'评分{attr["rating"]}分，人气较高')
        
        return '，'.join(reasons[:3])

    def get_recommendation(self, user_preferences, weather_info):
        if self.use_mock:
            print("Using mock recommendation (no API key configured)")
            return self._get_mock_recommendation(user_preferences, weather_info)

        print(f"Starting LLM recommendation with preferences: {user_preferences}")
        try:
            result = self._get_llm_recommendation(user_preferences, weather_info)
            print(f"Recommendation completed using: {result.get('source', 'unknown')}")
            return result
        except Exception as e:
            print(f"Unexpected error in recommendation: {e}")
            print(traceback.format_exc())
            return self._get_mock_recommendation(user_preferences, weather_info)

    def _get_llm_recommendation(self, user_preferences, weather_info):
        for attempt in range(LLM_MAX_RETRIES):
            try:
                from openai import OpenAI

                import httpx
                client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                    timeout=httpx.Timeout(LLM_TIMEOUT, connect=5)
                )

                prompt = self._build_prompt(user_preferences, weather_info)
                
                start_time = time.time()

                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的厦门旅游推荐专家，擅长根据用户偏好推荐合适的景点和游玩路线。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7,
                    top_p=0.8,
                    stream=False
                )

                elapsed = time.time() - start_time
                print(f"LLM call completed in {elapsed:.2f}s")

                result_text = response.choices[0].message.content
                parsed = self._parse_llm_response(result_text, user_preferences, weather_info)
                
                if not parsed['attractions']:
                    raise ValueError("LLM returned empty attractions list")
                
                return parsed

            except ImportError:
                print("openai not installed, using mock recommendation")
                return self._get_mock_recommendation(user_preferences, weather_info)
            except TimeoutError as e:
                print(f"LLM timeout on attempt {attempt + 1}: {e}")
                if attempt == LLM_MAX_RETRIES - 1:
                    print("All LLM retries exhausted, falling back to rule-based")
                    return self._get_mock_recommendation(user_preferences, weather_info)
            except Exception as e:
                print(f"LLM error on attempt {attempt + 1}: {e}")
                print(traceback.format_exc())
                if attempt == LLM_MAX_RETRIES - 1:
                    print("All LLM retries exhausted, falling back to rule-based")
                    return self._get_mock_recommendation(user_preferences, weather_info)
        
        return self._get_mock_recommendation(user_preferences, weather_info)

    def _build_prompt(self, user_preferences, weather_info):
        themes = user_preferences.get('themes', [])
        duration = user_preferences.get('duration', '全天')
        travel_style = user_preferences.get('travel_style', '随意')

        if isinstance(duration, int):
            duration_str = f"{duration}分钟"
        else:
            duration_str = duration

        weather_desc = ""
        if weather_info:
            weather_desc = f"当前天气：{weather_info.get('weather', '未知')}，温度{weather_info.get('temp', 'N/A')}℃"

        attractions_desc = "\n".join([
            f"{aid}. {attr['name']} - {attr['desc'][:30]}...（开放时间：{attr['open_time']}，推荐时长：{attr['recommended_duration']}分钟，强度：{attr['intensity']}，评分：{attr['rating']}，标签：{','.join(attr['tags'])}）"
            for aid, attr in self.attraction_data.items()
        ])

        prompt = f"""你是一个厦门旅游推荐专家。请根据以下信息为用户推荐景点和游玩路线。

用户偏好：
- 偏好主题：{', '.join(themes) if themes else '无特定偏好'}
- 时间安排：{duration_str}
- 旅行风格：{travel_style}

{weather_desc}

厦门景点详情（从数据库读取）：
{attractions_desc}

请用JSON格式返回推荐结果，包含：
- reason: 整体推荐理由（100字以内，说明为什么推荐这些景点组合）
- recommended_attractions: 推荐景点列表，每个元素包含：
  - id: 景点ID（数字）
  - reason: 该景点的推荐理由（50字以内，结合用户偏好说明）
- tips: 游玩小贴士（100字以内，包含交通、注意事项、最佳游玩时间）

注意：
1. 根据时间安排合理选择景点数量，避免超时
2. 考虑景点间距离，尽量选择相邻区域的景点
3. 如果天气不佳，优先推荐室内或全天开放的景点
4. 如果用户选择低强度，避免推荐需要长时间步行的景点
5. recommended_attractions中的ID必须是景点详情中存在的有效ID
6. 只返回纯JSON文本，不要markdown代码块、不要多余文字。"""

        return prompt

    def _parse_llm_response(self, response_text, user_preferences, weather_info):
        try:
            json_str = response_text.strip()
            if json_str.startswith('```'):
                lines = json_str.split('\n')
                if lines[-1] == '```':
                    json_str = '\n'.join(lines[1:-1])
                else:
                    json_str = '\n'.join(lines[1:])

            result = json.loads(json_str)
            themes = user_preferences.get('themes', [])
            
            recommended_items = result.get('recommended_attractions', [])
            
            if not isinstance(recommended_items, list) or len(recommended_items) == 0:
                raise ValueError("recommended_attractions must be a non-empty list")
            
            id_list = []
            attraction_list = []
            
            for item in recommended_items:
                if isinstance(item, int):
                    aid = item
                    llm_reason = None
                elif isinstance(item, dict) and 'id' in item:
                    aid = item['id']
                    llm_reason = item.get('reason')
                else:
                    continue
                
                if aid in self.attraction_data:
                    attr = self.attraction_data[aid].copy()
                    if llm_reason and llm_reason.strip():
                        attr['recommend_reason'] = llm_reason.strip()
                    else:
                        attr['recommend_reason'] = self._generate_reason_for_attraction(attr, themes, weather_info)
                    attraction_list.append(attr)
                    id_list.append(aid)
            
            if not id_list:
                raise ValueError("No valid attraction IDs found in response")

            duration = user_preferences.get('duration', '全天')
            if isinstance(duration, int):
                max_duration = duration
            else:
                duration_map = {'2小时': 120, '半天': 240, '全天': 480}
                max_duration = duration_map.get(duration, 480)
            
            total_time = sum(self.attraction_data[aid]['recommended_duration'] for aid in id_list)
            total_time += max(0, len(id_list) - 1) * 30
            
            if total_time > max_duration * 1.2:
                print(f"LLM recommendation exceeds duration: {total_time}min > {max_duration}min, truncating")
                
                truncated_ids = []
                current_total = 0
                for aid in id_list:
                    time_needed = self.attraction_data[aid]['recommended_duration']
                    buffer = 30 if truncated_ids else 0
                    if current_total + buffer + time_needed <= max_duration:
                        if truncated_ids:
                            current_total += buffer
                        truncated_ids.append(aid)
                        current_total += time_needed
                
                if not truncated_ids:
                    truncated_ids = [id_list[0]]
                
                attraction_list = []
                for aid in truncated_ids:
                    attr = self.attraction_data[aid].copy()
                    attr['recommend_reason'] = self._generate_reason_for_attraction(attr, themes, weather_info)
                    attraction_list.append(attr)
                
                id_list = truncated_ids

            schedule = self._build_time_schedule(id_list)
            
            return {
                'reason': result.get('reason', '基于您的偏好推荐'),
                'attractions': attraction_list,
                'schedule': schedule,
                'tips': result.get('tips', '祝您旅途愉快！'),
                'source': 'llm'
            }
        except (json.JSONDecodeError, ValueError) as e:
            print(f"LLM response parsing failed: {e}")
            return self._get_mock_recommendation(user_preferences, weather_info)

    def _get_mock_recommendation(self, user_preferences, weather_info):
        themes = user_preferences.get('themes', [])
        duration = user_preferences.get('duration', '全天')
        
        if isinstance(duration, int):
            duration_minutes = duration
        else:
            duration_map = {'2小时': 120, '半天': 240, '全天': 480}
            duration_minutes = duration_map.get(duration, 480)

        scored_ids = self._get_attractions_by_preference(themes)
        filtered_ids = self._filter_by_weather(scored_ids, weather_info)
        
        if not filtered_ids:
            filtered_ids = list(self.attraction_data.keys())

        recommended_ids = []
        current_total_time = 0
        
        for aid in filtered_ids:
            attr = self.attraction_data[aid]
            time_needed = attr['recommended_duration']
            
            if recommended_ids:
                buffer_time = 30
            else:
                buffer_time = 0
            
            if current_total_time + buffer_time + time_needed <= duration_minutes:
                if recommended_ids:
                    current_total_time += buffer_time
                recommended_ids.append(aid)
                current_total_time += time_needed

        if not recommended_ids:
            recommended_ids = [next(iter(self.attraction_data.keys()))]

        attraction_list = []
        for aid in recommended_ids:
            attr = self.attraction_data[aid].copy()
            attr['recommend_reason'] = self._generate_reason_for_attraction(attr, themes, weather_info)
            attraction_list.append(attr)

        schedule = self._build_time_schedule(recommended_ids)

        reason_parts = []
        if themes:
            reason_parts.append(f"根据您的「{', '.join(themes)}」偏好")
        if weather_info and '雨' in weather_info.get('weather', ''):
            reason_parts.append("考虑到天气情况")
        
        if duration_minutes <= 120:
            reason_parts.append("推荐精选景点")
        elif duration_minutes <= 240:
            reason_parts.append("为您规划半日游路线")
        else:
            reason_parts.append("为您规划一日游路线")
        
        reason = "，".join(reason_parts) + "，路线涵盖开放时间合适、推荐时长匹配的景点。"

        tips_parts = []
        if 1 in recommended_ids:
            tips_parts.append("鼓浪屿建议提前购买船票")
        if 2 in recommended_ids:
            tips_parts.append("厦大需提前预约参观")
        if weather_info and '雨' in weather_info.get('weather', ''):
            tips_parts.append("雨天注意携带雨具")
        if '亲子' in themes:
            tips_parts.append("带儿童建议避开人流高峰")
        
        tips = "、".join(tips_parts) + "。" if tips_parts else "祝您旅途愉快！"

        return {
            'reason': reason,
            'attractions': attraction_list,
            'schedule': schedule,
            'tips': tips,
            'source': 'rule-based'
        }
