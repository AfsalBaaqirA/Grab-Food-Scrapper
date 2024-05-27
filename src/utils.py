from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import gzip
import ndjson

def setup_driver():
    options = webdriver.EdgeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

def store_data(restaurant_data):
        with gzip.open(f"data/restaurant_data.ndjson.gz", "wt", encoding="utf-8") as f:
            writer = ndjson.writer(f)
            while not restaurant_data.empty():
                data = restaurant_data.get()
                if data is not None:
                    writer.writerow(data)
    