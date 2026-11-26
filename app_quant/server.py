import json
from flask import Flask, jsonify, render_template
from config import CACHE_FILE
from database import (
    init_db, get_status, get_learning_data, get_asset_history, set_status
)

app = Flask(__name__, template_folder='templates')
init_db()

STOP_EVENT = None
RUN_NOW_EVENT = None

def ler_cache():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'run_at': None, 'results': [], 'charts': {}, 'horizonte_dias': 30}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    from datetime import datetime
    st = get_status()
    cache = ler_cache()
    return jsonify({
        'worker': st,
        'cache': {
            'run_at': cache.get('run_at'),
            'total_results': len(cache.get('results', [])),
            'horizonte_dias': cache.get('horizonte_dias'),
        },
        'server_time': datetime.now().isoformat(timespec='seconds'),
    })

@app.route('/api/results')
def api_results():
    cache = ler_cache()
    return jsonify({
        'run_at': cache.get('run_at'),
        'horizonte_dias': cache.get('horizonte_dias'),
        'results': cache.get('results', []),
    })

@app.route('/api/learning')
def api_learning():
    return jsonify(get_learning_data())

@app.route('/api/asset/<symbol>')
def api_asset(symbol):
    cache = ler_cache()
    chart = cache.get('charts', {}).get(symbol)
    row = next((r for r in cache.get('results', []) if r['Ativo'] == symbol), None)
    return jsonify({
        'symbol': symbol,
        'summary': row,
        'chart': chart,
        'history': get_asset_history(symbol),
    })

@app.route('/api/worker/run-now', methods=['POST'])
def api_run_now():
    if RUN_NOW_EVENT:
        RUN_NOW_EVENT.set()
        return jsonify({'ok': True, 'message': 'Ciclo solicitado'})
    return jsonify({'ok': False, 'message': 'Worker não ativo'}), 400

@app.route('/api/worker/stop', methods=['POST'])
def api_stop_all():
    if STOP_EVENT:
        STOP_EVENT.set()
        set_status(running=0, message='Parando...')
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400


def iniciar_server(stop_event, run_now_event):
    global STOP_EVENT, RUN_NOW_EVENT
    STOP_EVENT = stop_event
    RUN_NOW_EVENT = run_now_event
    from config import HOST, PORT
    app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)