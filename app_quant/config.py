import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE       = os.path.join(BASE_DIR, 'previsoes_historico.db')
CACHE_FILE    = os.path.join(BASE_DIR, 'cache_resultados.json')

HORIZONTE_DIAS     = 30
INTERVALO_HORAS    = 24
RODAR_AO_INICIAR   = True

HOST = '0.0.0.0'
PORT = 5000