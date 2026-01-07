import random
import re
import os
import pretty_midi

class ModeloMarkovMusicalV2:
    def __init__(self):
        # O dicionário agora mapeia uma TUPLA (nota1, nota2) para a próxima nota
        self.modelo = {}
        self.notas_iniciais = []

    def treinar_do_arquivo(self, caminho_txt):
        if not os.path.exists(caminho_txt):
            print(f"Erro: Arquivo {caminho_txt} não encontrado.")
            return

        with open(caminho_txt, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        # Regex para capturar Nota(Tempo s) ou [Acorde](Tempo s)
        padrao = r'(\[?[A-G][#b]?\d(?:,[A-G][#b]?\d)*\]?\([\d.]+s\))'
        
        # Processamos o arquivo linha por linha para manter a lógica das frases
        linhas = conteudo.split('\n')
        
        for linha in linhas:
            notas = re.findall(padrao, linha)
            if len(notas) < 3: # Precisamos de pelo menos 3 notas para 2ª ordem
                continue
            
            # Guardamos o início das frases para começar a geração de forma natural
            self.notas_iniciais.append((notas[0], notas[1]))

            for i in range(len(notas) - 2):
                estado_atual = (notas[i], notas[i+1])
                proxima_nota = notas[i+2]
                
                if estado_atual not in self.modelo:
                    self.modelo[estado_atual] = []
                self.modelo[estado_atual].append(proxima_nota)
        
        print(f"Treino concluído! Estados de 2ª ordem aprendidos: {len(self.modelo)}")

    def gerar_musica(self, num_notas=60):
        if not self.modelo:
            return "Erro: Modelo não treinado."

        # Começa com um par de notas que existia no início de alguma frase do treino
        atual = random.choice(self.notas_iniciais)
        resultado = [atual[0], atual[1]]

        for _ in range(num_notas - 2):
            if atual in self.modelo:
                proxima = random.choice(self.modelo[atual])
                resultado.append(proxima)
                # O novo estado é a última nota do par anterior + a nova nota
                atual = (atual[1], proxima)
            else:
                # Se travar, escolhe um novo par aleatório para continuar
                atual = random.choice(list(self.modelo.keys()))
                resultado.extend([atual[0], atual[1]])
        
        return " ".join(resultado)

def exportar_midi(texto_musical, nome_arquivo="markov_v2.mid"):
    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0)
    tempo_atual = 0.0
    
    # Extração de Nota e Duração
    matches = re.findall(r'(\[?[\w#,]+\]?)\(([\d.]+)s\)', texto_musical)
    
    for nota_acorde, duracao in matches:
        try:
            notas = nota_acorde.replace('[','').replace(']','').split(',')
            d = float(duracao)
            for n in notas:
                p = pretty_midi.note_name_to_number(n)
                piano.notes.append(pretty_midi.Note(velocity=85, pitch=p, start=tempo_atual, end=tempo_atual + d))
            tempo_atual += d
        except:
            continue

    if piano.notes:
        midi.instruments.append(piano)
        midi.write(nome_arquivo)
        print(f"--- MIDI GERADO COM SUCESSO ---")
        print(f"Arquivo: {nome_arquivo} | Total de Notas: {len(piano.notes)}")
    else:
        print("Erro ao converter notas para MIDI.")

# --- EXECUÇÃO ---

# 1. Instanciar e Treinar
markov_v2 = ModeloMarkovMusicalV2()
markov_v2.treinar_do_arquivo("treinar_midi.txt")

# 2. Gerar Sequência (ex: 100 notas)
musica_texto = markov_v2.gerar_musica(100)
print("\nPrimeiras notas geradas:")
print(musica_texto[:200] + "...")

# 3. Salvar o arquivo
exportar_midi(musica_texto)
