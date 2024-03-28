import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_web_title(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs Chrome in headless mode.
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Setup Chrome service
    service = Service(ChromeDriverManager().install())

    # Initialize the driver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)
    title = driver.title
    driver.quit()
    return title

st.title('Web Title Fetcher')

# User input for URL
url = st.text_input('Enter the URL of the website', 'http://www.example.com')

# Button to fetch the web page title
if st.button('Fetch Title'):
    with st.spinner('Fetching...'):
        title = get_web_title(url)
        st.success(f'The title of the page is: {title}')
