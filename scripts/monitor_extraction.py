"""
Monitor ERP Price Extraction Progress
Reports progress every interval
"""
import json
import time
import os
from datetime import datetime, timedelta

CHECKPOINT_FILE = "erp_extraction_checkpoint.json"
CHECK_INTERVAL = 300  # 5 minutes

def read_checkpoint():
    """Read current checkpoint"""
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def format_time(seconds):
    """Format seconds to readable time"""
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def main():
    print("="*80)
    print("ERP PRICE EXTRACTION MONITOR")
    print("="*80)
    print(f"Checking progress every {CHECK_INTERVAL/60:.0f} minutes")
    print("Press Ctrl+C to stop monitoring")
    print("="*80)

    last_page = 0

    while True:
        checkpoint = read_checkpoint()

        if checkpoint:
            stats = checkpoint['stats']
            page_number = checkpoint['page_number']

            # Calculate progress
            total_pages = 2797
            total_products = 69926
            progress_pct = (page_number / total_pages) * 100

            # Calculate speed and ETA
            elapsed = time.time() - stats['start_time']
            pages_per_sec = page_number / elapsed if elapsed > 0 else 0
            products_per_sec = stats['products_extracted'] / elapsed if elapsed > 0 else 0

            remaining_pages = total_pages - page_number
            eta_seconds = remaining_pages / pages_per_sec if pages_per_sec > 0 else 0

            # Calculate ETA time
            eta_time = datetime.now() + timedelta(seconds=eta_seconds)

            # Pages since last check
            pages_delta = page_number - last_page
            last_page = page_number

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] PROGRESS UPDATE")
            print("-" * 80)
            print(f"Pages:              {page_number:,} / {total_pages:,} ({progress_pct:.1f}%)")
            print(f"Products Extracted: {stats['products_extracted']:,} / {total_products:,}")
            print(f"Products w/ Prices: {stats['products_with_prices']:,}")
            print(f"Errors:             {stats['errors']}")
            print(f"\nPerformance:")
            print(f"  Elapsed Time:     {format_time(elapsed)}")
            print(f"  Speed:            {products_per_sec:.1f} products/sec")
            print(f"  Pages/Min:        {pages_per_sec * 60:.1f}")
            print(f"  Pages Last 5min:  {pages_delta}")
            print(f"\nEstimates:")
            print(f"  Time Remaining:   {format_time(eta_seconds)}")
            print(f"  Expected Done:    {eta_time.strftime('%I:%M %p')}")
            print("-" * 80)

            # Check if complete
            if page_number >= total_pages:
                print("\n[COMPLETE] Extraction finished!")
                print(f"Total products extracted: {stats['products_extracted']:,}")
                print(f"Total time: {format_time(elapsed)}")
                break

        else:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waiting for extraction to start...")

        # Wait for next check
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
