from selenium import webdriver

def configurar_driver():
    driver = webdriver.Chrome()
    return driver

def obter_url():
    return 'https://www.amazon.com.br/hz/wishlist/ls/2FJRI71SN2K0L?ref_=wl_share'  
