from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import re
#=======================================
# FUNÇÕES AUXILIARES DE EXTRAÇÃO
#=======================================

def extrair_nome_lista(soup):
    """Extrai o nome da lista de desejos da página."""
    nome_lista_desejos = soup.find('span', {'id': 'profile-list-name'})
    return nome_lista_desejos.text.strip() if nome_lista_desejos else 'Nome não encontrado'

def extrair_codigo_asin(link):
    """Extrai o código ASIN de um link de produto da Amazon."""
    padrao = r"/[dg]p/([A-Z0-9]{10})(/|$|\?)"
    match = re.search(padrao, link)
    return match.group(1).upper() if match else None

def extrair_dados_itens(item_soup, data_extracao):
    """Extrai os dados de um único item da lista."""
    try:
        dados_item = {}
        link_element = item_soup.find('a', {'class': 'a-link-normal'})
        
        # Garante que encontrou o link antes de prosseguir
        if not link_element:
            return None

        dados_item['nome'] = link_element.get('title', 'Nome não encontrado')
        dados_item['link'] = f"https://www.amazon.com.br{link_element.get('href', '')}"
        
        img_element = item_soup.find('img')
        dados_item['imagem'] = img_element.get('src', 'Imagem não encontrada') if img_element else 'Imagem não encontrada'
        
        dados_item['asin'] = extrair_codigo_asin(dados_item['link'])

        elemento_preco = item_soup.find('span', {'class': 'a-price'})
        preco_float = None
        if elemento_preco:
            preco_span = elemento_preco.find('span', {'aria-hidden': 'true'})
            if preco_span:
                preco_texto = preco_span.text.strip()
                # Limpa o preço para extrair apenas dígitos e a vírgula decimal
                preco_limpo = re.sub(r"[^\d,]", "", preco_texto)
                if preco_limpo:
                    preco_float = float(preco_limpo.replace(",", "."))
        
        dados_item['preco'] = preco_float
        dados_item['data_extracao'] = data_extracao
        return dados_item
    except (AttributeError, TypeError):
        # Ignora o item se algum atributo essencial não for encontrado
        return None

def extrair_itens_lista(soup):
    """Extrai todos os itens de uma lista de desejos."""
    itens_html = soup.find_all('li', {'class': 'g-item-sortable'})
    data_extracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lista_processada = []
    for item in itens_html:
        dados_item = extrair_dados_itens(item, data_extracao)
        if dados_item is not None:
            lista_processada.append(dados_item)
            
    return lista_processada

#=======================================
# FUNÇÃO PRINCIPAL 
#=======================================
def executar_scraping(url: str) -> dict:
    """
    Inicia o driver, raspa os dados da URL e fecha o driver.
    Garante que cada execução seja isolada.
    """
    driver = None  
    try:
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "profile-list-name"))
        )
        
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')

        nome_da_lista_tag = soup.find('span', {'id': 'profile-list-name'})
        if not nome_da_lista_tag:
            return {"error": "Nome da wishlist não encontrado. A página pode ter mudado ou a lista é privada.", "error_code": "WISHLIST_NOT_FOUND"}

        nome_da_lista = nome_da_lista_tag.get_text(strip=True)
        itens_raspados = extrair_dados_itens(soup)

        return {
            "nome_da_lista": nome_da_lista,
            "itens": itens_raspados
        }

    except Exception as e:
        return {"error": f"Ocorreu um erro durante o scraping: {str(e)}", "error_code": "SCRAPING_ERROR"}

    finally:
        if driver:
            driver.quit()  