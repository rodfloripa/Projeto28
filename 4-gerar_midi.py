import numpy as np
import tensorflow as tf
from mido import Message, MidiFile, MidiTrack
import random
import pretty_midi
import re

# 1. MESMA LOGICA DE LIMPEZA DO TREINO (Obrigatório)
def super_simplificador(linha):
    if "FILE" in linha or not linha.strip(): return None
    # Volume: 4 níveis
    def simplificar_v(m):
        v = int(m.group(1))
        if v == 0: return "V0"
        if v < 45: return "V40"
        if v < 85: return "V80"
        return "V120"
    linha = re.sub(r'V(\d+)', simplificar_v, linha)
    # Tempo: Múltiplos de 0.05
    def simplificar_t(m):
        t = float(m.group(1))
        t_arredondado = round(t * 20) / 20
        return f"T{t_arredondado:.2f}"
    linha = re.sub(r'T(\d+\.\d+)', simplificar_t, linha)
    return linha

# 2. CARREGAR E RECONSTRUIR VOCABULÁRIO LIMPO
MODEL_NAME = 'modelo_musical.h5'
model = tf.keras.models.load_model(MODEL_NAME)

with open("resultado_midi_instrumentos.txt", "r") as f:
    linhas_brutas = f.read().splitlines()

# Criar a lista de dados usando a limpeza agressiva
dados_limpos = []
for l in linhas_brutas:
    s = super_simplificador(l)
    if s: dados_limpos.append(s)

tokens = sorted(list(set(dados_limpos)))
token_to_int = {t: i for i, t in enumerate(tokens)}
int_to_token = {i: t for i, t in enumerate(tokens)}
n_vocab = len(tokens)

print(f"Vocabulário reconstruído: {n_vocab} tokens. (Deve ser próximo de 4005)")

# 3. FUNÇÃO DE GERAÇÃO
def gerar_musica(modelo, seed_seq, tamanho=300, temperatura=1.1):
    gerado = []
    pad_input = list(seed_seq)
    
    for i in range(tamanho):
        X_input = np.array([pad_input])
        predicoes = modelo.predict(X_input, verbose=0)[0]
        
        # Temperatura para criatividade
        predicoes = np.log(predicoes + 1e-8) / temperatura
        exp_preds = np.exp(predicoes)
        predicoes = exp_preds / np.sum(exp_preds)
        
        proximo_id = np.random.choice(range(n_vocab), p=predicoes)
        gerado.append(int_to_token[proximo_id])
        
        pad_input.append(proximo_id)
        pad_input = pad_input[1:]
    return gerado

# 4. CONVERSOR PARA MIDI
from mido import bpm2tempo

import re
import pretty_midi
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

def texto_para_midi(lista_texto, nome_saida="musica_lenta.mid", multiplicador_lentidao=2.0):
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)
    
    # 1. Definir o BPM (Ex: 60 é um tempo bem lento, estilo balada)
    bpm = 60 
    # USAMOS MetaMessage para o tempo, não Message comum
    track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))
    
    for item in lista_texto:
        try:
            partes = item.split('_')
            tipo = partes[0]
            nota_nome = partes[2]
            
            # Extração de números usando Regex
            vel = int(re.findall(r'\d+', partes[3])[0])
            tempo_val = float(re.findall(r'\d+\.\d+|\d+', partes[4])[0])
            
            nota_num = pretty_midi.note_name_to_number(nota_nome)
            
            # Cálculo dos ticks com o multiplicador de lentidão
            # Aumentar esse número estica o tempo entre as notas
            ticks = int(tempo_val * 480 * multiplicador_lentidao)
            
            msg_tipo = 'note_on' if tipo == "ON" else 'note_off'
            track.append(Message(msg_tipo, note=nota_num, velocity=vel, time=ticks))
        except Exception as e:
            continue
            
    midi.save(nome_saida)
    print(f"Sucesso! Arquivo lento '{nome_saida}' gerado.")

# Para rodar:
# texto_para_midi(musica_texto, "resultado_final_lento.mid", multiplicador_lentidao=2.0)

# Exemplo de uso:
# texto_para_midi(musica_texto, "musica_bem_lenta.mid", multiplicador_lentidao=2.5)

# --- EXECUTAR ---
SEQ_LENGTH = 25 
start_idx = random.randint(0, len(dados_limpos) - SEQ_LENGTH)
seed = [token_to_int[t] for t in dados_limpos[start_idx : start_idx + SEQ_LENGTH]]

print("IA compondo...")
musica_texto = gerar_musica(model, seed, tamanho=150, temperatura=0.9)
texto_para_midi(musica_texto)
