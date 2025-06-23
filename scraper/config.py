from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def configurar_driver():
    """Configura e retorna uma instância do Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver