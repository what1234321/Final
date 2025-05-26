from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)
API_KEY = '9777155c8a3cc183254aee7ad5ebbafe'
NEWS_API_KEY = '3c464a1ca21944c58aaf5c93c71f19e5'

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

@app.route('/', methods=['GET', 'POST'])
def home():
    # 기본값 설정
    city_input = request.args.get('city', default='Seoul')

    # 도시명 변환
    if city_input in city_map:
        city = city_map[city_input]
    else:
        city = city_input

    # 날씨 정보 가져오기
    weather = get_weather(city)

    # 뉴스 관련 처리
    news_articles = []
    news_error = None
    if request.method == 'POST':
        query = request.form.get('query')
        news_url = f'https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}&language=ko&pageSize=5'
        response = requests.get(news_url)
        if response.status_code == 200:
            news_articles = response.json().get('articles', [])
            if not news_articles:
                news_error = "검색 결과가 없습니다."
        else:
            news_error = "뉴스 정보를 가져오는데 실패했습니다."

    return render_template(
        'index.html',
        weather=weather,
        news_articles=news_articles,
        news_error=news_error
    )


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
    app.run(host='0.0.0.0', port=5000)

