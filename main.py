#!/usr/bin/env python3
"""
Main Entry Point for Job Portal Scraping
Combines data from both Jora and Seek portals into a single CSV file
"""

import pandas as pd
from datetime import datetime
import os
from jora_crawler import JoraCrawler
from seek_crawler import SeekCrawler


def main():
    """Main function to run both crawlers and combine results"""
    print("Job Portal Scraper - Combined Edition")
    print("=" * 60)
    print("This will scrape both Jora and Seek portals for sponsorship available jobs")
    print("All data will be combined into a single job_lists.csv file")
    print("=" * 60)
    
    # Initialize crawlers
    jora_crawler = JoraCrawler()
    seek_crawler = SeekCrawler()
    
    all_jobs_data = []
    
    # Scrape Jora
    print("\n" + "=" * 60)
    print("STARTING JORA SCRAPING")
    print("=" * 60)
    try:
        jora_jobs = jora_crawler.scrape_jobs(max_pages=34)
        if jora_jobs:
            all_jobs_data.extend(jora_jobs)
            print(f"✓ Jora scraping completed successfully. Jobs collected: {len(jora_jobs)}")
        else:
            print("✗ Jora scraping failed or returned no data")
    except Exception as e:
        print(f"✗ Error during Jora scraping: {e}")
    
    # Scrape Seek
    print("\n" + "=" * 60)
    print("STARTING SEEK SCRAPING")
    print("=" * 60)
    try:
        seek_jobs = seek_crawler.scrape_jobs(max_pages=25)
        if seek_jobs:
            all_jobs_data.extend(seek_jobs)
            print(f"✓ Seek scraping completed successfully. Jobs collected: {len(seek_jobs)}")
        else:
            print("✗ Seek scraping failed or returned no data")
    except Exception as e:
        print(f"✗ Error during Seek scraping: {e}")
    
    # Combine and save data
    if all_jobs_data:
        print("\n" + "=" * 60)
        print("COMBINING AND SAVING DATA")
        print("=" * 60)
        
        # Create DataFrame
        df = pd.DataFrame(all_jobs_data)
        
        # Ensure all required columns exist
        required_columns = ['title', 'company', 'location', 'salary', 'description', 'job_url', 'source']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 'N/A'
        
        # Reorder columns to put source first
        column_order = ['source'] + [col for col in df.columns if col != 'source']
        df = df[column_order]
        
        # Save to CSV
        output_filename = "job_lists.csv"
        df.to_csv(output_filename, index=False, encoding='utf-8')
        
        # Print summary
        print(f"✓ Combined data saved to: {output_filename}")
        print(f"✓ Total jobs collected: {len(all_jobs_data)}")
        print(f"✓ File size: {os.path.getsize(output_filename) / 1024:.1f} KB")
        
        # Print breakdown by source
        source_counts = df['source'].value_counts()
        print("\nJobs by source:")
        for source, count in source_counts.items():
            print(f"  - {source}: {count} jobs")
        

        
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    else:
        print("\n✗ No job data was collected from either portal.")
        print("Please check the individual scraper outputs above for errors.")


if __name__ == "__main__":
    main()
