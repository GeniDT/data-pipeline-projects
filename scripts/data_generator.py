# Python script to generate continuous CSV event data.

# Import all necessary libraries
import csv
import random
from datetime import datetime
from faker import Faker
import time
import os
import signal
import sys

# Initialize Faker
fake = Faker()

# Global variables
product_ids = [f'product_{i}' for i in range(1, 21)]
event_types = ["view", "purchase"]
output_directory = 'data_stream'

def generate_event():
    timestamp = datetime.now().isoformat()
    user_id = fake.uuid4()
    product_id = random.choice(product_ids)
    event_type = random.choice(event_types)
    return [timestamp, user_id, product_id, event_type]

def generate_and_save_batch(file_path, num_events):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'user_id', 'product_id', 'event_type'])
        for _ in range(num_events):
            event = generate_event()
            writer.writerow(event)
    print(f"Generated {num_events} events in {file_path}")

def signal_handler(sig, frame):
    print("\nStopping continuous data generation...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler for graceful Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Create output directory
    os.makedirs(output_directory, exist_ok=True)

    # Continuous generation
    batch_size = 10  # Number of events per file
    interval = 2     # Seconds between files
    file_counter = 1

    print("Starting continuous data generation (press Ctrl+C to stop)...")
    while True:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_directory, f'events_{timestamp}_{file_counter}.csv')
        
        # Generate and save batch
        generate_and_save_batch(filename, batch_size)
        file_counter += 1
        
        # Wait before generating next file
        time.sleep(interval)