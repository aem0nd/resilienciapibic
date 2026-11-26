import sqlite3
from datetime import datetime
from config import DB_FILE

def _conn():
    c = sqlite3.connect(DB_FILE, timeout=30)
    c.execute('PRAGMA journal_mode=WAL')
    return c

def init_db():
    c = _conn()
    cur = c.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS previsoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_previsao TEXT,
            ativo TEXT,
            data_alvo TEXT,
            modelo TEXT,
            preco_previsto REAL,
            preco_real REAL,
            erro_absoluto REAL,
            UNIQUE(ativo, data_alvo, modelo)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS worker_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            running INTEGER DEFAULT 0,
            paused INTEGER DEFAULT 0,
            current_asset TEXT DEFAULT '',
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            last_start TEXT,
            last_end TEXT,
            next_run TEXT,
            message TEXT DEFAULT ''
        )
    ''')
    cur.execute('INSERT OR IGNORE INTO worker_status (id) VALUES (1)')
    c.commit()
    c.close()

def salvar_previsoes(ativo, data_alvo, detalhes):
    c = _conn()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    for modelo, dados in detalhes.items():
        c.execute('''
            INSERT OR REPLACE INTO previsoes
            (data_previsao, ativo, data_alvo, modelo, preco_previsto, preco_real, erro_absoluto)
            VALUES (?, ?, ?, ?, ?, NULL, NULL)
        ''', (data_hoje, ativo, data_alvo, modelo, dados['preco_final']))
    c.commit()
    c.close()

def atualizar_previsoes_passadas(progresso_cb=None):
    from worker import get_ticker
    import yfinance as yf
    from datetime import timedelta

    c = _conn()
    hoje = datetime.now().strftime('%Y-%m-%d')
    rows = c.execute('''
        SELECT id, ativo, data_alvo, preco_previsto
        FROM previsoes WHERE preco_real IS NULL AND data_alvo <= ?
    ''', (hoje,)).fetchall()

    conferidas = falhas = 0
    for i, (idp, ativo, data_alvo, prev) in enumerate(rows):
        try:
            dt = datetime.strptime(data_alvo, '%Y-%m-%d')
            hist = yf.download(
                get_ticker(ativo),
                start=(dt - timedelta(days=5)).strftime('%Y-%m-%d'),
                end=(dt + timedelta(days=2)).strftime('%Y-%m-%d'),
                progress=False, timeout=10
            )
            if not hist.empty:
                if hasattr(hist.columns, 'get_level_values'):
                    hist.columns = hist.columns.get_level_values(0)
                real = float(hist['Close'].iloc[-1])
                erro = abs((real - prev) / real) * 100
                c.execute('UPDATE previsoes SET preco_real=?, erro_absoluto=? WHERE id=?', (real, erro, idp))
                c.commit()
                conferidas += 1
            else:
                falhas += 1
        except Exception:
            falhas += 1
        if progresso_cb and i % 5 == 0:
            progresso_cb(f'Conferindo previsões: {i+1}/{len(rows)}')
    c.close()
    return conferidas, falhas, len(rows)

def calcular_pesos_adaptativos(ativo):
    c = _conn()
    rows = c.execute('''
        SELECT modelo, AVG(erro_absoluto) FROM previsoes
        WHERE ativo=? AND erro_absoluto IS NOT NULL
        GROUP BY modelo
    ''', (ativo,)).fetchall()
    c.close()
    if not rows:
        return {'Prophet': 0.25, 'ARIMA': 0.25, 'XGBoost': 0.25, 'Holt-Winters': 0.25}
    pesos = {m: (1.0 / mape if mape > 0 else 100.0) for m, mape in rows}
    for m in ['Prophet', 'ARIMA', 'XGBoost', 'Holt-Winters']:
        pesos.setdefault(m, 0.01)
    soma = sum(pesos.values())
    return {m: v / soma for m, v in pesos.items()}

def set_status(**kw):
    if not kw:
        return
    c = _conn()
    sets = ', '.join(f'{k}=?' for k in kw)
    c.execute(f'UPDATE worker_status SET {sets} WHERE id=1', tuple(kw.values()))
    c.commit()
    c.close()

def get_status():
    c = _conn()
    row = c.execute('SELECT * FROM worker_status WHERE id=1').fetchone()
    cols = [d[0] for d in c.execute('SELECT * FROM worker_status WHERE id=1').description]
    c.close()
    return dict(zip(cols, row)) if row else {}

def get_learning_data():
    c = _conn()
    rows = c.execute('''
        SELECT data_previsao, modelo, AVG(erro_absoluto), COUNT(*)
        FROM previsoes WHERE erro_absoluto IS NOT NULL
        GROUP BY data_previsao, modelo
        ORDER BY data_previsao
    ''').fetchall()
    tot = c.execute('SELECT COUNT(*), SUM(CASE WHEN preco_real IS NOT NULL THEN 1 ELSE 0 END) FROM previsoes').fetchone()
    c.close()

    by_date = {}
    for dt, mod, mape, n in rows:
        by_date.setdefault(dt, {})[mod] = round(mape, 3)

    return {
        'mape_by_date': [{'date': d, **v} for d, v in sorted(by_date.items())],
        'total_predictions': tot[0] or 0,
        'total_evaluated': tot[1] or 0,
        'evaluation_rate': (tot[1] / tot[0]) if tot[0] else 0
    }

def get_asset_history(symbol):
    c = _conn()
    rows = c.execute('''
        SELECT data_previsao, data_alvo, modelo, preco_previsto, preco_real, erro_absoluto
        FROM previsoes WHERE ativo=? ORDER BY data_previsao DESC LIMIT 100
    ''', (symbol,)).fetchall()
    c.close()
    return [
        {'data_previsao': r[0], 'data_alvo': r[1], 'modelo': r[2],
         'previsto': r[3], 'real': r[4], 'erro': r[5]}
        for r in rows
    ]