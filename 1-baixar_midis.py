!pip install requests beautifulsoup4 --quiet
import os
import requests
from bs4 import BeautifulSoup
import time
import re

def baixar_de_tinyurl(url_tiny, caminho_destino):
    """Segue o redirecionamento do TinyURL e baixa o arquivo."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        # 1. Segue o redirecionamento para ver onde o TinyURL vai dar
        resposta_apoio = requests.get(url_tiny, headers=headers, allow_redirects=True, timeout=15)
        url_final = resposta_apoio.url
        
        # 2. Se cair no Google Drive, usamos a lógica de download direto
        if 'drive.google.com' in url_final:
            file_id = ""
            patterns = [r'id=([a-zA-Z0-9_-]+)', r'd/([a-zA-Z0-9_-]+)']
            for p in patterns:
                match = re.search(p, url_final)
                if match:
                    file_id = match.group(1)
                    break
            
            if file_id:
                direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
                r_direct = requests.get(direct_url, stream=True)
                with open(caminho_destino, 'wb') as f:
                    for chunk in r_direct.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        
        # 3. Se for um link direto para .mid
        elif url_final.endswith('.mid'):
            with open(caminho_destino, 'wb') as f:
                f.write(resposta_apoio.content)
            return True
            
    except Exception as e:
        print(f"      Erro no TinyURL: {e}")
    return False

def scraper_final_tinyurl(url_base, limite=100):
    pasta = "midis_baixados"
    if not os.path.exists(pasta): os.makedirs(pasta)
    headers = {"User-Agent": "Mozilla/5.0"}
    contador = 0
    url_atual = url_base

    while contador < limite:
        res = requests.get(url_atual, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        links_posts = [a['href'] for a in soup.select('h3.post-title a')]

        for post_url in links_posts:
            if contador >= limite: break
            
            print(f"Analisando Post: {post_url.split('/')[-1]}")
            res_post = requests.get(post_url, headers=headers)
            soup_post = BeautifulSoup(res_post.text, 'html.parser')
            
            # Procura por links que contenham 'tinyurl.com'
            links_tiny = [a['href'] for a in soup_post.find_all('a', href=True) if 'tinyurl.com' in a['href']]
            
            for link in links_tiny:
                nome_arquivo = re.sub(r'\W+', '', post_url.split('/')[-1])[:40] + ".mid"
                caminho = os.path.join(pasta, nome_arquivo)
                
                print(f"   [Encontrado] TinyURL: {link}")
                if baixar_de_tinyurl(link, caminho):
                    print(f"   [OK] Arquivo salvo: {nome_arquivo}")
                    contador += 1
                    break 
            
            time.sleep(1)

        # Paginação para próxima página do blog
        proxima = soup.select_one('a.blog-pager-older-link')
        if proxima: url_atual = proxima['href']
        else: break

    print(f"\nConcluído! {contador} arquivos na pasta '{pasta}'")

# Executar
scraper_final_tinyurl("https://www.freepianotutorials.net")
