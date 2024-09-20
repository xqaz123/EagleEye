import time
import requests
import re
import os
import tempfile
import random
import string
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
import utils.console as console

class FBProfileImageFetcher:
    def __init__(self, name):
        f_name = name.replace(' ', '%20')
        self.url = f"https://facebook.com/public/?query={f_name}"
        self.profile_links = []
        self.setup_driver()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode if you don't need a GUI
        self.driver = webdriver.Chrome(options=options)

    def fetch_profile_links(self):
        console.task(f"Fetching profile links from: {self.url}")
        self.driver.get(self.url)
        time.sleep(10)  # Wait for the page to load

        profile_elements = self.driver.find_elements(By.XPATH, "//a[@class='_2ial']")
        for element in profile_elements:
            href = element.get_attribute("href")
            self.profile_links.append(href)
            console.task(f"Found profile link: {href}")

        console.task("Finished fetching profile links.")

    def extract_ids(self, page_source):
        id_pattern = r'"container_id":"(\d+)"'
        return re.findall(id_pattern, page_source)

    def fetch_image_urls(self):
        image_urls = []

        for profile_url in self.profile_links:
            console.task(f"Fetching image URLs from: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(5)  # Wait for the page to load

            page_source = self.driver.page_source
            ids = self.extract_ids(page_source)
            console.task(f"Extracted IDs: {ids}")

            for user_id in ids:
                img_url = f"https://graph.facebook.com/{user_id}/picture?redirect=1&height=4000&type=normal&width=4000&access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662"
                response = requests.get(img_url)
                if response.ok:
                    redirected_url = response.url
                    image_urls.append(redirected_url)
                    console.task(f"Fetched image URL: {redirected_url}")

        console.task("Finished fetching image URLs.")
        self.driver.quit()  # Close the driver when done
        return image_urls

class FaceRecog:
    def __init__(self, profile_img):
        self.profile_img = profile_img
        console.section('Starting Face Recognition')

    def constructIndexes(self):
        console.section('Analyzing')
        for img_url in self.profile_img:
            console.task(f"Processing image from URL: {img_url}")
            response = requests.get(img_url)
            if response.ok:
                file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)) + '.jpg'
                tmp_path = os.path.join(tempfile.gettempdir(), file_name)
                with open(tmp_path, 'wb') as f:
                    f.write(response.content)
                console.task(f"Image saved to temporary path: {tmp_path}")
            else:
                console.failure(f"Failed to fetch image from {img_url}")

        self.run_face_recognition()

    def run_face_recognition(self):
        console.task("Running face recognition on all images in /tmp...")

        # Check if the command exists
        if not self.is_command_available('face_recognition'):
            console.failure("Error: 'face_recognition' command not found. Please ensure it is installed and available in your PATH.")
            return

        try:
            subprocess.run(['face_recognition', './known', tempfile.gettempdir()], check=True)
            console.task("Face recognition process completed.")
        except subprocess.CalledProcessError as e:
            console.failure(f"Face recognition command failed: {e}")

    def is_command_available(self, cmd):
        return subprocess.call(['which', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

if __name__ == "__main__":
    name = input("Enter the name to search on Facebook: ")
    fetcher = FBProfileImageFetcher(name)
    fetcher.fetch_profile_links()
    image_urls = fetcher.fetch_image_urls()

    if image_urls:
        face_recog = FaceRecog(profile_img=image_urls)
        face_recog.constructIndexes()
    else:
        console.failure("No image URLs found.")
