import streamlit as st
from playwright.sync_api import sync_playwright

def get_web_title(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        title = page.title()
        browser.close()
        return title

st.title('Web Page Title Fetcher with Playwright')

url = st.text_input('Enter the URL of the website', '')

if st.button('Fetch Title'):
    with st.spinner('Fetching...'):
        title = get_web_title(url)
        st.success(f'The title of the page is: "{title}"')
