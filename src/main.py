from config.config_script import configurar_driver, obter_url
from utils.scraping import *
import time


inicio_script = time.time()
driver = configurar_driver() 
url = obter_url()           
try:
    driver.get(url)
    
   
    if driver.title:  #se captar o título da página = sucesso
        print(f'Sucesso ao acessar: {driver.title}')
    else:
        print(f'Erro ao acessar.')

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extração do nome da lista
    nome_lista = soup.find('span', {'id': 'profile-list-name'})
    if nome_lista:
        print(f'Lista: "{nome_lista.text}" carregada com sucesso!')
    else:
        print(f'Nome da lista de compras não encontrada')

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