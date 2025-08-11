#!/usr/bin/env python3
"""
Base Crawler Class for Job Portals
Contains common functionality for scraping job portals
"""

import time
import random
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import re
import os


class BaseCrawler(ABC):
    """Base class for job portal crawlers"""
    
    def __init__(self, portal_name, search_url):
        self.portal_name = portal_name
        self.search_url = search_url
        self.driver = None
        self.all_jobs_data = []
        
    def setup_chrome_driver(self):
        """
        Setup Chrome driver in headless mode (no browser window shown)
        """
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode (no GUI)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            print(f"Setting up Chrome driver for {self.portal_name}...")
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print(f"✓ Chrome driver setup successful for {self.portal_name}")
            return driver
        except Exception as e:
            print(f"✗ Chrome driver setup failed for {self.portal_name}: {e}")
            raise Exception(f"Could not setup Chrome driver for {self.portal_name}. Please ensure Chrome browser is installed and try again.")

    def wait_for_element(self, driver, selector, timeout=10):
        """Wait for an element to be present on the page"""
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            return False

    def scrape_job_details(self, driver, job_url):
        """Scrape detailed information from individual job page - to be overridden by child classes"""
        try:
            print(f"  → Navigating to job details: {job_url}")
            driver.get(job_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            time.sleep(random.uniform(1, 2))
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract specific information using portal-specific selectors
            details = self.extract_job_details(soup, job_url)
            
            # Add source information
            details['source'] = self.portal_name
            details['job_url'] = job_url
            
            print(f"  ✓ Successfully scraped details for: {details['title'][:50]}...")
            return details
            
        except Exception as e:
            print(f"  ✗ Error scraping job details: {e}")
            return {
                'title': 'Error loading',
                'company': 'N/A',
                'location': 'N/A',
                'salary': 'N/A',
                'description': 'N/A',
                'job_url': job_url,
                'source': self.portal_name
            }

    @abstractmethod
    def extract_job_details(self, soup, job_url):
        """Extract job details from BeautifulSoup object - must be implemented by child classes"""
        pass

    @abstractmethod
    def get_job_cards(self, soup):
        """Get job cards from BeautifulSoup object - must be implemented by child classes"""
        pass

    @abstractmethod
    def extract_job_url(self, card):
        """Extract job URL from job card - must be implemented by child classes"""
        pass

    @abstractmethod
    def navigate_to_next_page(self, driver, page_number):
        """Navigate to next page - must be implemented by child classes"""
        pass

    def scrape_jobs(self, max_pages=2):
        """Main scraping method that uses the portal-specific implementations"""
        try:
            print(f"{self.portal_name} Detailed Job Scraper")
            print("=" * 50)
            
            # Setup driver
            self.driver = self.setup_chrome_driver()
            
            # Navigate to search page
            print(f"Navigating to: {self.search_url}")
            self.driver.get(self.search_url)
            
            # Wait for page to load
            print("Waiting for page to load...")
            time.sleep(3)
            
            page_number = 1
            
            while page_number <= max_pages:
                print(f"\nScraping page {page_number} for {self.portal_name}...")
                
                # First, go back to the search results page if we're on a job detail page
                current_url = self.driver.current_url
                if '/job/' in current_url:
                    print("Currently on job detail page, returning to search results...")
                    self.driver.get(self.search_url)
                    time.sleep(random.uniform(2, 3))
                
                # Wait for job cards to load using portal-specific selector
                try:
                    self.wait_for_job_cards()
                    print("✓ Job cards loaded successfully")
                except Exception as e:
                    print(f"✗ Timeout waiting for job cards: {e}")
                    break
                
                # Parse job cards
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_cards = self.get_job_cards(soup)
                
                if not job_cards:
                    print("✓ No more job cards found. Ending scrape.")
                    break
                
                print(f"✓ Found {len(job_cards)} jobs on page {page_number}.")
                
                # Process each job card
                for i, card in enumerate(job_cards, 1):
                    print(f"\nProcessing job {i}/{len(job_cards)} on page {page_number}")
                    
                    # Extract job URL
                    job_url = self.extract_job_url(card)
                    
                    if job_url and job_url != "N/A":
                        print(f"  → Scraping detailed information...")
                        job_data = self.scrape_job_details(self.driver, job_url)
                        
                        # Wait between jobs to avoid being blocked
                        time.sleep(random.uniform(1, 2))
                    else:
                        print(f"  ⚠ No job URL found, skipping job")
                        job_data = {
                            'title': 'N/A',
                            'company': 'N/A',
                            'location': 'N/A',
                            'salary': 'N/A',
                            'description': 'N/A',
                            'job_url': 'N/A',
                            'source': self.portal_name
                        }
                    
                    self.all_jobs_data.append(job_data)
                    print(f"✓ Completed job {i}/{len(job_cards)}")
                
                # Navigate to next page
                if page_number < max_pages:
                    if not self.navigate_to_next_page(self.driver, page_number):
                        print(f"No more pages available for {self.portal_name}")
                        break
                    page_number += 1
                else:
                    print(f"✓ Reached maximum pages limit ({max_pages}) for {self.portal_name}")
                    break
            
            print(f"\n✓ {self.portal_name} scraping completed. Total jobs: {len(self.all_jobs_data)}")
            return self.all_jobs_data
            
        except Exception as e:
            print(f"✗ An error occurred during {self.portal_name} scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
            
        finally:
            # Always close the driver
            if self.driver:
                try:
                    self.driver.quit()
                    print(f"✓ Browser closed successfully for {self.portal_name}")
                except:
                    pass

    def wait_for_job_cards(self):
        """Wait for job cards to load - to be overridden by child classes if needed"""
        # Default implementation - child classes can override
        pass

    def get_jobs_data(self):
        """Return the collected jobs data"""
        return self.all_jobs_data
