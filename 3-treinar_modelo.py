import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Embedding, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
import re

# 1. PROCESSADOR ULTRA-AGRESSIVO (Reduzir 26k para ~1k tokens)
def super_simplificador(linha):
    if "FILE" in linha or not linha.strip(): return None
    
    # 1. Volume: Apenas 4 níveis (Silêncio, Baixo, Médio, Forte)
    # Isso agrupa milhares de notas que só mudavam de volume
    def simplificar_v(m):
        v = int(m.group(1))
        if v == 0: return "V0"
        if v < 45: return "V40"
        if v < 85: return "V80"
        return "V120"
    linha = re.sub(r'V(\d+)', simplificar_v, linha)
    
    # 2. Tempo: Arredondar para múltiplos de 0.05 (Quantização)
    # Transforma T0.1123, T0.1189, T0.1201 tudo em T0.1
    def simplificar_t(m):
        t = float(m.group(1))
        t_arredondado = round(t * 20) / 20 # Múltiplos de 0.05
        return f"T{t_arredondado:.2f}"
    linha = re.sub(r'T(\d+\.\d+)', simplificar_t, linha)
    
    return linha

print("Limpando dados agressivamente...")
with open("resultado_midi_instrumentos.txt", "r") as f:
    linhas_brutas = f.read().splitlines()

# Filtra e simplifica
dados_limpos = []
for l in linhas_brutas:
    s = super_simplificador(l)
    if s: dados_limpos.append(s)

tokens = sorted(list(set(dados_limpos)))
token_to_int = {t: i for i, t in enumerate(tokens)}
n_vocab = len(tokens)
print(f"SUCESSO! Vocabulário reduzido de 26k para: {n_vocab} tokens.")

# 2. SEQUENCIAMENTO (Janela curta para evitar decoreba)
seq_length = 25 
X_list, y_list = [], []
for i in range(0, len(dados_limpos) - seq_length):
    X_list.append([token_to_int[t] for t in dados_limpos[i:i + seq_length]])
    y_list.append(token_to_int[dados_limpos[i + seq_length]])

X = np.array(X_list)
y = np.array(y_list)

# 3. MODELO PEQUENO (Modelo grande decora mais fácil)
model = Sequential([
    Embedding(n_vocab, 64, input_length=seq_length),
    LSTM(256, return_sequences=True),
    Dropout(0.5),
    LSTM(256),
    BatchNormalization(),
    Dropout(0.5),
    Dense(n_vocab, activation='softmax')
])

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# 4. TREINO COM PARADA RÁPIDA
# Se a validação não melhorar em 2 épocas, paramos (evita viciar)
early_stop = EarlyStopping(monitor='val_loss', patience=2, restore_best_weights=True)
checkpoint = ModelCheckpoint('modelo_musical.h5', monitor='val_loss', save_best_only=True)

print("Iniciando treino de generalização...")
history = model.fit(X, y, epochs=15, batch_size=128, validation_split=0.2, shuffle=True, callbacks=[early_stop, checkpoint])


