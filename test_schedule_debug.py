import requests

token = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'demo', 'password': 'user123'}).json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("=== 测试LLM推荐 ===")
r = requests.post('http://127.0.0.1:5000/api/routes/llm/recommend', headers=headers, json={
    'preferences': {'themes': ['海边'], 'duration': '全天', 'travel_style': '随意'},
    'weather': {'weather': '多云', 'temp': 26}
})
result = r.json()
if result.get('code') == 200:
    data = result['data']
    print(f"推荐源: {data.get('source')}")
    print(f"景点数量: {len(data.get('attractions', []))}")
    print(f"时间表数量: {len(data.get('schedule', []))}")
    print("\n景点列表:")
    for a in data.get('attractions', []):
        print(f"  ID:{a['id']} 名称:{a['name']}")
    print("\n时间表:")
    for s in data.get('schedule', []):
        print(f"  {s['order']}. {s['start_time']} - {s['end_time']}: 景点{s['attraction_id']}")
else:
    print(f"失败: {result.get('message')}")