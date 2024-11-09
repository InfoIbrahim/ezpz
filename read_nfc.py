import sys
import time
import json
from smartcard.System import readers
from smartcard.util import toHexString

import subprocess

# Function to read NFC data (example, modify according to your actual NFC scanner)
def read_nfc_tag():
    # Simulate reading NFC tag
    print("Scanning NFC tag...")
    nfc_data = "1"  # Example IHB number from scanned NFC (replace with actual NFC scanning code)

    # Now run the Node.js script that processes the NFC data
    run_node_script(nfc_data)

def run_node_script(IHB_number):
    try:
        # Call the Node.js script using subprocess
        result = subprocess.run(['node', 'processNFC.js', IHB_number], capture_output=True, text=True)

        # Output the results from the Node.js script
        print("Node.js Output:")
        print(result.stdout)  # Print whatever Node.js script outputs

        if result.stderr:
            print("Error:", result.stderr)
    except Exception as e:
        print(f"Error running Node.js script: {e}")

# Call the function to simulate reading an NFC tag
read_nfc_tag()

# Path to the JSON file where data will be logged
data_file = 'nfc_data.json'

# Initialize or load existing data
def load_data():
    try:
        with open(data_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # If the file doesn't exist or is empty, return an empty list

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)

# List the available readers
r = readers()
if len(r) == 0:
    print("No readers found. Please make sure the ACR122U is connected.")
    sys.exit()

# Select the first reader
reader = r[0]
print(f"Using reader: {reader}")

# Connect to the reader
connection = reader.createConnection()

# Function to check for card presence
def check_for_card():
    try:
        connection.connect()
        return True
    except Exception as e:
        print(f"Error connecting to card: {e}")
        return False

# Load existing data from nfc_data.json
logs = load_data()

# Create a mapping of UID to IHB_number number
uid_to_IHB_number = {entry['uid']: entry['IHB_number'] for entry in logs if 'IHB_number' in entry}

# Determine the next IHB_number number (starting from 1)
next_IHB_number = max([entry['IHB_number'] for entry in logs if 'IHB_number' in entry], default=0) + 1

print("Waiting for NFC tag...")

while True:
    if check_for_card():
        try:
            # Card detected, attempt to read it
            atr = connection.getATR()
            print("Card detected! ATR:", toHexString(atr))

            # Send a command to get the UID (0xCA is the standard command for reading UID)
            response, sw1, sw2 = connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
            uid = toHexString(response)
            print(f"UID of the card: {uid}")

            # Check if the UID already has an IHB_number number
            if uid not in uid_to_IHB_number:
                # Assign the next IHB_number number to this UID
                IHB_number_number = next_IHB_number
                next_IHB_number += 1
                print(f"Assigning IHB_number number {IHB_number_number} to UID {uid}")
                
                # Record the UID with the assigned IHB_number number in the logs
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())  # Timestamp for when the tag was read
                log_entry = {
                    "uid": uid,
                    "timestamp": timestamp,
                    "IHB_number": IHB_number_number
                }
                logs.append(log_entry)

                # Update the UID-to-IHB_number mapping
                uid_to_IHB_number[uid] = IHB_number_number

                # Save the updated data to the JSON file
                save_data(logs)

            else:
                # If UID already has an IHB_number, print it
                print(f"UID {uid} already has an IHB_number number: {uid_to_IHB_number[uid]}")

            print("Card read successfully.")
            
            # Exit the loop after processing the card
            break

        except Exception as e:
            print(f"Error during card read: {e}")
            break
    else:
        print("No card detected. Please place a card on the reader.")
        time.sleep(1)
