import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Initialize the WebDriver in headless mode

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)
#driver = webdriver.Chrome()
# Base URL
base_url = "https://meirtv.com/alonei-shabat/"

def download_file(url, download_dir):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        file_name = os.path.join(download_dir, os.path.basename(url))
        with open(file_name, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {file_name}")
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")

def scrape_page(url, search_text, download_dir):
    # Navigate to the URL
    driver.get(url)

    # Wait until the necessary elements are present
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.elementor-heading-title.elementor-size-default a"))
        )
    except Exception as e:
        print(f"An error occurred while waiting for the page to load: {e}")
        return

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Find all elements that match the given selector
    elements = soup.select('h2.elementor-heading-title.elementor-size-default a')

    # Extract and print the text content of each <a> tag that contains the search text
    for element in elements:
        text = element.get_text(strip=True)
        if search_text in text:
            print(text)
            # Extract the href attribute and navigate to the new URL
            link = element.get('href')
            if link:
                driver.get(link)

                # Wait until the new page is loaded
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".jet-listing-dynamic-field__content a[href$='.pdf']"))
                    )
                    # Parse the new page with BeautifulSoup
                    new_soup = BeautifulSoup(driver.page_source, 'lxml')
                    pdf_link = new_soup.select_one(".jet-listing-dynamic-field__content a[href$='.pdf']")
                    if pdf_link:
                        pdf_url = pdf_link.get('href')
                        download_file(pdf_url, download_dir)
                except Exception as e:
                    print(f"Failed to find PDF link on the new page: {e}")

                # Go back to the original page
                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h2.elementor-heading-title.elementor-size-default a"))
                )

    # Find the next page button and navigate to the next page if it exists
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='jet-filters-pagination__link' and contains(text(), 'הבא')]"))
        )
        next_button.click()  # Click the next button

        # Wait for the new page to load before continuing
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.elementor-heading-title.elementor-size-default a"))
        )
        scrape_page(driver.current_url, search_text, download_dir)  # Recursively scrape the next page
    except Exception:
        print("No more pages.")

# Prompt the user for the search text
search_text = input("Enter the text to search for: ")

# Create a directory to save downloaded files based on user input
download_dir = os.path.join("downloads", search_text)
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Start scraping from the base URL
scrape_page(base_url, search_text, download_dir)

# Close the WebDriver
driver.quit()
