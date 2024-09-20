import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

class FBProfileImageFetcher:
    def __init__(self, name):
        f_name = name.replace(' ', '%20')
        self.url = f"https://facebook.com/public/?query={f_name}"
        self.profile_links = []

    def fetch_profile_links(self):
        driver = webdriver.Chrome()  # Make sure you have the Chrome WebDriver installed
        driver.get(self.url)

        time.sleep(10)  # Wait for the page to load and user to log in

        # Collect profile links from elements with class _2ial
        profile_elements = driver.find_elements(By.XPATH, "//a[@class='_2ial']")
        for element in profile_elements:
            href = element.get_attribute("href")
            self.profile_links.append(href)

        driver.close()

    def extract_ids(self, page_source):
        id_pattern = r'"container_id":"(\d+)"'
        return re.findall(id_pattern, page_source)

    def fetch_image_urls(self):
        image_urls = []
        driver = webdriver.Chrome()  # Make sure you have the Chrome WebDriver installed

        for profile_url in self.profile_links:
            driver.get(profile_url)
            time.sleep(5)  # Wait for the page to load

            # Get the page source and extract IDs
            page_source = driver.page_source
            ids = self.extract_ids(page_source)

            # Print each extracted ID
            for user_id in ids:
                print(f"Fetched ID: {user_id}")

                img_url = f"https://graph.facebook.com/{user_id}/picture?redirect=1&height=4000&type=normal&width=4000&access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662"
                
                # Make a request to the Graph API URL
                response = requests.get(img_url)
                if response.ok:
                    # Extract the redirected image URL from the response
                    redirected_url = response.url
                    image_urls.append(redirected_url)
                else:
                    print(f"Failed to fetch image for ID {user_id}")

        driver.close()
        return image_urls

if __name__ == "__main__":
    name = input("Enter the name to search on Facebook: ")
    fetcher = FBProfileImageFetcher(name)
    fetcher.fetch_profile_links()
    image_urls = fetcher.fetch_image_urls()

    # Print all the returned image URLs
    print("\nReturned Image URLs:")
    if image_urls:
        for url in image_urls:
            print(url)
    else:
        print("No image URLs found.")

