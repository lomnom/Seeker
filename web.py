"""
This module defines a simple interface to control a browser instance that can:
1. Search a term in a search engine (duckduckgo now) and return links to search results.
2. Open a page and return the text content
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import atexit
from log import log
import time

class WebInstance:
    """
    A browser instance that can:
    1. Search a term in duckduckgo and return links to search results.
    2. Open a page and return the text content

    Starts when initialised, stops when program terminates.
    """
    def __init__(self):
        """Creates the Selenium driver."""
        log("Starting browser...")

        driver = webdriver.Firefox()
        driver.set_window_size(767, 767) # Non-default viewport.
        atexit.register(driver.quit) # Quit driver on exit
        self.driver = driver

        log("Browser started.")

    ddg_url = "https://www.ddg.gg/search?q="
    def search_engine(self, query: str, result_n: int) -> list[str]:
        """
        Searches a query in duckduckgo.
        Returns the first result_n results. Note that this is
        is limited to the number of results on the first page for now.
        Returns list of urls.
        """
        log(f"Searching '{query}' on duckduckgo.")

        success = False
        while not success:
            try:
                self.driver.get(self.ddg_url + query)
            except Exception as e:
                log(repr(e) + f" encountered on search query {query}! Trying again in 30s")
                time.sleep(30)
            else:
                success = True
        self.driver.implicitly_wait(3) # Wait till page fully loads before proceeding

        # Get first n search result links
        search_urls = []
        for i in range(result_n):
            result = self.driver.find_element(By.ID, f'r1-{i}') 
            link = result.find_element(By.CSS_SELECTOR, '[data-testid="result-title-a"]')
            url = link.get_attribute("href")
            search_urls.append(url)

        return search_urls
    
    def page_text(self, url: str) -> str|None: 
        """
        Returns the text from the page at given URL.
        Returns None if fetching is unsuccessful. 

        Has an optimisation specific to MOE sites.
        """
        log(f"Reading page {url}.")
        try:
            # Open search result
            self.driver.get(url)
            # Wait till page fully loads before proceeding
            self.driver.implicitly_wait(3) 

            # Add all links to visible text so that page.text includes <a href=email> emails
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                text = link.text.strip()
                if href:
                    new_text = f"{text} [{href}]"
                    # Use JS to modify the page content
                    self.driver.execute_script("arguments[0].textContent = arguments[1];", link, new_text)
            
            # Extract page text
            page = self.driver.find_element(By.TAG_NAME, 'html') # Default behavior

            # On MOE sites
            try:
                # Where the page content lives in most MOE sites
                page = self.driver.find_element(By.CLASS_NAME, 'content')
            except:
                pass
            
            result = page.text
        except Exception as e:
            log(repr(e) + f" encountered on page {self.driver.current_url}! Ignoring page.")
            # Usually some fast-evolving page that isnt the correct one anyway 
            # causing stale element errors
            result = None

        return result