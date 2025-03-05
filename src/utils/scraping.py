from bs4 import BeautifulSoup
from datetime import datetime
import re

def extrair_nome_lista(soup):
    nome_lista = soup.find('span', {'id': 'profile-list-name'})
    return nome_lista.text if nome_lista else 'Nome não encontrado'

def extrair_itens_lista(soup):
    itens = soup.find_all('li', {'class': 'g-item-sortable'})
    data_extracao = obter_data_extracao()
    return [extrair_dados_itens(item, data_extracao) for item in itens]
    
def obter_data_extracao():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extrair_codigo_asin(link):
    padrao = r"/[dg]p/([A-Z0-9]{10})(/|$|\?)"
    match = re.search(padrao, link)

    if match:
        asin = match.group(1).upper()
        return asin
    return None


def extrair_dados_itens(item, data_extracao):
    dados_item = {}
    dados_item['nome'] = item.find('a', {'class': 'a-link-normal'}).get('title', 'Nome não encontrado')
    dados_item['link'] = f"https://www.amazon.com.br{item.find('a', {'class': 'a-link-normal'}).get('href', '')}"
    dados_item['imagem'] = item.find('img').get('src', 'Imagem não encontrada') if item.find('img') else 'Imagem não encontrada'
    dados_item['asin'] = extrair_codigo_asin(dados_item['link'])
    
    #Essa conversão é para Amazon Brasileira. A amazon não permite misturar wishlist brasileira com a  estadunidense por exemplo, ou seja, o produto disponível em sua wishlist BR obrigatoriamente vem  convertido em BRL. Esse  tratamento abaixo visa resolver o problema da vírgula e ponto em formatos numéricos brasileiros.

    elemento_preco = item.find('span', {'class': 'a-price'})
    if elemento_preco:
        preco_texto = elemento_preco.find('span', {'aria-hidden': 'true'}).text.strip()
        preco_limpo = re.sub(r"[^\d,]", "",preco_texto)
        preco_float = float(preco_limpo.replace(",",".") if preco_limpo else None)
    else:
        preco_float = None
    dados_item['preco'] = preco_float

    dados_item['data_extracao'] = data_extracao
    return dados_item

import json






