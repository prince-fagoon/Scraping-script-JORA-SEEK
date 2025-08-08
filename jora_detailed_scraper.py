import pandas as pd
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
import os

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
import os

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def scrape_job_details(driver, job_url):
    """
    Scrape specific information from individual job page using correct selectors
    """
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
        
        # Extract specific information using correct selectors from debug HTML
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
                import re
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
        
        # Job URL
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
            'job_url': job_url
        }

def scrape_jora_jobs():
    """
    Scraper using Selenium to control a real browser, ensuring JavaScript
    filters are applied correctly on Jora.com.
    Enhanced to click each job link and scrape detailed information.
    """
    
    # --- URL that includes the search query ---
    search_url = "https://au.jora.com/j?q=sponsorship+available&l=Australia"
    
    driver = None
    
    try:
        # Setup Chrome driver
        driver = setup_chrome_driver()
        
        all_jobs_data = []
        page_number = 1
        max_pages = 30  # Set how many pages you want to scrape

        print("Jora.com Detailed Selenium Scraper Initialized")
        print("=" * 50)
        
        driver.get(search_url)
        print(f"✓ Navigated to: {search_url}")

        while page_number <= max_pages:
            print(f"\nScraping page {page_number} for 'sponsorship available' jobs...")

            # --- CRUCIAL: Wait for the job cards to be loaded by JavaScript ---
            try:
                # Wait for job cards to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
                )
                print("✓ Job cards loaded successfully")
            except Exception as e:
                print(f"✗ Timeout waiting for job cards: {e}")
                # Try alternative selector
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article.job-card"))
                    )
                    print("✓ Job cards found with alternative selector")
                except:
                    print("✗ No job cards found. Ending scrape.")
                    break
            
            # Now that the page is loaded, we give the HTML to BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Try multiple selectors for job cards based on HTML analysis
            job_cards = soup.select('div.job-card.result')
            if not job_cards:
                job_cards = soup.select('article.job-card')
            if not job_cards:
                job_cards = soup.select('[data-job-card="true"]')

            if not job_cards:
                print("✓ No more job cards found. Ending scrape.")
                break

            print(f"✓ Found {len(job_cards)} jobs on page {page_number}.")

            # Parse job data with correct selectors based on debug HTML
            for i, card in enumerate(job_cards, 1):
                print(f"\nProcessing job {i}/{len(job_cards)} on page {page_number}")
                
                # Get job URL from the listing page using correct selector
                title_elem = card.select_one('h2.job-title a')
                job_url = ""
                if title_elem and title_elem.has_attr('href'):
                    href = title_elem['href']
                    job_url = "https://au.jora.com" + href if href.startswith('/') else href

                # Now scrape detailed information from the job page
                if job_url and job_url != "N/A":
                    print(f"  → Scraping detailed information...")
                    job_data = scrape_job_details(driver, job_url)
                    
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
                        'job_url': 'N/A'
                    }

                all_jobs_data.append(job_data)
                
                print(f"✓ Completed job {i}/{len(job_cards)}")
            
            # --- Handle Pagination with Selenium ---
            print(f"\nLooking for next page...")
            
            # First, go back to the search results page if we're on a job detail page
            current_url = driver.current_url
            if '/job/' in current_url:
                print("Currently on job detail page, returning to search results...")
                driver.get("https://au.jora.com/j?q=sponsorship+available&l=Australia")
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
                    
                    page_number += 1
                    time.sleep(random.uniform(2, 4))  # Wait for page to load
                    
                    # Wait for new job cards to load
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
                    )
                    print(f"✓ Successfully navigated to page {page_number}")
                    
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
                        page_number += 1
                        time.sleep(random.uniform(2, 4))
                        
                        # Wait for new job cards to load
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card.result"))
                        )
                        print(f"✓ Successfully navigated to page {page_number} via URL")
                        
                    except Exception as url_error:
                        print(f"Error with URL-based pagination: {url_error}")
                        print(f"Stopping at page {page_number}")
                        break
            else:
                print(f"No next button found or it's disabled. Stopping at page {page_number}")
                break
            
            if page_number > max_pages:
                print("Reached max pages limit.")
                break
            
    except Exception as e:
        print(f"✗ An error occurred during scraping: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
                print("✓ Browser closed successfully")
            except:
                pass
            
    if all_jobs_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jora_jobs_detailed_{timestamp}.csv"
        df = pd.DataFrame(all_jobs_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print("\n" + "=" * 50)
        print(f"✓ Detailed scraping complete. Data saved to {filename}")
        print(f"✓ Total jobs scraped: {len(all_jobs_data)}")
        print(f"✓ Pages processed: {page_number - 1}")
        print(f"✓ File size: {os.path.getsize(filename) / 1024:.1f} KB")
        print("\nSample of scraped data:")
        print(df.head())
        return filename
    else:
        print("\n✗ No job data was found or scraped.")
        return None

if __name__ == "__main__":
    result_file = scrape_jora_jobs()
    if result_file:
        print(f"\n✓ Process finished successfully.")
    else:
        print(f"\n✗ Process finished with errors or no data.") 
