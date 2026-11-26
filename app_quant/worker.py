import time
import json
import threading
import warnings
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from prophet import Prophet
import pmdarima_rs as pm
import xgboost as xgb
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from config import HORIZONTE_DIAS, INTERVALO_HORAS, CACHE_FILE
from database import (
    init_db, salvar_previsoes, calcular_pesos_adaptativos,
    atualizar_previsoes_passadas, set_status
)

warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('peewee').setLevel(logging.CRITICAL)
logging.getLogger('prophet').setLevel(logging.CRITICAL)
logging.getLogger('cmdstanpy').setLevel(logging.CRITICAL)

CRIPTOS = {'BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD','AVAX-USD','DOT-USD','LINK-USD','LTC-USD','SHIB-USD'}
INTERNACIONAIS = {'AAPL','MSFT','GOOGL','AMZN','TSLA','NVDA','META','BRK-B','JPM','V','JNJ','WMT','SPY','QQQ'}
ETFS = {'BOVA11','IBOB11','IVVB11','SMAL11','PIBB11','LFTX11','XB3011','XB3511','BNDX11','USDB11','FIND11','MATB11','DOLA11','GOLD11','ECOO11'}

def get_ticker(symbol):
    return symbol if (symbol in CRIPTOS or symbol in INTERNACIONAIS) else f"{symbol}.SA"

def _extract_close(data):
    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
        return pd.Series(dtype=float, name='Close')
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if 'Close' not in df.columns:
        return pd.Series(dtype=float, name='Close')
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return pd.to_numeric(close, errors='coerce').dropna()

def _safe_float(v, default=0.0):
    try:
        if v is None: return default
        if isinstance(v, (pd.Series, pd.DataFrame)):
            arr = np.asarray(v, dtype=float).ravel()
            if arr.size == 0: return default
            v = arr[0]
        v = float(np.asarray(v, dtype=float).ravel()[0])
        return v if np.isfinite(v) else default
    except Exception:
        return default

def safe_round(v, c=2): return round(_safe_float(v), c)

def calc_rsi(s, p=14):
    try:
        if s is None or len(s) < p + 1: return 50.0
        d = s.diff()
        g = d.clip(lower=0).rolling(p).mean()
        l = (-d.clip(upper=0)).rolling(p).mean()
        ug, ul = _safe_float(g.iloc[-1]), _safe_float(l.iloc[-1])
        if ul == 0: return 100.0 if ug > 0 else 50.0
        return float(100 - 100 / (1 + ug / ul))
    except Exception:
        return 50.0

def calc_sharpe(r, rf=0, ppy=252):
    try:
        if r is None or len(r) < 2: return 0.0
        sd = _safe_float(r.std())
        return 0.0 if sd == 0 else float((_safe_float(r.mean()) * ppy - rf) / (sd * np.sqrt(ppy)))
    except Exception:
        return 0.0

def calc_sortino(r, rf=0, ppy=252):
    try:
        if r is None or len(r) < 2: return 0.0
        neg = r[r < 0]
        if len(neg) == 0: return 0.0
        ds = _safe_float(neg.std())
        return 0.0 if ds == 0 else float((_safe_float(r.mean()) * ppy - rf) / (ds * np.sqrt(ppy)))
    except Exception:
        return 0.0

def calc_var_cvar(r, a=0.95):
    try:
        if r is None or len(r) < 10: return 0.0, 0.0
        arr = np.asarray(r, dtype=float).ravel()
        v = float(np.percentile(arr, (1 - a) * 100))
        m = arr <= v
        return v, (float(arr[m].mean()) if m.any() else v)
    except Exception:
        return 0.0, 0.0

def calc_macd(s, f=12, sl=26, sg=9):
    try:
        if s is None or len(s) < sl + sg: return 0.0, 0.0, 0.0
        m = s.ewm(span=f, adjust=False).mean() - s.ewm(span=sl, adjust=False).mean()
        sig = m.ewm(span=sg, adjust=False).mean()
        return _safe_float(m.iloc[-1]), _safe_float(sig.iloc[-1]), _safe_float((m - sig).iloc[-1])
    except Exception:
        return 0.0, 0.0, 0.0

def calc_bb(s, p=20, d=2):
    try:
        if s is None or len(s) < p: return 0.0, 0.0, 0.0
        m = s.rolling(p).mean(); sd = s.rolling(p).std()
        return _safe_float((m + sd * d).iloc[-1]), _safe_float(m.iloc[-1]), _safe_float((m - sd * d).iloc[-1])
    except Exception:
        return 0.0, 0.0, 0.0

def _aviso(msg):
    # Nunca levanta exceção (ex.: console sem suporte a emoji/acentos)
    try:
        print(f"[AVISO] {msg}", flush=True)
    except Exception:
        pass

def _log_falha(modelo, symbol, e):
    _aviso(f"{modelo} falhou em {symbol}: {type(e).__name__}: {e}")

def _datas_futuras(ultima_data, dias):
    return pd.date_range(start=ultima_data + pd.Timedelta(days=1), periods=dias, freq='D')

def _n_passos(ultima_data, dias, cripto):
    """Quantos passos (pregões) o modelo precisa projetar para cobrir `dias` dias corridos."""
    if cripto:
        return dias
    return max(int((_datas_futuras(ultima_data, dias).weekday < 5).sum()), 1)

def _alinhar_calendario(passos, ultima_data, dias, cripto):
    """Converte uma projeção em passos de pregão para uma série em dias corridos (len == dias)."""
    passos = np.asarray(passos, dtype=float)
    if cripto:
        return passos[:dias]
    cont = np.cumsum(_datas_futuras(ultima_data, dias).weekday < 5)
    idx = np.clip(cont - 1, 0, len(passos) - 1)
    return passos[idx]

def prever(close, symbol, dias):
    try:
        close = close.dropna()
        if len(close) < 60: return None
        pa = float(close.iloc[-1])
        res = {}
        cripto = symbol in CRIPTOS

        idx = pd.to_datetime(close.index)
        if idx.tz is not None:
            idx = idx.tz_localize(None)
        close = pd.Series(close.values, index=idx)
        ultima_data = idx[-1]
        n_passos = _n_passos(ultima_data, dias, cripto)

        # PROPHET: ajustado em log(preço), sazonalidade semanal só para cripto,
        # changepoint_range maior para enxergar viradas recentes de tendência.
        try:
            m = Prophet(daily_seasonality=False, yearly_seasonality=False,
                        weekly_seasonality=cripto,
                        changepoint_prior_scale=0.05, changepoint_range=0.9)
            m.fit(pd.DataFrame({'ds': idx, 'y': np.log(close.values)}))
            fc = m.predict(m.make_future_dataframe(periods=dias))
            b = np.exp(fc['yhat'].iloc[-dias:].values)
            a = b + (pa - b[0])
            cr = float((a[-1] / pa - 1) * 100)
            if -50 < cr < 200:
                res['Prophet'] = {'preco_final': float(a[-1]), 'crescimento': cr, 'serie': a}
        except Exception as e:
            _log_falha('Prophet', symbol, e)

        # ARIMA: projeta em passos de pregão (m=5 ações/ETFs, m=7 cripto)
        # e converte para dias corridos, alinhado com os demais modelos.
        try:
            m_sazonal = 7 if cripto else 5
            mo = pm.auto_arima(close.values, d=1, seasonal=True, m=m_sazonal,
                               stepwise=True, suppress_warnings=True, error_action="ignore",
                               max_p=3, max_q=3, max_P=2, max_Q=2)
            b = _alinhar_calendario(mo.predict(n_periods=n_passos), ultima_data, dias, cripto)
            a = b + (pa - b[0])
            cr = float((a[-1] / pa - 1) * 100)
            if -50 < cr < 200:
                res['ARIMA'] = {'preco_final': float(a[-1]), 'crescimento': cr, 'serie': a}
        except Exception as e:
            _log_falha('ARIMA', symbol, e)

        # XGBoost: features técnicas (RSI e volatilidade) + lags.
        # Ordem das colunas em X: [rsi, vol, lag_1, lag_2, lag_3, lag_4, lag_5]
        try:
            dfx = pd.DataFrame(index=close.index)
            dfx['y'] = np.log(close / close.shift(1))

            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / loss
            dfx['rsi'] = 100 - (100 / (1 + rs))
            dfx['vol'] = close.pct_change().rolling(14).std()

            for i in range(1, 6):
                dfx[f'lag_{i}'] = dfx['y'].shift(i)

            dfx = dfx.replace([np.inf, -np.inf], np.nan).dropna()
            X, y = dfx.drop('y', axis=1).values, dfx['y'].values

            mx = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
            mx.fit(X, y)

            # Última linha de features já inclui o retorno mais recente como lag_1 do próximo passo
            last = X[-1].reshape(1, -1).copy()
            last[0, 2:7] = np.r_[dfx['y'].values[-1], X[-1, 2:6]]
            preds = []
            for _ in range(n_passos):
                p = float(mx.predict(last)[0])
                preds.append(p)
                # RSI e vol ficam fixos; só desliza a janela de lags (lag_1 = p, lag_k = lag_{k-1})
                last[0, 2:7] = np.r_[p, last[0, 2:6]]

            b = _alinhar_calendario(pa * np.exp(np.cumsum(preds)), ultima_data, dias, cripto)
            a = b + (pa - b[0])
            cr = float((a[-1] / pa - 1) * 100)
            if -50 < cr < 200:
                res['XGBoost'] = {'preco_final': float(a[-1]), 'crescimento': cr, 'serie': a}
        except Exception as e:
            _log_falha('XGBoost', symbol, e)

        # HOLT-WINTERS: também em passos de pregão -> dias corridos
        try:
            mo = ExponentialSmoothing(close.values, trend='add', damped_trend=True, seasonal=None).fit()
            b = _alinhar_calendario(mo.forecast(n_passos), ultima_data, dias, cripto)
            a = b + (pa - b[0])
            cr = float((a[-1] / pa - 1) * 100)
            if -50 < cr < 200:
                res['Holt-Winters'] = {'preco_final': float(a[-1]), 'crescimento': cr, 'serie': a}
        except Exception as e:
            _log_falha('Holt-Winters', symbol, e)

        if not res: return None

        pesos = calcular_pesos_adaptativos(symbol)
        pm_, sp = 0.0, 0.0
        for n, dd in res.items():
            if n in pesos:
                pm_ += dd['preco_final'] * pesos[n]; sp += pesos[n]
        pm_ = pm_ / sp if sp > 0 else pa
        cresc = float((pm_ / pa - 1) * 100)

        # Cone de incerteza usa volatilidade dos últimos 30 dias
        vol_recente = close.pct_change().tail(30).dropna().std()
        da = np.arange(1, dias + 1)
        ls = pa * np.exp(1.96 * vol_recente * np.sqrt(da))
        li = pa * np.exp(-1.96 * vol_recente * np.sqrt(da))

        return {
            'preco_medio': pm_, 'crescimento_medio': cresc,
            'metodos': list(res.keys()), 'detalhes': res,
            'limite_superior': ls, 'limite_inferior': li, 'pesos_usados': pesos
        }
    except Exception as e:
        _log_falha('prever', symbol, e)
        return None

# Ativos descartados de propósito (dado ruim); não adianta tentar de novo no mesmo ciclo
_DESCARTADOS = set()

def _limpar_outliers(ps, cripto):
    """Remove pontos de preço claramente errados (spikes) comparando cada preço
    com a mediana móvel centrada de 11 pregões. Retorna (série limpa, qtd removida)."""
    limite = 0.5 if cripto else 0.3
    med = ps.rolling(11, center=True, min_periods=3).median()
    ok = ((ps / med) - 1).abs() <= limite
    return ps[ok], int((~ok).sum())

def processar(symbol):
    try:
        ticker = get_ticker(symbol)
        data = None
        for espera in (0, 3, 8, 20):
            if espera:
                time.sleep(espera)
            try:
                data = yf.download(ticker, period="2y", interval="1d", progress=False,
                                   auto_adjust=True, multi_level_index=False, timeout=10)
                if data is not None and not data.empty: break
            except Exception: pass
        ps = _extract_close(data)
        if ps is None or len(ps) < 100:
            _aviso(f"{symbol}: sem dados suficientes do Yahoo ({0 if ps is None else len(ps)} pregoes)")
            return None, None

        cripto = symbol in CRIPTOS
        ps = ps[ps > 0]
        ps, n_out = _limpar_outliers(ps, cripto)
        if n_out:
            _aviso(f"{symbol}: {n_out} preco(s) com spike removido(s) do historico")
        if len(ps) < 100:
            _aviso(f"{symbol}: menos de 100 pregoes validos apos limpeza")
            return None, None
        pa = float(ps.iloc[-1])
        ret = ps.pct_change().dropna()
        vol_check = _safe_float(ret.std() * np.sqrt(252) * 100)
        limite_vol = 500 if cripto else 250
        if vol_check > limite_vol:
            _aviso(f"{symbol} descartado: dado suspeito (volatilidade anual {vol_check:.0f}%, maior variacao diaria {ret.abs().max()*100:.0f}%)")
            _DESCARTADOS.add(symbol)
            return None, None
        prev = prever(ps, symbol, HORIZONTE_DIAS)
        if prev is None:
            _aviso(f"{symbol}: nenhum modelo gerou previsao valida")
            return None, None

        data_alvo = (datetime.now() + timedelta(days=HORIZONTE_DIAS)).strftime('%Y-%m-%d')
        salvar_previsoes(symbol, data_alvo, prev['detalhes'])

        rsi = calc_rsi(ps); sh = calc_sharpe(ret); so = calc_sortino(ret)
        v95, cv95 = calc_var_cvar(ret)
        mx = ps.expanding().max()
        dd = _safe_float(((mx - ps) / mx * 100).iloc[-1])
        volat = _safe_float(ret.std() * np.sqrt(252) * 100)
        macd, sig, hst = calc_macd(ps); bbs, bbm, bbi = calc_bb(ps)
        rsi_s = max(0, (100 - rsi) / 100) * 10
        sh_s = max(-5.0, min(5.0, sh)); so_s = max(-5.0, min(5.0, so))  # evita um ativo dominar o ranking
        score = (prev['crescimento_medio'] * 0.3) + (sh_s * 15) + (so_s * 10) - (dd * 0.2) + rsi_s

        if symbol in CRIPTOS: tipo = 'Cripto'
        elif symbol in INTERNACIONAIS: tipo = 'Ação Internacional'
        elif symbol in ETFS: tipo = 'ETF'
        elif symbol.endswith('11'): tipo = 'FII'
        else: tipo = 'Ação'

        row = {
            'Ativo': symbol, 'Tipo': tipo,
            'Preço Atual (R$)': safe_round(pa),
            'Previsão Média (R$)': safe_round(prev['preco_medio']),
            'Cresc. Médio (%)': safe_round(prev['crescimento_medio']),
            'Peso Prophet (%)': safe_round(prev['pesos_usados'].get('Prophet', 0) * 100, 1),
            'Peso ARIMA (%)': safe_round(prev['pesos_usados'].get('ARIMA', 0) * 100, 1),
            'Peso XGBoost (%)': safe_round(prev['pesos_usados'].get('XGBoost', 0) * 100, 1),
            'Peso Holt-Winters (%)': safe_round(prev['pesos_usados'].get('Holt-Winters', 0) * 100, 1),
            'Volatilidade Anual (%)': safe_round(volat),
            'Drawdown Atual (%)': safe_round(dd),
            'Sharpe Ratio': safe_round(sh, 3), 'Sortino Ratio': safe_round(so, 3),
            'RSI (14d)': safe_round(rsi, 1),
            'VaR 95% (1d %)': safe_round(v95 * 100), 'CVaR 95% (1d %)': safe_round(cv95 * 100),
            'MACD': safe_round(macd), 'Sinal MACD': safe_round(sig), 'Histograma MACD': safe_round(hst),
            'Banda Superior (BB)': safe_round(bbs), 'Banda Média (BB)': safe_round(bbm),
            'Banda Inferior (BB)': safe_round(bbi),
            '🎯 Score Oportunidade': safe_round(score),
        }

        hist90 = ps.iloc[-90:]
        datas_fut = pd.date_range(
            start=hist90.index[-1] + pd.Timedelta(days=1),
            periods=HORIZONTE_DIAS, freq='D'
        )
        chart = {
            'hist_dates': [d.strftime('%Y-%m-%d') for d in hist90.index],
            'hist_prices': [float(x) for x in hist90.to_numpy()],
            'proj_dates': [d.strftime('%Y-%m-%d') for d in datas_fut],
            'ensemble': [float(x) for x in prev['preco_medio'] * np.ones(HORIZONTE_DIAS)],
            'upper': [float(x) for x in prev['limite_superior'][:HORIZONTE_DIAS]],
            'lower': [float(x) for x in prev['limite_inferior'][:HORIZONTE_DIAS]],
            'projections': {n: [float(x) for x in d['serie'][:HORIZONTE_DIAS]]
                            for n, d in prev['detalhes'].items()},
            'weights': prev['pesos_usados'],
            'preco_atual': float(pa),
            'preco_medio': float(prev['preco_medio']),
            'crescimento_medio': float(prev['crescimento_medio']),
        }
        return row, chart
    except Exception:
        return None, None


ATIVOS = [
    'PETR4','ITUB4','VALE3','BBDC4','B3SA3','BBAS3','BBDC3','ITSA4','BPAC11','SANB11',
    'WEGE3','EMBJ3','RADL3','VIVT3','TOTS3','ABEV3','SBSP3','GGBR4','CSMG3',
    'AXIA3','ENEV3','MOTV3','DIRR3','TEND3','ALUP11','JBSS3','TTEN3','PNVL3','SMFT3',
    'RDOR3','MATD3','CYRE3','RENT3','TIMS3','ELET3','ELET6','CMIG4','CSNA3','BRFS3',
    'LREN3','MGLU3','AZZA3','COGN3','SUZB3','KLBN11','RAIL3','EQTL3',
    'PRIO3','RECV3','CPLE6','UGPA3','CSAN3','HAPV3','FLRY3','QUAL3','HYPE3',
    'MULT3','VAMO3','PSSA3',
    'BTLG11','KNCR11','HGCR11','KNHY11','KNIP11','TRXF11','PVBI11','VILG11','XPML11','HGRU11',
    'KNRI11','BRCO11','MCCI11','JSRE11','RZTR11','HGLG11','XPLG11','VISC11','BCFF11','CPTS11',
    'MXRF11','IRDM11','RECR11','GGRC11','ALZR11',
    'BOVA11','IBOB11','IVVB11','SMAL11','PIBB11','LFTX11','XB3011','XB3511','BNDX11','USDB11',
    'FIND11','MATB11','DOLA11','GOLD11','ECOO11',
    'BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD',
    'AVAX-USD','DOT-USD','LINK-USD','LTC-USD','SHIB-USD',
    'AAPL','MSFT','GOOGL','AMZN','TSLA','NVDA','META','BRK-B','JPM','V',
    'JNJ','WMT','SPY','QQQ'
]
ATIVOS = list(dict.fromkeys(ATIVOS))


def ciclo_completo(stop_event):
    inicio = datetime.now().isoformat(timespec='seconds')
    set_status(running=1, progress=0, total=len(ATIVOS), current_asset='',
               last_start=inicio, message='Iniciando ciclo...')

    set_status(message='Conferindo previsões passadas...')
    try:
        conf, fal, tot = atualizar_previsoes_passadas(
            progresso_cb=lambda msg: set_status(message=msg)
        )
        print(f"🔄 Feedback: {conf} conferidas, {fal} falhas, {tot} pendentes")
    except Exception as e:
        print(f"⚠️ Erro no feedback: {e}")

    resultados, charts, sem_resultado = [], {}, []
    _DESCARTADOS.clear()
    for i, sym in enumerate(ATIVOS):
        if stop_event.is_set():
            set_status(message='Interrompido pelo usuário')
            return
        set_status(current_asset=sym, progress=i + 1,
                   message=f'Analisando {sym} ({i+1}/{len(ATIVOS)})')
        row, chart = processar(sym)
        if row:
            resultados.append(row)
            if chart:
                charts[sym] = chart
        else:
            sem_resultado.append(sym)
        time.sleep(1.0)

    # Segunda tentativa: ativos que falharam por limite/instabilidade do Yahoo
    repetir = [s_ for s_ in sem_resultado if s_ not in _DESCARTADOS]
    if repetir and not stop_event.is_set():
        set_status(current_asset='', message=f'Aguardando 30s para repetir {len(repetir)} ativos que falharam...')
        time.sleep(30)
        for sym in repetir:
            if stop_event.is_set():
                break
            set_status(current_asset=sym, message=f'Reprocessando {sym}')
            row, chart = processar(sym)
            if row:
                resultados.append(row)
                sem_resultado.remove(sym)
                if chart:
                    charts[sym] = chart
            time.sleep(1.0)

    if sem_resultado:
        _aviso(f"{len(sem_resultado)} ativos sem resultado neste ciclo: {', '.join(sem_resultado)}")

    cache = {
        'run_at': datetime.now().isoformat(timespec='seconds'),
        'horizonte_dias': HORIZONTE_DIAS,
        'results': sorted(resultados, key=lambda x: -x['🎯 Score Oportunidade']),
        'charts': charts,
    }
    tmp = CACHE_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, default=str)
    Path(tmp).replace(CACHE_FILE)

    fim = datetime.now().isoformat(timespec='seconds')
    proximo = (datetime.now() + timedelta(hours=INTERVALO_HORAS)).isoformat(timespec='seconds')
    set_status(running=0, progress=len(ATIVOS), current_asset='',
               last_end=fim, next_run=proximo,
               message=f'Ciclo concluído: {len(resultados)} ativos')
    print(f"✅ Ciclo concluído: {len(resultados)} ativos processados")


def rodar_worker(stop_event, run_now_event):
    _aviso("worker iniciado - versao v5 (filtro de volatilidade > 500% ativo)")
    init_db()
    from config import RODAR_AO_INICIAR
    if RODAR_AO_INICIAR:
        ciclo_completo(stop_event)
    while not stop_event.is_set():
        proximo = (datetime.now() + timedelta(hours=INTERVALO_HORAS)).isoformat(timespec='seconds')
        set_status(next_run=proximo, message=f'Aguardando próximo ciclo (a cada {INTERVALO_HORAS}h)')
        if run_now_event.wait(timeout=INTERVALO_HORAS * 3600):
            run_now_event.clear()
            if stop_event.is_set():
                break
            print("▶️  Ciclo manual solicitado")
        if not stop_event.is_set():
            ciclo_completo(stop_event)
