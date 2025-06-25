from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .config import configurar_driver 

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
def executar_scraping(url: str):
    """
    Função principal que orquestra o scraping.
    Abre a URL, verifica se a lista existe e extrai os dados.
    """
    driver = None
    try:
        driver = configurar_driver()
        driver.get(url)
        
        time.sleep(2)

        try:
            # Tentando encontrar um elemento que só existe na página de erro da Amazon.
            erro_h1 = driver.find_element(By.CSS_SELECTOR, "h1.a-spacing-base")
            if "não encontrada" in erro_h1.text or "not found" in erro_h1.text.lower():
                return {
                    "error": "A lista de desejos não foi encontrada ou é privada.", 
                    "error_code": "WISHLIST_NOT_FOUND"
                }
        except NoSuchElementException:
            # Se não encontrou o elemento de erro, significa que a página é válida.
            pass
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        nome_lista = extrair_nome_lista(soup)
        itens = extrair_itens_lista(soup)
        
        # Se o nome não foi encontrado e não tem itens provavelmente é uma lista privada ou vazia
        if nome_lista == 'Nome não encontrado' and not itens:
             return {
                "error": "A lista de desejos pode estar vazia, ser privada ou não foi possível carregá-la corretamente.", 
                "error_code": "WISHLIST_EMPTY_OR_PRIVATE"
            }

        return {
            "nome_da_lista": nome_lista,
            "total_itens_encontrados": len(itens),
            "itens": itens
        }
    except Exception as e:
        return {"error": f"Ocorreu um erro durante o scraping: {str(e)}"}
    finally:
        if driver:
            driver.quit()