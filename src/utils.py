from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import gzip
import ndjson

def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('chromedriver',chrome_options=chrome_options)
    return driver

def store_data(restaurant_data):
        with gzip.open(f"data/restaurant_data.ndjson.gz", "wt", encoding="utf-8") as f:
            writer = ndjson.writer(f)
            while not restaurant_data.empty():
                data = restaurant_data.get()
                if data is not None:
                    writer.writerow(data)
    