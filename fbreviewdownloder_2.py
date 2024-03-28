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
from selenium.webdriver.chrome.options import Options
import requests
from selenium.webdriver.chrome.service import Service
from webdriver_manager.firefox import GeckoDriverManager


st.set_page_config(page_title="Facebook Review Extractor", page_icon="🌟")


# Function to process Facebook reviews
def process_facebook_reviews(page_url, max_scrolls):
    # Define the current year to append in case the date doesn't have a year
    current_year = datetime.now().year
    
    def add_year_if_missing(date_str, year):
        try:
            # Try to parse the date - if no year is present, ValueError will be raised
            datetime.strptime(date_str, '%d %B %Y')
            return date_str  # Date is fine, return as is
        except ValueError:
            # Date didn't include a year, so we add it
            return f'{date_str} {year}'
    
    try:
        response = requests.get(page_url)
        # If the response status code is not 200 (OK), raise an exception
        if response.status_code != 200:
            st.error("Please enter a valid URL. The provided URL is not accessible or does not exist.")
            return  # Stop execution if the URL is invalid
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while trying to access the URL: {e}")
        return  # Stop execution if there's an error accessing the URL

    #open browser in background
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    
    service = FirefoxService(executable_path=GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(page_url)

    #close the login popup which open immediately after loading the website
    button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[1]/div/div[2]/div/div/div/div[1]/div"))).click()

    time.sleep(2)

    #code to scroll the page until it fully loaded with 5 minutes with each iteration
    last_height = driver.execute_script("return document.body.scrollHeight")

    for scroll in range(max_scrolls):
        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for the page to load
        time.sleep(3)  # Adjust the wait time as needed

        # Calculate the new height of the page
        new_height = driver.execute_script("return document.body.scrollHeight")

        # Check if the page has stopped growing
        if new_height == last_height:
            break

        last_height = new_height # Update the last height

    see_more_buttons = driver.find_elements(By.CSS_SELECTOR, 'div.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xt0psk2.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.xt0b8zv.xzsf02u.x1s688f[role="button"]')

    # Iterate over found elements and click each one
    for button in see_more_buttons:
        try:
            # Scroll into view of the button and then click
            driver.execute_script("arguments[0].scrollIntoView();", button)
            # Click the button using JavaScript to avoid potential issues with elements covering the button
            driver.execute_script("arguments[0].click();", button)
            # Optional: add a short delay after each click to allow for dynamic content to load
            time.sleep(1)
        except Exception as e:
            print(f"Could not click on a button: {e}")

    elements = driver.find_elements(By.CLASS_NAME, 'x1yztbdb')

    #extract the required information
    names = []
    images = []
    recommendations = []
    dates = []
    reviews = []
    review_links = []
    for element in elements:
        html_code = element.get_attribute('outerHTML')
        soup = BeautifulSoup(html_code,'html.parser')

        anchor_tag = soup.find('a', class_='x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1a2a7pz xzsf02u x1rg5ohu')
        if anchor_tag:
            name = anchor_tag['aria-label']
            image_url = soup.find('image')['xlink:href']
            names.append(name)
            images.append(image_url)

        span = soup.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x6prxxf xvq8zen xo1l8bm xi81zsa')
        if span:
            recommendation = span.get_text(separator=' ', strip=True)
            recommendations.append(recommendation)  

        span_tag = soup.find('span', class_='x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j')
        if span_tag:
            date = span_tag.get_text(strip=True)
            review_link = span_tag.find('a')['href']
            dates.append(date)
            review_links.append(review_link)

        review = soup.find('span', class_=['x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h'])
        if review:
            for img in review.find_all('img'):
                img.replace_with(img.get('alt', ''))
            review_text = review.get_text()
            reviews.append(review_text)

        review = soup.find('div', class_=['xzsf02u xngnso2 xo1l8bm x1qb5hxa'])
        if review:
            for img in review.find_all('img'):
                img.replace_with(img.get('alt', ''))
            review_text = review.get_text(separator=' ',strip=True)
            reviews.append(review_text)

    #clean the output

    #remove the extra space in recommendation
    recommendations = [re.sub(r'\s+(?=\.)', '', string) for string in recommendations]

    # Update the dates list with the year added where necessary
    dates = [add_year_if_missing(date, current_year) for date in dates]

    #save the list in json format
    output = zip_longest(names, images, recommendations, dates, reviews,review_links)

    json_data = []
    for name,image,recommendation,date,review,review_link in output:
        entry = {
            "recommendation": recommendation if recommendation is not None else  None,
            "author_title": name if name is not None else None,
            "author_image": image if image is not None else None,
            "review_text": review if review is not None else None,
            "review_link": review_link if review_link is not None else None,
            "date": date if date is not None else None,
        }
        json_data.append(entry)
    return json_data

# Define the Streamlit app
def main():
    st.title('Facebook Page Review Extractor')

    # Input fields for the Facebook page URL and max scrolls
    page_url = st.text_input('Enter Facebook Page URL', 'https://www.facebook.com/insprimophotography')
    page_url = page_url + '/reviews'
    max_scrolls = st.number_input('Enter Max Scrolls', value=10, min_value=1)

    
    col1, col2 = st.columns(2)  # Create two columns

    with col1:  # This is the first column
        extract_reviews_pressed = st.button('Extract Reviews')

    json_data = None
    if extract_reviews_pressed:
        with st.spinner('Fetching and extracting reviews...'):
        # Call function to process Facebook reviews
            json_data = process_facebook_reviews(page_url, max_scrolls)
            st.json(json_data)

        if json_data:
            st.success(f'Reviews extracted successfully! Found {len(json_data["recommendation"])} reviews.')
            st.json(json_data)
        else:
            st.error('No reviews found or an error occurred during extraction.')


        if not json_data:
            st.error('No data to download.')
            # If there's no data, we don't want to show the download button, so return early
            return

    with col2:  # This is the second column
        # Only show the download button if there's data
        if json_data:
            # Serialize JSON data into a string
            json_string = json.dumps(json_data, indent=2)

            # Create a download button
            st.download_button(label="Download Reviews as JSON",
                               data=json_string,
                               file_name="facebook_reviews.json",
                               mime="application/json")


if __name__ == '__main__':
    main()
