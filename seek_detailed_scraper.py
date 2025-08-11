#!/usr/bin/env python3
"""
Seek.com.au Detailed Job Scraper
Scrapes detailed job information by clicking each job link
"""

import time
import random
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import re
import os

def setup_chrome_driver():
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
        print("Setting up Chrome driver in headless mode...")
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✓ Chrome driver setup successful (headless mode)")
        return driver
    except Exception as e:
        print(f"✗ Chrome driver setup failed: {e}")
        raise Exception("Could not setup Chrome driver. Please ensure Chrome browser is installed and try again.")

def wait_for_element(driver, selector, timeout=10):
    """Wait for an element to be present on the page"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return True
    except TimeoutException:
        return False

def scrape_job_details(driver, job_url):
    """Scrape detailed information from individual job page"""
    try:
        print(f"  → Navigating to job details...")
        driver.get(job_url)
        
        # Wait for page to load with timeout
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            print(f"  ⚠ Timeout waiting for job page to load, skipping...")
            return {
                'title': 'N/A',
                'company': 'N/A', 
                'location': 'N/A',
                'salary': 'N/A',
                'description': 'N/A',
                'job_url': job_url
            }
        
        time.sleep(random.uniform(1, 2))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
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
        
        details['job_url'] = job_url
        
        print(f"  ✓ Extracted: {details['title'][:50]}...")
        return details
        
    except Exception as e:
        print(f"  ✗ Error scraping job details: {e}")
        return {
            'title': 'N/A',
            'company': 'N/A', 
            'location': 'N/A',
            'salary': 'N/A',
            'description': 'N/A',
            'job_url': job_url
        }

def scrape_seek_jobs():
    """Main function to scrape Seek.com.au jobs"""
    search_url = "https://www.seek.com.au/sponsorship-available-jobs"
    driver = None
    
    try:
        print("Seek.com.au Detailed Job Scraper")
        print("=" * 50)
        
        # Setup driver
        driver = setup_chrome_driver()
        
        # Navigate to search page
        print(f"Navigating to: {search_url}")
        driver.get(search_url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(3)
        
        all_jobs_data = []
        page_number = 1
        max_pages = 22  # Scrape 30 pages
        
        while page_number <= max_pages:
            print(f"\nScraping page {page_number}...")
            
            # First, go back to the search results page if we're on a job detail page
            current_url = driver.current_url
            if '/job/' in current_url:
                print("Currently on job detail page, returning to search results...")
                driver.get(search_url)
                time.sleep(random.uniform(2, 3))
                
                # Wait for job cards to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card']"))
                )
            
            # Wait for job cards to load
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card']"))
                )
                print("✓ Job cards loaded successfully")
            except TimeoutException:
                print("✗ Timeout waiting for job cards")
                break
            
            # Parse job cards
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.select("[data-testid='job-card']")
            
            if not job_cards:
                print("✗ No job cards found")
                break
            
            print(f"Found {len(job_cards)} jobs on page {page_number}.")
            
            # Extract basic info from cards and get job URLs
            job_urls = []
            # Process ALL job cards on each page
            job_cards_to_process = job_cards
            
            for i, card in enumerate(job_cards_to_process):
                try:
                    # Extract basic info from card
                    title_elem = card.select_one('[data-testid="job-card-title"]')
                    company_elem = card.select_one('[data-automation="jobCompany"]')
                    location_elem = card.select_one('[data-automation="jobLocation"]')
                    salary_elem = card.select_one('[data-automation="jobSalary"]')
                    
                    title = title_elem.get_text(strip=True) if title_elem else "N/A"
                    company = company_elem.get_text(strip=True) if company_elem else "N/A"
                    location = location_elem.get_text(strip=True) if location_elem else "N/A"
                    salary = salary_elem.get_text(strip=True) if salary_elem else "N/A"
                    
                    # Get job URL
                    job_link = card.select_one('a[href*="/job/"]')
                    if job_link:
                        job_url = "https://www.seek.com.au" + job_link.get('href')
                        job_urls.append(job_url)
                        print(f"  {i+1}. {title[:50]}... - {company}")
                    else:
                        print(f"  {i+1}. No job URL found for: {title[:50]}...")
                        
                except Exception as e:
                    print(f"  ✗ Error processing job card {i+1}: {e}")
                    continue
            
            # Scrape detailed info for each job
            for i, job_url in enumerate(job_urls):
                print(f"\n  Scraping detailed information... ({i+1}/{len(job_urls)})")
                try:
                    job_details = scrape_job_details(driver, job_url)
                    all_jobs_data.append(job_details)
                    print(f"  ✓ Completed job {i+1}/{len(job_urls)}")
                except Exception as e:
                    print(f"  ✗ Failed to scrape job {i+1}: {e}")
                    # Add empty data to maintain count
                    all_jobs_data.append({
                        'title': 'ERROR',
                        'company': 'ERROR', 
                        'location': 'ERROR',
                        'salary': 'ERROR',
                        'description': 'ERROR',
                        'job_url': job_url
                    })
                
                # Random delay between jobs
                time.sleep(random.uniform(1, 3))
            
            # Check if there's a next page
            if page_number < max_pages:
                # Always return to search results page before looking for pagination
                print(f"Returning to search results page to find next button...")
                driver.get(search_url)
                time.sleep(random.uniform(2, 3))
                
                # Wait for job cards to load again
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card']"))
                    )
                    print("✓ Returned to search results page successfully")
                except TimeoutException:
                    print("✗ Timeout waiting for job cards after returning to search page")
                    break
                
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
                                
                                page_number += 1
                                time.sleep(random.uniform(2, 4))  # Wait for page to load
                                
                            except Exception as e:
                                print(f"Error clicking next button: {e}")
                                # Try URL-based pagination as fallback
                                try:
                                    print("Trying URL-based pagination...")
                                    base_search_url = "https://www.seek.com.au/sponsorship-available-jobs"
                                    new_url = f"{base_search_url}?page={page_number + 1}"
                                    driver.get(new_url)
                                    page_number += 1
                                    time.sleep(random.uniform(2, 4))
                                    print(f"✓ Successfully navigated to page {page_number}")
                                except Exception as url_error:
                                    print(f"Error with URL-based pagination: {url_error}")
                                    break
                        else:
                            print("  ✗ Next button is disabled")
                            print("✓ No more pages available")
                            break
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
                        break
                        
                except Exception as e:
                    print(f"Error finding next button: {e}")
                    # Try URL-based pagination as fallback
                    try:
                        print("Trying URL-based pagination...")
                        base_search_url = "https://www.seek.com.au/sponsorship-available-jobs"
                        new_url = f"{base_search_url}?page={page_number + 1}"
                        driver.get(new_url)
                        page_number += 1
                        time.sleep(random.uniform(2, 4))
                        print(f"✓ Successfully navigated to page {page_number}")
                    except Exception as url_error:
                        print(f"Error with URL-based pagination: {url_error}")
                        break
            else:
                print(f"✓ Reached maximum pages limit ({max_pages})")
                break
        
        # Save to CSV
        if all_jobs_data:
            df = pd.DataFrame(all_jobs_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"seek_jobs_detailed_{timestamp}.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"\n" + "=" * 50)
            print("✓ Scraping completed successfully!")
            print(f"✓ Total jobs scraped: {len(all_jobs_data)}")
            print(f"✓ Pages processed: {page_number}")
            print(f"✓ Data saved to: {filename}")
            print(f"✓ File size: {os.path.getsize(filename) / 1024:.1f} KB")
        else:
            print("\n✗ No jobs data collected")
            
    except Exception as e:
        print(f"✗ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
                print("✓ Browser closed successfully")
            except:
                pass

if __name__ == "__main__":
    scrape_seek_jobs() 
