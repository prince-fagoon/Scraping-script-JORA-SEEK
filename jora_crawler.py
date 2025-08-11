#!/usr/bin/env python3
"""
Jora.com Crawler
Inherits from BaseCrawler and implements Jora-specific scraping logic
"""

from base_crawler import BaseCrawler
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import random


class JoraCrawler(BaseCrawler):
    """Jora.com specific crawler implementation"""
    
    def __init__(self):
        super().__init__(
            portal_name="Jora",
            search_url="https://au.jora.com/j?q=sponsorship+available&l=Australia"
        )
    
    def wait_for_job_cards(self):
        """Wait for Jora job cards to load"""
        try:
            # Wait for job cards to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
            )
        except Exception as e:
            # Try alternative selector
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article.job-card"))
                )
            except:
                raise Exception("No job cards found on Jora")
    
    def get_job_cards(self, soup):
        """Get job cards from Jora page"""
        # Try multiple selectors for job cards based on HTML analysis
        job_cards = soup.select('div.job-card.result')
        if not job_cards:
            job_cards = soup.select('article.job-card')
        if not job_cards:
            job_cards = soup.select('[data-job-card="true"]')
        
        return job_cards
    
    def extract_job_url(self, card):
        """Extract job URL from Jora job card"""
        title_elem = card.select_one('h2.job-title a')
        if title_elem and title_elem.has_attr('href'):
            href = title_elem['href']
            return "https://au.jora.com" + href if href.startswith('/') else href
        return "N/A"
    
    def extract_job_details(self, soup, job_url):
        """Extract job details from Jora job page"""
        details = {}
        
        # Job title - using the correct selector from debug HTML
        title_elem = soup.select_one('h1.job-title')
        details['title'] = title_elem.get_text(strip=True) if title_elem else "N/A"
        
        # Company name - using the correct selector from debug HTML
        company_elem = soup.select_one('span.company')
        details['company'] = company_elem.get_text(strip=True) if company_elem else "N/A"
        
        # Location - using the correct selector from debug HTML
        location_elem = soup.select_one('span.location')
        details['location'] = location_elem.get_text(strip=True) if location_elem else "N/A"
        
        # Salary - look for salary information in badges or other elements
        salary = "N/A"
        # Try to find salary in badges
        badge_elements = soup.select('div.badge .content')
        for badge in badge_elements:
            badge_text = badge.get_text(strip=True)
            if '$' in badge_text or 'salary' in badge_text.lower() or 'pay' in badge_text.lower():
                salary = badge_text
                break
        
        # Also check for salary in other common locations
        if salary == "N/A":
            # Look for salary in job description
            desc_text = details.get('description', '')
            if '$' in desc_text:
                # Extract salary from description
                salary_match = re.search(r'\$[\d,]+(?:\.\d{2})?(?:\s*-\s*\$[\d,]+(?:\.\d{2})?)?', desc_text)
                if salary_match:
                    salary = salary_match.group()
        
        details['salary'] = salary
        
        # Job description - using the correct selector from debug HTML
        desc_container = soup.select_one('#job-description-container')
        if desc_container:
            # Get all text content from the description container
            details['description'] = desc_container.get_text(strip=True)
        else:
            details['description'] = "N/A"
        
        return details
    
    def navigate_to_next_page(self, driver, page_number):
        """Navigate to next page on Jora"""
        print(f"\nLooking for next page on Jora...")
        
        # First, go back to the search results page if we're on a job detail page
        current_url = driver.current_url
        if '/job/' in current_url:
            print("Currently on job detail page, returning to search results...")
            driver.get(self.search_url)
            time.sleep(random.uniform(2, 3))
            
            # Wait for job cards to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
            )
        
        # Try to find the next button using the correct selectors from analysis
        next_button = None
        
        # Primary selectors based on the HTML analysis
        next_selectors = [
            'a.rounded-button.-primary.-size-lg.-w-full',  # Mobile next button
            'a.next-page-button',  # Desktop next page button
            'a.pagination-page',  # Any pagination page link
            'a[href*="&p=' + str(page_number + 1) + '"]'  # Direct URL with next page number
        ]
        
        for selector in next_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # For pagination-page, find the one with the next page number
                    if 'pagination-page' in selector:
                        for elem in elements:
                            href = elem.get_attribute('href')
                            if href and f'&p={page_number + 1}' in href:
                                next_button = elem
                                print(f"Found next page button with selector: {selector}")
                                break
                    else:
                        next_button = elements[0]
                        print(f"Found next button with selector: {selector}")
                        break
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        
        # Alternative: Look for next button by text content
        if not next_button:
            try:
                all_links = driver.find_elements(By.TAG_NAME, 'a')
                for link in all_links:
                    if 'next' in link.text.lower() and link.is_enabled():
                        next_button = link
                        print("Found next button by text content")
                        break
            except:
                pass
        
        if next_button and next_button.is_enabled():
            try:
                print(f"Clicking next button to go to page {page_number + 1}")
                
                # Try multiple click methods
                try:
                    # Method 1: JavaScript click
                    driver.execute_script("arguments[0].click();", next_button)
                except:
                    try:
                        # Method 2: Direct click
                        next_button.click()
                    except:
                        # Method 3: Get href and navigate
                        href = next_button.get_attribute('href')
                        if href:
                            driver.get(href)
                        else:
                            raise Exception("No href found on next button")
                
                time.sleep(random.uniform(2, 4))  # Wait for page to load
                
                # Wait for new job cards to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
                )
                print(f"✓ Successfully navigated to page {page_number + 1}")
                return True
                
            except Exception as e:
                print(f"Error clicking next button: {e}")
                # Try URL-based pagination as fallback
                print("Trying URL-based pagination...")
                try:
                    # Use the original search URL as base for pagination
                    base_search_url = "https://au.jora.com/j?q=sponsorship+available&l=Australia"
                    new_url = f"{base_search_url}&p={page_number + 1}"
                    
                    print(f"Navigating to: {new_url}")
                    driver.get(new_url)
                    time.sleep(random.uniform(2, 4))
                    
                    # Wait for new job cards to load
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
                    )
                    print(f"✓ Successfully navigated to page {page_number + 1} via URL")
                    return True
                    
                except Exception as url_error:
                    print(f"Error with URL-based pagination: {url_error}")
                    print(f"Stopping at page {page_number}")
                    return False
        else:
            print(f"No next button found or it's disabled. Stopping at page {page_number}")
            return False
