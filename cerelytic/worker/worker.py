import time
import signal
import sys
from redis_client import dequeue_analysis_job
from processor import process_bill

class Worker:
    def __init__(self):
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    def run(self):
        """Main worker loop"""
        print("Starting Cerelytic worker...")
        
        while self.running:
            try:
                # Wait for a job (blocking with timeout)
                job = dequeue_analysis_job()
                
                if job:
                    bill_id = job.get("bill_id")
                    file_url = job.get("file_url")
                    
                    print(f"Received job: bill_id={bill_id}, file_url={file_url}")
                    
                    # Process the bill
                    success = process_bill(bill_id, file_url)
                    
                    if success:
                        print(f"Successfully processed bill {bill_id}")
                    else:
                        print(f"Failed to process bill {bill_id}")
                else:
                    # Timeout occurred, check if we should continue running
                    print("No jobs available, continuing to wait...")
                    
            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(5)  # Wait before retrying
        
        print("Worker stopped")

if __name__ == "__main__":
    worker = Worker()
    worker.run()
