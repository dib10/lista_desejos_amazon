from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # não preciso interagir com cliques
    driver = webdriver.Chrome(options=chrome_options)

    return driver

    

url = 'https://www.amazon.com.br/hz/wishlist/ls/2FJRI71SN2K0L?ref_=wl_share'  #url da wishlist


