from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests

options = Options()
options.add_argument("--headless=new")  # no window
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
if driver:
    print("Web Driver initiated")

# Navigate to the page for textbook search
url = "https://ocw.mit.edu/search/?r=Open%20Textbooks&type=resourcefile&u=compact"
driver.get(url)

# Scroll till the end of the page
wait = WebDriverWait(driver, 30)
i=0
while True:
    try:
        # wait for spinner to appear, then disappear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.loading[data-testid='spinner']")))
    except:
        # no spinner found = reached end of results
        print("Spinner wait timeout")
        break

    # scroll down to load more content
    i+=1
    print(f"Scrolling...{i}")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

# Get all the download pages links
download_pages=[]

pdf_images = driver.find_elements(By.CSS_SELECTOR, "img[alt='pdf']")
for img in pdf_images:
    a_tag = img.find_element(By.XPATH, "./parent::a")
    link = a_tag.get_attribute("href")
    download_pages.append(link)
    print(f"Download Page Found: {link}")

# Setup for Download
DOWNLOAD_FOLDER_NAME = "data/mit_ocw_textbooks"
os.makedirs(DOWNLOAD_FOLDER_NAME, exist_ok=True)
queue_number = 0
max_queue = 3
active_tabs = []

for download_page in download_pages:
    if queue_number < max_queue:
        # open new tab
        driver.execute_script(f"window.open('{download_page}', '_blank');")
        active_tabs.append(driver.window_handles[-1])
        queue_number += 1
        print(f"Opened {download_page} (Queue: {queue_number}/{max_queue})")
    else:
        # process current open tabs
        for handle in list(active_tabs):  # copy since we'll modify list
            driver.switch_to.window(handle)
            try:
                pdf_link = driver.find_element(By.CSS_SELECTOR, "a[href$='.pdf']").get_attribute("href")
                file_name = pdf_link.split("/")[-1]
                response = requests.get(pdf_link)
                with open(os.path.join(DOWNLOAD_FOLDER_NAME, file_name), "wb") as f:
                    f.write(response.content)
                print(f" Downloaded: {file_name}")
            except:
                pass

            # close tab, update queue
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            active_tabs.remove(handle)
            queue_number -= 1
            print(f"Closed tab. Queue now {queue_number}")

    time.sleep(1)

