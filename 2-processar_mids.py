!pip install mido
import mido
import os
import glob
from mido import MidiFile, MidiTrack, Message


def midi_com_instrumentos_para_txt(caminho_pasta, arquivo_saida="resultado_midi_instrumentos.txt"):
    arquivos = glob.glob(os.path.join(caminho_pasta, "*.mid")) + \
               glob.glob(os.path.join(caminho_pasta, "*.midi"))
    
    full_output = []
    
    def msg_to_note_name(n):
        nomes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return f"{nomes[n % 12]}{(n // 12) - 1}"

    print(f"Processando {len(arquivos)} arquivos com instrumentos...")

    for arquivo in arquivos:
        try:
            mid = MidiFile(arquivo)
            # Dicionário para rastrear qual instrumento está em cada canal
            # Padrão MIDI: Canal 9 (index 10) é sempre percussão (instrumento 128 aqui)
            canais_instrumentos = {i: 0 for i in range(16)} 
            canais_instrumentos[9] = 128 

            full_output.append(f"START_FILE_{os.path.basename(arquivo)}")
            
            for msg in mid:
                tempo = msg.time
                
                # Rastrear troca de instrumentos (Program Change)
                if msg.type == 'program_change':
                    canais_instrumentos[msg.channel] = msg.program
                
                # Registrar Notas
                if msg.type in ['note_on', 'note_off']:
                    tipo = "ON" if (msg.type == 'note_on' and msg.velocity > 0) else "OFF"
                    inst_id = canais_instrumentos[msg.channel]
                    nome_n = msg_to_note_name(msg.note)
                    
                    # NOVO FORMATO: TIPO | INSTRUMENTO | NOTA | VELOCIDADE | DELTA_TEMPO
                    # Ex: ON_I0_D2_V110_T0.01 (I0 = Piano, I40 = Violino)
                    full_output.append(f"{tipo}_I{inst_id}_{nome_n}_V{msg.velocity}_T{tempo}")
                
                elif tempo > 0:
                    full_output.append(f"TIME_{tempo}")

            full_output.append(f"END_FILE")
            print(f"✓ {os.path.basename(arquivo)} ok.")

        except Exception as e:
            print(f"X Erro em {arquivo}: {e}")

    with open(arquivo_saida, "w", encoding='utf-8') as f:
        f.write("\n".join(full_output))
    
    print(f"\nConcluído! Arquivo gerado: {arquivo_saida}")

# Executar
midi_com_instrumentos_para_txt("midis_baixados")





def converter_txt_multi_instrumentos(arquivo_txt, lista_ids, nome_saida="multi_instrumentos.mid"):
    mid = MidiFile()
    # Criamos uma trilha para cada instrumento para manter o som organizado
    trilhas = {}
    
    def name_to_midi_num(name):
        nomes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        if "#" in name:
            n, o = name[:2], name[2:]
        else:
            n, o = name[0], name[1:]
        return (int(o) + 1) * 12 + nomes.index(n)

    print(f"A extrair os instrumentos: {lista_ids}...")
    
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    # Dicionário para controlar o tempo individual de cada trilha
    tempo_nas_trilhas = {id_inst: 0 for id_inst in lista_ids}
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or "FILE" in linha: continue
            
        partes = linha.split('_')
        
        # 1. PROCESSAMENTO DE TEMPO (Avança o relógio para todas as trilhas escolhidas)
        if partes[0] == "TIME":
            ticks = int(mido.second2tick(float(partes[1]), mid.ticks_per_beat, 500000))
            for id_inst in lista_ids:
                tempo_nas_trilhas[id_inst] += ticks
            continue
            
        # 2. PROCESSAMENTO DE NOTAS
        try:
            tipo = partes[0]
            inst_id = int(partes[1][1:])
            nota_nome = partes[2]
            vel = int(partes[3][1:])
            t_msg_ticks = int(mido.second2tick(float(partes[4][1:]), mid.ticks_per_beat, 500000))
            
            # Se o instrumento atual for um dos que escolheste
            if inst_id in lista_ids:
                # Se a trilha para este instrumento ainda não existir, cria-a
                if inst_id not in trilhas:
                    t = MidiTrack()
                    mid.tracks.append(t)
                    t.append(Message('program_change', program=inst_id, time=0))
                    trilhas[inst_id] = t
                
                nota_num = name_to_midi_num(nota_nome)
                msg_tipo = 'note_on' if tipo == "ON" else 'note_off'
                
                # O tempo da mensagem é o tempo acumulado na trilha + o tempo da própria nota
                tempo_total = tempo_nas_trilhas[inst_id] + t_msg_ticks
                
                trilhas[inst_id].append(Message(msg_tipo, note=nota_num, velocity=vel, time=tempo_total))
                
                # Resetamos o acumulador de tempo desta trilha específica
                tempo_nas_trilhas[inst_id] = 0
            else:
                # Se for um instrumento que NÃO queres, apenas somamos o tempo dele ao relógio
                for id_inst in lista_ids:
                    tempo_nas_trilhas[id_inst] += t_msg_ticks
                    
        except: continue

    mid.save(nome_saida)
    print(f"✓ Ficheiro '{nome_saida}' gerado com sucesso!")

# --- CONFIGURAÇÃO ---
# Exemplo: 0 (Piano), 40 (Violino), 56 (Trompete)
meus_instrumentos = [0] 
converter_txt_multi_instrumentos("resultado_midi_instrumentos.txt", meus_instrumentos)




