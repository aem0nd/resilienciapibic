import pandas as pd
df = pd.read_excel('dpmu2.xlsx')

mdpp1 = float(3)
mdpp2 = float(4)
mdpp3 = float(2)
mdpp4 = float(3)
mdpb1 = float(7.5)
mdpb2 = float(12.5)
mdpb3 = float(18)
mdpb4 = float(23)

valores1 = []
for linha in df.itertuples():
    if linha.distancia == 0:
        valores1.append('mesma ra')
    else:
        if linha.modoagregado1 == 'TA':
            if linha.modoagregado2 == 'TA_aPe':
                valores1.append('persistent' if linha.distancia <= mdpp1 else 'exceptional')
            else:
                valores1.append('persistent' if linha.distancia <= mdpb1 else 'exceptional')
        else:
            valores1.append('adptable' if linha.distancia <= mdpb1 else 'transformable')
df['cenario1'] = valores1

valores2 = []
for linha in df.itertuples():
    if linha.distancia == 0:
        valores2.append('mesma ra')
    else:
        if linha.modoagregado1 == 'TA':
            if linha.modoagregado2 == 'TA_aPe':
                valores2.append('persistent' if linha.distancia <= mdpp2 else 'exceptional')
            else:
                valores2.append('persistent' if linha.distancia <= mdpb2 else 'exceptional')
        else:
            valores2.append('adptable' if linha.distancia <= mdpb2 else 'transformable')
df['cenario2'] = valores2

valores3 = []
for linha in df.itertuples():
    if linha.distancia == 0:
        valores3.append('mesma ra')
    else:
        if linha.modoagregado1 == 'TA':
            if linha.modoagregado2 == 'TA_aPe':
                valores3.append('persistent' if linha.distancia <= mdpp3 else 'exceptional')
            else:
                valores3.append('persistent' if linha.distancia <= mdpb3 else 'exceptional')
        else:
            valores3.append('adptable' if linha.distancia <= mdpb3 else 'transformable')
df['cenario3'] = valores3

valores4 = []
for linha in df.itertuples():
    if linha.distancia == 0:
        valores4.append('mesma ra')
    else:
        if linha.modoagregado1 == 'TA':
            if linha.modoagregado2 == 'TA_aPe':
                valores4.append('persistent' if linha.distancia <= mdpp4 else 'exceptional')
            else:
                valores4.append('persistent' if linha.distancia <= mdpb4 else 'exceptional')
        else:
            valores4.append('adptable' if linha.distancia <= mdpb4 else 'transformable')
df['cenario4'] = valores4

df.to_excel('dpmures.xlsx')
