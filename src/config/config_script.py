from selenium import webdriver

def configurar_driver():
    driver = webdriver.Chrome()
    return driver

url = 'https://www.amazon.com.br/hz/wishlist/ls/2FJRI71SN2K0L?ref_=wl_share'  #url da wishlist
