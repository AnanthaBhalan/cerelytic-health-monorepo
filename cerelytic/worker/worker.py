import time
import signal
from redis_client import dequeue_analysis_job
from processor import process_job


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
                    print(f"Received job: {job}")

                    # Process the job using new contract
                    success = process_job(job)

                    if success:
                        print(f"Successfully processed bill {job.get('bill_id')}")
                    else:
                        print(f"Failed to process bill {job.get('bill_id')}")

                else:
                    # Timeout occurred, loop again
                    time.sleep(1)

            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(5)

        print("Worker stopped")


if __name__ == "__main__":
    worker = Worker()
    worker.run()
