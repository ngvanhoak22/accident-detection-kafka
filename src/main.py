from producer import run_producer
from consumer import run_consumer
import threading

def main():
    # Chạy producer và consumer trong các thread riêng
    producer_thread = threading.Thread(target=run_producer)
    consumer_thread = threading.Thread(target=run_consumer)
    
    producer_thread.start()
    consumer_thread.start()
    
    producer_thread.join()
    consumer_thread.join()

if __name__ == "__main__":
    main()