# keep_alive.py - A simple script to keep the container running
import time

while True:
    print("Container is running and waiting for commands." * 3, end="\r")
    print("Container is running and waiting for commands.." * 3, end="\r")
    print("Container is running and waiting for commands..." * 3, end="\r")    
    time.sleep(5)  # Adjust the interval as needed
