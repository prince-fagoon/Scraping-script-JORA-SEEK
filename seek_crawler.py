#!/usr/bin/env python3
"""
Seek.com.au Crawler
Inherits from BaseCrawler and implements Seek-specific scraping logic
"""

from base_crawler import BaseCrawler
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import time
import random


class SeekCrawler(BaseCrawler):
    """Seek.com.au specific crawler implementation"""
    
    def __init__(self):
        super().__init__(
            portal_name="Seek",
            search_url="https://www.seek.com.au/sponsorship-available-jobs"
        )
    
    def wait_for_job_cards(self):
        """Wait for Seek job cards to load"""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card']"))
            )
        except TimeoutException:
            raise Exception("No job cards found on Seek")
    
    def get_job_cards(self, soup):
        """Get job cards from Seek page"""
        job_cards = soup.select("[data-testid='job-card']")
        return job_cards
    
    def extract_job_url(self, card):
        """Extract job URL from Seek job card"""
        job_link = card.select_one('a[href*="/job/"]')
        if job_link:
            return "https://www.seek.com.au" + job_link.get('href')
        return "N/A"
    
    def extract_job_details(self, soup, job_url):
        """Extract job details from Seek job page"""
        details = {}
        
        # Extract title - using the correct selector from job page
        title_elem = soup.select_one('[data-automation="job-detail-title"]')
        if not title_elem:
            title_elem = soup.select_one('h1')
        details['title'] = title_elem.get_text(strip=True) if title_elem else "N/A"
        
        # Extract company - using the correct selector from job page
        company_elem = soup.select_one('[data-automation="advertiser-name"]')
        if not company_elem:
            company_elem = soup.select_one('[data-automation="jobCompany"]')
        details['company'] = company_elem.get_text(strip=True) if company_elem else "N/A"
        
        # Extract location - using the correct selector from job page
        location_elem = soup.select_one('[data-automation="job-detail-location"]')
        if not location_elem:
            location_elem = soup.select_one('[data-automation="jobLocation"]')
        details['location'] = location_elem.get_text(strip=True) if location_elem else "N/A"
        
        # Extract salary - this job doesn't have specific salary info, so we'll use N/A
        salary = "N/A"
        # Try to find salary in aria-label or other elements
        salary_elem = soup.select_one('[data-automation="job-detail-salary"]')
        if salary_elem:
            salary = salary_elem.get_text(strip=True)
        else:
            # Try to find salary in aria-label
            salary_containers = soup.select('[aria-label*="Salary"]')
            for container in salary_containers:
                aria_label = container.get('aria-label', '')
                if 'Salary:' in aria_label:
                    salary = aria_label.replace('Salary:', '').strip()
                    break
        
        # If still no salary, try regex in description
        if salary == "N/A":
            desc_text = soup.get_text()
            salary_match = re.search(r'\$[\d,]+(?:\.\d{2})?(?:\s*-\s*\$[\d,]+(?:\.\d{2})?)?', desc_text)
            if salary_match:
                salary = salary_match.group()
        
        details['salary'] = salary
        
        # Extract description - using the correct selector from job page
        desc_elem = soup.select_one('[data-automation="job-detail-description"]')
        if not desc_elem:
            # Try to find description in the job content area
            desc_elem = soup.select_one('.sye2ly0')  # Based on the HTML structure
        if not desc_elem:
            desc_elem = soup.select_one('[data-automation="jobDescription"]')
        if not desc_elem:
            desc_elem = soup.select_one('.job-description')
        details['description'] = desc_elem.get_text(strip=True) if desc_elem else "N/A"
        
        return details
    
    def navigate_to_next_page(self, driver, page_number):
        """Navigate to next page on Seek"""
        print(f"\nLooking for next page on Seek...")
        
        # Always return to search results page before looking for pagination
        print(f"Returning to search results page to find next button...")
        driver.get(self.search_url)
        time.sleep(random.uniform(2, 3))
        
        # Wait for job cards to load again
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card']"))
            )
            print("✓ Returned to search results page successfully")
        except TimeoutException:
            print("✗ Timeout waiting for job cards after returning to search page")
            return False
        
        try:
            # Try multiple selectors for next button based on HTML analysis
            next_selectors = [
                'a[data-automation="page-' + str(page_number + 1) + '"][aria-label="Next"]',  # Exact match from HTML
                'a[aria-label="Next"]',  # Primary selector based on HTML analysis
                'a[data-automation="page-' + str(page_number + 1) + '"]',  # Dynamic page selector
                'a[rel="next"]',
                '[data-automation="page-next"]',
                'a[aria-label="next"]',
                'button[aria-label="Next"]',
                '.pagination a:last-child',
                '[data-testid="next-page"]',
                'a[href*="page=' + str(page_number + 1) + '"]'
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_displayed():
                        print(f"  ✓ Found next button with selector: {selector}")
                        break
                except:
                    continue
            
            # If no button found, try text-based search
            if not next_button:
                try:
                    next_links = driver.find_elements(By.TAG_NAME, 'a')
                    for link in next_links:
                        if link.text.strip().lower() == 'next':
                            next_button = link
                            break
                except:
                    pass
            
            # Additional check: look for any link with "Next" in aria-label
            if not next_button:
                try:
                    next_links = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label*="Next"]')
                    for link in next_links:
                        if 'Next' in link.get_attribute('aria-label'):
                            next_button = link
                            break
                except:
                    pass
            
            if next_button:
                print(f"  ✓ Next button found: {next_button.get_attribute('aria-label')} - Enabled: {next_button.is_enabled()}")
                if next_button.is_enabled():
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
                        return True
                        
                    except Exception as e:
                        print(f"Error clicking next button: {e}")
                        # Try URL-based pagination as fallback
                        try:
                            print("Trying URL-based pagination...")
                            base_search_url = "https://www.seek.com.au/sponsorship-available-jobs"
                            new_url = f"{base_search_url}?page={page_number + 1}"
                            driver.get(new_url)
                            time.sleep(random.uniform(2, 4))
                            print(f"✓ Successfully navigated to page {page_number + 1}")
                            return True
                        except Exception as url_error:
                            print(f"Error with URL-based pagination: {url_error}")
                            return False
                else:
                    print("  ✗ Next button is disabled")
                    print("✓ No more pages available")
                    return False
            else:
                print("  ✗ No next button found")
                # Debug: Show current URL and try to find any pagination elements
                print(f"  Debug: Current URL: {driver.current_url}")
                try:
                    pagination_elements = driver.find_elements(By.CSS_SELECTOR, 'a[data-automation*="page-"]')
                    print(f"  Debug: Found {len(pagination_elements)} pagination elements")
                    for elem in pagination_elements:
                        print(f"    - {elem.get_attribute('data-automation')} | {elem.get_attribute('aria-label')}")
                except:
                    pass
                print("✓ No more pages available")
                return False
                
        except Exception as e:
            print(f"Error finding next button: {e}")
            # Try URL-based pagination as fallback
            try:
                print("Trying URL-based pagination...")
                base_search_url = "https://www.seek.com.au/sponsorship-available-jobs"
                new_url = f"{base_search_url}?page={page_number + 1}"
                driver.get(new_url)
                time.sleep(random.uniform(2, 4))
                print(f"✓ Successfully navigated to page {page_number + 1}")
                return True
            except Exception as url_error:
                print(f"Error with URL-based pagination: {url_error}")
                return False
