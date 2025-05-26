from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)
API_KEY = '9777155c8a3cc183254aee7ad5ebbafe'

city_map = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju', '대전': 'Daejeon',
    '울산': 'Ulsan', '세종': 'Sejong', '수원': 'Suwon', '춘천': 'Chuncheon', '청주': 'Cheongju', '전주': 'Jeonju',
    '목포': 'Mokpo', '창원': 'Changwon', '진주': 'Jinju', '안동': 'Andong', '포항': 'Pohang', '강릉': 'Gangneung',
    '속초': 'Sokcho', '평택': 'Pyeongtaek', '김해': 'Gimhae', '양산': 'Yangsan', '구미': 'Gumi', '여수': 'Yeosu',
    '순천': 'Suncheon', '군산': 'Gunsan', '김천': 'Gimcheon', '제주': 'Jeju'
}

autocomplete_list = list(city_map.keys()) + list(city_map.values())

FAV_FILE = 'favorites.json'

if not os.path.exists(FAV_FILE):
    with open(FAV_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

def load_groups():
    with open(FAV_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_groups(groups):
    with open(FAV_FILE, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    city_input = request.args.get('city', default='Seoul')
    city = city_map.get(city_input, city_input)
    weather = get_weather(city)
    return render_template('index.html', weather=weather)

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '')
    suggestions = [c for c in autocomplete_list if query.lower() in c.lower()]
    return jsonify(suggestions)

@app.route('/weather-data')
def weather_data():
    city = request.args.get('city', default='Seoul')
    weather = get_weather(city)
    return jsonify(weather)

@app.route('/add-group', methods=['POST'])
def add_group():
    data = request.get_json()
    name = data['name']
    entries = data['entries']
    groups = load_groups()
    groups = [g for g in groups if g['group_name'] != name]
    groups.append({'group_name': name, 'entries': entries})
    save_groups(groups)
    return jsonify({'message': '저장 완료', 'groups': groups})

@app.route('/groups')
def get_groups():
    return jsonify(load_groups())

@app.route('/delete-group', methods=['POST'])
def delete_group():
    name = request.get_json()['name']
    groups = load_groups()
    groups = [g for g in groups if g['group_name'] != name]
    save_groups(groups)
    return '', 204

@app.route('/get-group-weather')
def get_group_weather():
    name = request.args.get('group')
    groups = load_groups()
    group = next((g for g in groups if g['group_name'] == name), None)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    results = []
    for entry in group['entries']:
        city = entry['city']
        weather = get_weather(city)
        if weather.get('error'): continue
        results.append({
            'weekday': entry['weekday'],
            'time': entry['time'],
            'city': city,
            'temperature': weather['temperature'],
            'description': weather['description'],
            'humidity': weather['humidity']
        })
    return jsonify({'results': results, 'city': name})

def get_weather(city):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=kr'
    response = requests.get(url)
    data = response.json()
    if data.get('cod') != 200:
        return {
            'city': city,
            'error': f"'{city}'의 날씨를 찾을 수 없습니다. (영문 도시명은 첫 글자를 대문자로 입력하세요. 예: Busan)"
        }
    else:
        return {
            'city': city,
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'rain': data.get('rain', {}).get('1h', 0),
            'error': None
        }

if __name__ == '__main__':
    app.run()
