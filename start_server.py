import subprocess
import concurrent.futures

def start_main():
    subprocess.run(["python", "main.py"])

def start_server():
    subprocess.run(["python", "server.py"])

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(start_main)
        executor.submit(start_server)