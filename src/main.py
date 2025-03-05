from config.config_script import configurar_driver, url
from utils.scraping import *
import time

# Inicialização
inicio_script = time.time()
driver = configurar_driver() 

try:
    driver.get(url)
    
    if driver.title:  #se captar o título da página = sucesso
        print(f'Sucesso ao acessar: {driver.title}')
    else:
        print(f'Erro ao acessar.')

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    nome_lista_desejos = extrair_nome_lista(soup)


    # Processamento dos itens
    itens_lista = extrair_itens_lista(soup)
    if itens_lista:
        print(f'Itens encontrados na lista: {len(itens_lista)}\n')
        for item in itens_lista:
            for chave, valor in item.items():
                print(f'{chave.capitalize()}: {valor}')
            print(f'----------')
           
finally:
    driver.quit()
    print(f'\nTempo total do script: {time.time() - inicio_script:.2f} segundos')
    print()