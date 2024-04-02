import streamlit as st
import re
import json
from itertools import zip_longest
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import requests

# Set up the Streamlit page configuration
st.set_page_config(page_title="Facebook Review Extractor", page_icon="🌟")

def initialize_webdriver():
    """
    Initializes and returns a headless Selenium WebDriver.
    """
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(options=options)
    return driver

def close_login_popup(driver):
    """
    Attempts to close the login popup modal on the Facebook page.
    
    Args:
    driver: Selenium WebDriver instance used to interact with the webpage.
    """
    try:
        button_xpath = "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[1]/div/div[2]/div/div/div/div[1]/div"
        button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, button_xpath)))
        button.click()
    except Exception as e:
        print(f"Failed to close the login popup: {e}")

def scroll_and_collect_reviews(driver, reviews_to_fetch):
    """
    Scrolls the webpage and collects review elements until the desired number is reached.
    
    Args:
    driver: Selenium WebDriver instance for webpage interaction.
    reviews_to_fetch: The number of reviews to fetch from the page.

    Returns:
    A list of WebElement objects representing the reviews.
    """
    items = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while reviews_to_fetch > len(items):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for the page to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # Check if the page height has not changed after scrolling
            break
        last_height = new_height

        # Find and click 'See More' buttons to load additional content
        see_more_buttons = driver.find_elements(By.CSS_SELECTOR, 'div.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.xt0b8zv.xzsf02u.x1s688f[role="button"]')
        for button in see_more_buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView();", button)
                driver.execute_script("arguments[0].click();", button)
                time.sleep(1)  # Allow time for the content to load
            except Exception as e:
                print(f"Error clicking a 'See More' button: {e}")

        items = driver.find_elements(By.CLASS_NAME, 'x1yztbdb')

    return items[:reviews_to_fetch]

def extract_review_data(element, current_year):
    """
    Extracts data from a single review element.
    
    Args:
    element: The review WebElement to extract data from.
    current_year: The current year to append to dates that lack a year.

    Returns:
    A dictionary containing extracted review data.
    """
    html_code = element.get_attribute('outerHTML')
    soup = BeautifulSoup(html_code, 'html.parser')
    
    # Extract various pieces of data from the review element
    anchor_tag = soup.find('a', class_='x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1a2a7pz xzsf02u x1rg5ohu')
    name = anchor_tag['aria-label'] if anchor_tag else None
    image_url = soup.find('image')['xlink:href'] if anchor_tag else None
    
    span = soup.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x6prxxf xvq8zen xo1l8bm xi81zsa')
    recommendation = span.get_text(separator=' ', strip=True) if span else None

    span_tag = soup.find('span', class_='x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j')
    date = span_tag.get_text(strip=True) if span_tag else None
    review_link = span_tag.find('a')['href'] if span_tag else None

    review_text = None
    review_containers = soup.find_all(['span', 'div'], class_=['x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h', 'xzsf02u','xzsf02u xngnso2 xo1l8bm x1qb5hxa'])
    for container in review_containers:
        for img in container.find_all('img'):
            img.replace_with(img.get('alt', ''))
        text = container.get_text(separator=' ', strip=True)
        if text:
            review_text = text
            break

    # Clean and format the extracted data
    review_data = {
        "recommendation": re.sub(r'\s+(?=\.)', '', recommendation) if recommendation else None,
        "author_title": name,
        "author_image": image_url,
        "review_text": review_text,
        "review_link": review_link,
        "date": add_year_or_replace_hour(date, current_year) if date else None
    }
    return review_data


def add_year_or_replace_hour(date_str, year):
    """
    Adds the current year to a date string if the year is missing, or replaces relative time formats with the current date.
    
    Args:
    date_str: The date string to process.
    year: The current year to append if necessary.

    Returns:
    The processed date string with the year appended if it was missing.
    """
    if ' h' in date_str:  # If the format is like "6 h", indicating hours ago
        return datetime.now().strftime('%d %B %Y')  # Return the current date
    else:
        try:
            datetime.strptime(date_str, '%d %B %Y')
            return date_str  # If the date is already complete, return as is
        except ValueError:
            return f'{date_str} {year}'  # Append the current year to the date

def process_facebook_reviews(page_url, reviews_to_fetch):
    """
    Main function to process Facebook reviews from the given page URL.

    Args:
    page_url: The URL of the Facebook page from which to extract reviews.
    reviews_to_fetch: The number of reviews to fetch.

    Returns:
    A list of dictionaries, each containing data for a single review.
    """
    current_year = datetime.now().year

    # Attempt to make an initial request to validate the URL
    try:
        response = requests.get(page_url)
        if response.status_code != 200:
            st.error("Please enter a valid URL. The provided URL is not accessible or does not exist.")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while trying to access the URL: {e}")
        return []

    # Initialize WebDriver and navigate to the page
    driver = initialize_webdriver()
    driver.get(page_url)

    # Close the login popup if it appears
    close_login_popup(driver)

    # Scroll through the page and collect reviews
    items = scroll_and_collect_reviews(driver, reviews_to_fetch + 2)  # Fetch one extra to ensure enough reviews are collected

    # Extract data from each review element
    reviews_data = [extract_review_data(item, current_year) for item in items]
    reviews_data = reviews_data[1:reviews_to_fetch+1]

    # Cleanup and quit the WebDriver
    driver.quit()

    return reviews_data


# Define the Streamlit UI
def main():
    st.title('Facebook Page Review Extractor')

    # User inputs for the Facebook page URL and number of reviews to fetch
    default_url = 'https://www.facebook.com/insprimophotography'
    page_url = st.text_input('Enter Facebook Page URL', default_url)
    page_url += '/reviews'  # Append '/reviews' to navigate directly to the reviews section
    reviews_to_fetch = st.number_input('Enter Number of Reviews to Fetch', value=10, min_value=1)

    col1, col2 = st.columns(2)  # Create two columns for layout
    json_data = None

    with col1:  # Column for the 'Extract Reviews' button
        if st.button('Extract Reviews'):
            with st.spinner('Fetching and extracting reviews...'):
                json_data = process_facebook_reviews(page_url, reviews_to_fetch)
                if json_data:
                    st.success(f'Reviews extracted successfully! Found {len(json_data)} reviews.')
                    st.json(json_data)  # Display the extracted reviews as JSON in the app
                else:
                    st.error('No reviews found or an error occurred during extraction.')

    with col2:  # Column for the 'Download Reviews' button
        if json_data:
            json_string = json.dumps(json_data, indent=2)
            st.download_button(label="Download Reviews as JSON",
                               data=json_string,
                               file_name="facebook_reviews.json",
                               mime="application/json")

if __name__ == '__main__':
    main()
