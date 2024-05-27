# Grab Food Scraper

This project is a web scraper for [Grab Food](https://food.grab.com/sg/en/) using Python and Selenium. It extracts 
1. Restaurant Name
2. Restaurant Cuisine
3. Restaurant Rating
4. Estimated time of Delivery
5. Restaurant Distance from Delivery Location
6. Promotional Offers
7. Restaurant Notice If Visible.
8. Image Link of the Restaurant
9. Is promo available (True/False)
10. Restaurant ID
11. Restaurant latitude and longitude
12. Estimated Delivery Fee

## Getting Started

Follow the below instructions to setup and run the scraper on your local machine.

### Prerequisites

You need to have Python installed on your machine. You can download Python [here](https://www.python.org/downloads/).

### Installing

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Set up a virtual environment:
        ```sh
        python -m venv venv
        ```
4. Activate the virtual environment:
        ```sh
        .\venv\Scripts\activate
        ```
5. Install the required packages:
        ```sh
        pip install -r requirements.txt
        ```

## Running the Scraper

To run the scraper, navigate to the `src` directory and run the `scraper.py` script:
    ```sh
    python scraper.py
    ```

## Extracted data

1. The extracted data is stored in data/restaurant_data.ndjson.gz file.
2. The count of restaurants scraped for the location ```Chong Boon Dental Surgery - Block 456 Ang Mo Kio Avenue 10, #01-1574, Singapore, 560456``` 
    is about ``` 290 - 295 ```.
3. The number of restaurants scraped for the location differs for different runs due to the dependency on the accuracy of the location.

## Overall Approach
1. First I implemented it fully using python lists and dictionaries. Later moving on to multi-threading I discovered that queue would be more efficient.
2. My first approach on multi-threading was to simply divide the workload to 2 threads, But later I implemented threadpool to make it more ease to scale up and down.
3. The Grab Food website seems to be deployed on AWS and prevents scrapping by blocking the IP address if there is too much traffic via CloudFront.
4. So I had to do some research on the original source of the data and found that the data is being fetched from the API.
5. But API also has some rate limit, so increasing the number of threads would result in blocking the IP address. 
6. It requires to be found a sweet spot of number of threads to determine number of requests made to API in a specific period of time.

## Challenges
1. The Grab Food website is deployed on AWS and prevents scrapping by blocking the IP address if there is too much traffic via CloudFront.
2. The API also has some rate limit, so increasing the number of threads would result in blocking the IP address.
3. The website is dynamic and the data is loaded using javascript, so I had to use selenium to scrape the data. 

## Future Improvements
1. Implementing a rotating proxy to avoid blocking the IP address.

## Analysis
1. Single Thread Time taken: 139.82602047920227
2. Dual Thread Time taken: 79.92468237876892

Note: The time taken is for scraping 290-295 restaurants for the location ```Chong Boon Dental Surgery - Block 456 Ang Mo Kio Avenue 10, #01-1574, Singapore, 560456``` time may vary depending on network speed and hardware capabilities.

## Important Notes
1. The API has a rate limit, so increasing the number of threads results in 429 HTTP Error.
2. While running the scraper, you may experience 429 HTTP Error too, so I would suggest you to either try after some time or reduce the number of threads.
3. I have implemented threadpool so it will be easy to scale up and down while testing the scraper.
4. To change the location you need to change the cookies. Just replace the already existing location cookie with this value.
        ```
         "location": '{
                "latitude": 1.396364,
                "longitude": 103.747462,
                "address": "Choa Chu Kang North 6, Singapore, 689577",
                "countryCode": "SG",
                "isAccurate": True,
                "addressDetail": "PT Singapore - Choa Chu Kang North 6, Singapore, 689577",
                "noteToDriver": "",
                "city": "Singapore City",
                "cityID": 6,
                "displayAddress": "PT Singapore - Choa Chu Kang North 6, Singapore, 689577"
                }'
        ```
5. After changing the location cookie, you need to change the geolocation details in the API endpoint too.
```
url = f"https://portal.grab.com/foodweb/v2/merchants/{restaurant_id}?latlng=1.396364,103.747462"
```
