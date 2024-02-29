import os
import argparse
import threading
from queue import Queue
import chardet  # For character encoding detection

# Constants
DEFAULT_THREADS = 4  # Default number of threads if not specified

# Function to process each file
def process_file(file_path, whitelist, blacklist, output_file, errors_log, lock):
    try:
        # Detect file's encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        # Read file content based on detected encoding
        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
            if file_path.endswith(('.exe', '.dll', '.bin', '.so')):  # Non-human-readable files
                content = file.read()
                for index, char in enumerate(content):
                    if char.isprintable():
                        # Extract string from binary content (this might need refinement based on actual binary structure)
                        string = ''.join(content[index:index+3])  # Adjust based on how we define a 'string' in binary
                        if string not in blacklist:
                            with lock:
                                with open(output_file, 'a', encoding='utf-8') as out:
                                    out.write(f"{file_path}:{string}:{index}\n")
            else:  # Human-readable files
                for line_num, line in enumerate(file, 1):
                    words = line.strip().split()
                    for word in words:
                        if len(word) >= 3 and word not in blacklist:
                            if not whitelist or word in whitelist:
                                with lock:
                                    with open(output_file, 'a', encoding='utf-8') as out:
                                        out.write(f"{file_path}:{word}:{line_num}\n")
    except Exception as e:
        with lock:
            with open(errors_log, 'a', encoding='utf-8') as log:
                log.write(f"Error processing file {file_path}: {e}\n")

# Thread worker function
def worker(file_queue, whitelist, blacklist, output_file, errors_log, lock):
    while True:
        file_path = file_queue.get()
        if file_path is None:
            break  # Exit loop if None is encountered
        process_file(file_path, whitelist, blacklist, output_file, errors_log, lock)
        file_queue.task_done()

# Main function to setup and execute the script
def main(target_path, whitelist_path, blacklist_path, output_file, recursive, num_threads):
    # Load whitelist and blacklist
    with open(whitelist_path, 'r', encoding='utf-8') as file:
        whitelist = set(file.read().splitlines())
    with open(blacklist_path, 'r', encoding='utf-8') as file:
        blacklist = set(file.read().splitlines())

    # Prepare threading
    file_queue = Queue()
    lock = threading.Lock()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(file_queue, whitelist, blacklist, output_file, "errors.log", lock))
        t.start()
        threads.append(t)

    # Walk through the directory
    if os.path.isdir(target_path):
        for root, dirs, files in os.walk(target_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_queue.put(file_path)
            if not recursive:
                break  # Non-recursive, break after first directory
    else:
        file_queue.put(target_path)  # Single file mode

    # Block until all tasks are done
    file_queue.join()

    # Stop workers
    for _ in range(num_threads):
        file_queue.put(None)
    for t in threads:
        t.join()

# Command-line argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find, catalog, and review strings in files.")
    parser.add_argument("target_path", help="Target file or directory path")
    parser.add_argument("whitelist_path", help="Path to the whitelist file")
    parser.add_argument("blacklist_path", help="Path to the blacklist file")
    parser.add_argument("output_file", help="Path to the output file for results")
    parser.add_argument("--recursive", action='store_true', help="Operate recursively")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS, help="Number of threads to use")
    args = parser.parse_args()

    main(args.target_path, args.whitelist_path, args.blacklist_path, args.output_file, args.recursive, args.threads)
