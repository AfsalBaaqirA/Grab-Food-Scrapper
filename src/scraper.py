import gzip
import json
from queue import Queue
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import ndjson
import logging
from utils import setup_driver, store_data
import requests
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(filename='logs/scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Main class for scraping GrabFood data
class GrabFoodScraper:
    def __init__(self):
        self.driver = setup_driver()
        self.restaurant_data = Queue()
        self.lock = threading.Lock()
        cookies = {
            "gfc_country": "SG",
            "gfc_session_guid": "694226c1-b9c1-4b47-89a7-0d98fc4abe21",
            "next-i18next": "en",
            "_gsvid": "1a6fec89-c5b1-421e-a7cb-21586fcb3a1e",
            "_gcl_au": "1.1.701740744.1715357490",
            "hwuuid": "adc3d9c5-d28c-4470-8cd5-1d400945a0ff",
            "hwuuidtime": "1715357540",
            "_ga": "GA1.1.1032334565.1715454609",
            "location": '{"latitude":1.367476,"longitude":103.858326,"address":"Block 456 Ang Mo Kio Avenue 10, #01-1574, Singapore, 560456","countryCode":"SG","isAccurate":true,"addressDetail":"Chong Boon Dental Surgery - Block 456 Ang Mo Kio Avenue 10, #01-1574, Singapore, 560456","noteToDriver":"","city":"Singapore City","cityID":6,"displayAddress":"Chong Boon Dental Surgery - Block 456 Ang Mo Kio Avenue 10, #01-1574, Singapore, 560456"}',
            "pid": "www.google.com",
            "c": "non-paid",
            "_gssid": "2404151150-xial46y7nxr",
            "_ga_RPEHNJMMEM": "GS1.1.1715773927.6.0.1715773927.60.0.995007504"
        }
        self.driver.get("https://food.grab.com/sg/en/") # Base URL
        time.sleep(3) # Wait for the page to load
        for key, value in cookies.items():
            self.driver.add_cookie({"name": key, "value": value}) # Add cookies to the driver

    def extract_restaurant_data(self):
        self.driver.get("https://food.grab.com/sg/en/restaurants") # URL to scrape restaurant details
        self.scroll_down() # Scroll down to load all restaurants
        restaurants = self.driver.find_elements(By.CLASS_NAME, 'RestaurantListCol___1FZ8V') # Get all restaurant cards
        
        # Split the restaurants into two halves and process them in parallel
        mid_index = len(restaurants) // 2
        restaurants1 = restaurants[:mid_index]
        restaurants2 = restaurants[mid_index:]

        thread1 = threading.Thread(target=self.process_restaurants, args=(restaurants1,))
        thread2 = threading.Thread(target=self.process_restaurants, args=(restaurants2,))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()


    # Retrieves basic details directly from the card
    def get_info_from_card(self, restaurant):
        try:
            link_element = restaurant.find_element(By.TAG_NAME, 'a')
            link = link_element.get_attribute('href')
            restaurant_id = link.split('/')[-1][:-1]
        except NoSuchElementException:
            restaurant_id = 'Not found'

        try:
            restaurant_name = restaurant.find_element(By.CLASS_NAME, 'name___2epcT').text
        except NoSuchElementException:
            restaurant_name = 'Not found'

        try:
            restaurant_cuisine = restaurant.find_element(By.CLASS_NAME, 'cuisine___T2tCh').text
        except NoSuchElementException:
            restaurant_cuisine = 'Not found'

        try:
            promotional_offers = restaurant.find_element(By.CLASS_NAME, 'discountText___GQCkj').text
        except NoSuchElementException:
            promotional_offers = 'No Offers'

        return restaurant_id, restaurant_name, restaurant_cuisine, promotional_offers

    # Retrieves additional details from the API
    def get_info_from_api(self, restaurant_id, restaurant_name, restaurant_cuisine, promotional_offers):
        try:
            time.sleep(3)
            url = f"https://portal.grab.com/foodweb/v2/merchants/{restaurant_id}?latlng=1.367210,103.858589"
            max_retries = 3
            backoff_time = 300  # Initial backoff time in seconds

            for attempt in range(max_retries):
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    break
                except requests.HTTPError as http_err:
                    if response.status_code == 429:  # Rate limit exceeded
                        logging.warning(f"Rate limit exceeded. Retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                    else:
                        logging.error(f"HTTP error occurred: {http_err}")
                        return None
                except Exception as err:
                    logging.error(f"Other error occurred: {err}")
                    return None
            else:
                logging.error(f"Failed to retrieve data after {max_retries} attempts")
                return None

            # Extract the latitude and longitude data and other data if the request is successful
            if response.status_code == 200:
                response = response.json()
                print(restaurant_id)
                if response['merchant']['estimatedDeliveryFee'].get('hasDiscountedPrice', False):
                    estimated_delivery_fee = response['merchant']['estimatedDeliveryFee'].get('discountedPrice',  response['merchant']['estimatedDeliveryFee']['price'])
                else:
                    estimated_delivery_fee = response['merchant']['estimatedDeliveryFee']['price']
                estimated_delivery_fee = f"S${str(estimated_delivery_fee)[:-2]}.{str(estimated_delivery_fee)[-2:]}"
                latitude = response['merchant']['latlng'].get('latitude', 'Not Available')
                longitude = response['merchant']['latlng'].get('longitude', 'Not Available')
                estimated_delivery_time = response['merchant'].get('ETA', 'Not Available')
                restaurant_distance = response['merchant'].get('distanceInKm', 'Not Available')
                restaurant_rating = response['merchant'].get('rating', 'Not Available')
                restaurant_image = response['merchant'].get('photoHref', 'Not Available')
                restaurant_promo = response['merchant'].get('promo', {}).get('hasPromo', 'False')
                restaurant_notice = response['merchant']['sofConfiguration'].get('tips', 'Not Available')

                if restaurant_distance != 'Not Available':
                    restaurant_distance = f"{restaurant_distance} km"
                if estimated_delivery_time != 'Not Available':
                    estimated_delivery_time = f"{estimated_delivery_time} mins"

                restaurant_data = {
                    'restaurant_id': restaurant_id,
                    'restaurant_name': restaurant_name,
                    'restaurant_cuisine': restaurant_cuisine,
                    'promotional_offers': promotional_offers,
                    'estimated_delivery_fee': estimated_delivery_fee,
                    'estimated_delivery_time': estimated_delivery_time,
                    'latitude': latitude,
                    'longitude': longitude,
                    'restaurant_distance': restaurant_distance,
                    'restaurant_rating': restaurant_rating,
                    'restaurant_image': restaurant_image,
                    'restaurant_promo': restaurant_promo,
                    'restaurant_notice': restaurant_notice
                }
                self.restaurant_data.put(restaurant_data)
                logging.info(f"Processed {restaurant_data['restaurant_name']}")
            else:
                print(response.json())
        except requests.RequestException as e:
            logging.error(f"Error fetching data for restaurant ID {restaurant_id}: {e}")

    # Main function called by each threads
    def process_restaurants(self, restaurants):
        for restaurant in restaurants:
            restaurant_id, restaurant_name, restaurant_cuisine, promotional_offers = self.get_info_from_card(restaurant)
            self.get_info_from_api(restaurant_id, restaurant_name, restaurant_cuisine, promotional_offers)

    # Scroll down feature to load all restaurants cards
    def scroll_down(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            time.sleep(4)

    def run(self):
        self.extract_restaurant_data()
        self.driver.quit()
        store_data(self.restaurant_data)

if __name__ == "__main__":
    start = time.time()
    scraper = GrabFoodScraper()
    scraper.run()
    end = time.time()
    print(f"Time taken: {end - start}") # Timer to check how long the script took to run