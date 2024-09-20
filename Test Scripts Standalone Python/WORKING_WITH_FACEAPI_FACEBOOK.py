import time
import requests
import re
import os
import tempfile
import cv2
import random
import string
from pathlib import Path
import face_recognition
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from utils.console import task, section, subtask, failure
from face_recognition import face_distance

class FBProfileImageFetcher:
    def __init__(self, name):
        f_name = name.replace(' ', '%20')
        self.url = f"https://facebook.com/public/?query={f_name}"
        self.profile_links = []

    def fetch_profile_links(self):
        task(f"Fetching profile links from: {self.url}")

        options = Options()
        options.add_argument("--headless")  # Enable headless mode
        driver = webdriver.Chrome(options=options)

        driver.get(self.url)
        time.sleep(10)

        profile_elements = driver.find_elements(By.XPATH, "//a[@class='_2ial']")
        for element in profile_elements:
            href = element.get_attribute("href")
            self.profile_links.append(href)
            task(f"Found profile link: {href}")

        driver.close()
        task("Finished fetching profile links.")

    def extract_ids(self, page_source):
        id_pattern = r'"container_id":"(\d+)"'
        return re.findall(id_pattern, page_source)

    def fetch_image_urls(self):
        image_urls = []
        
        options = Options()
        options.add_argument("--headless")  # Enable headless mode
        driver = webdriver.Chrome(options=options)

        for profile_url in self.profile_links:
            driver.get(profile_url)
            time.sleep(5)

            page_source = driver.page_source
            ids = self.extract_ids(page_source)
            task(f"Extracted IDs: {ids}")

            for user_id in ids:
                img_url = f"https://graph.facebook.com/{user_id}/picture?redirect=1&height=4000&type=normal&width=4000&access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662"
                response = requests.get(img_url)
                if response.ok:
                    redirected_url = response.url
                    image_urls.append(redirected_url)

        driver.close()
        task("Finished fetching image URLs.")
        return image_urls

class FaceRecog:
    def __init__(self, profile_img, num_jitters=1, threshold=0.5):  # Added threshold parameter
        self.profile_img = profile_img
        self.num_jitters = num_jitters
        self.threshold = threshold  # Set threshold for face matching
        self.known_face_encodings = []
        self.known_face_names = []
        section('Starting Face Recognition')

    def loadKnown(self, label):
        task('Loading known faces...')
        pa_g = Path('./known')
        for ext in ['.jpg', '.png', '.jpeg', '.bmp']:
            pathlist = list(pa_g.glob(f'**/*{ext}'))
            for path in pathlist:
                p_str = str(path)
                subtask(f'Loading {p_str}')
                im = face_recognition.load_image_file(p_str)
                encoding = face_recognition.face_encodings(im, num_jitters=1)
                for e in encoding:
                    self.known_face_encodings.append(e)
                    self.known_face_names.append(label)

    def constructIndexes(self, label):
        section('Analyzing')
        for img_url in self.profile_img:
            response = requests.get(img_url)
            if response.ok:
                file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)) + '.jpg'
                tmp_path = os.path.join(tempfile.gettempdir(), file_name)
                with open(tmp_path, 'wb') as f:
                    f.write(response.content)

                self.compare_faces(tmp_path, label)
            else:
                failure(f"Failed to fetch image from {img_url}")

    def compare_faces(self, img_path, label):
        task(f"Comparing {img_path} with known faces...")
        frame = cv2.imread(img_path)

        if frame is None:
            failure(f"Failed to read image from {img_path}.")
            return

        rgb_small_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)

        if not face_locations:
            failure(f"No faces detected in the image: {img_path}")
            return

        face_encodings = []
        for location in face_locations:
            encodings = face_recognition.face_encodings(rgb_small_frame, [location], num_jitters=self.num_jitters)
            face_encodings.extend(encodings)

        if not face_encodings:
            failure("No face encodings could be found.")
            return

        detected_names = set()

        for face_encoding in face_encodings:
            distances = face_distance(self.known_face_encodings, face_encoding)
            matches = distances < self.threshold  # Use the threshold for matching
            if True in matches:
                first_match_index = matches.argmax()
                name = self.known_face_names[first_match_index]
                detected_names.add(name)

        if detected_names:
            for name in detected_names:
                task(f"Detected {name} in the image.")
                self.show_image(frame)  # Show the matching image
        else:
            task("No known faces detected.")

    def show_image(self, frame):
        cv2.imshow("Matched Face", frame)
        cv2.waitKey(0)  # Wait indefinitely until a key is pressed
        cv2.destroyAllWindows()  # Close the displayed image window

if __name__ == "__main__":
    name = input("Enter the name to search on Facebook: ")
    label = input("Enter the label for known faces: ")
    
    # Ask user for number of jitters
    while True:
        try:
            num_jitters = int(input(f"Enter the number of jitters (default is 70, max is 100): ") or 70)
            if 1 <= num_jitters <= 100:
                break
            else:
                print("Please enter a value between 1 and 100.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    fetcher = FBProfileImageFetcher(name)
    fetcher.fetch_profile_links()
    image_urls = fetcher.fetch_image_urls()

    if image_urls:
        face_recog = FaceRecog(profile_img=image_urls, num_jitters=num_jitters)
        face_recog.loadKnown(label)
        face_recog.constructIndexes(label)
    else:
        failure("No image URLs found.")
