import pandas as pd
from faker import Faker
import os
import time
import logging
import random
from datetime import datetime
import pickle

# Configure logging
logging.basicConfig(
    filename='/logs/data_generator.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

def get_next_event_id(counter_file='/csv-data/event_id_counter.pkl'):
    """Read and increment the event_id counter from a file."""
    try:
        if os.path.exists(counter_file):
            with open(counter_file, 'rb') as f:
                counter = pickle.load(f)
        else:
            counter = 0
        counter += 1
        with open(counter_file, 'wb') as f:
            pickle.dump(counter, f)
        logger.info(f"Generated event_id: {counter}")
        return counter
    except Exception as e:
        logger.error(f"Failed to manage event_id counter: {str(e)}")
        raise e

def generate_data(output_dir, num_records=100):
    try:
        logger.info(f"Starting data generation for {num_records} records")
        fake = Faker()
        actions = ['view', 'click', 'purchase', 'add_to_cart']
        
        data = []
        for _ in range(num_records):
            event_id = get_next_event_id()
            user_id = fake.uuid4()
            action = random.choice(actions)
            product_id = random.randint(1, 1000)
            timestamp = datetime.now()
            created_at = timestamp
            
            data.append({
                'event_id': event_id,
                'user_id': user_id,
                'action': action,
                'product_id': product_id,
                'timestamp': timestamp,
                'created_at': created_at
            })
        
        df = pd.DataFrame(data)
        filename = os.path.join(output_dir, f'events_{int(time.time())}.csv')
        df.to_csv(filename, index=False)
        logger.info(f"Generated {num_records} records in {filename} with event_ids {data[0]['event_id']} to {data[-1]['event_id']}")
    except Exception as e:
        logger.error(f"Data generation failed: {str(e)}")
        raise e

if __name__ == "__main__":
    output_dir = os.getenv('CSV_OUTPUT_DIR', '/csv-data')
    logger.info(f"Starting data generator with output_dir: {output_dir}")
    try:
        while True:
            generate_data(output_dir)
            time.sleep(5)
    except Exception as e:
        logger.error(f"Data generator loop failed: {str(e)}")
        raise e