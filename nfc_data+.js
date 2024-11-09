const fs = require('fs');

// Get the IHB number from command line arguments
const ihbNumber = process.argv[2];  // IHB number passed from Python script

// Function to load JSON data from a file
function loadJSONFile(filePath) {
    return new Promise((resolve, reject) => {
        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) reject(err);
            else resolve(JSON.parse(data));
        });
    });
}

// Function to save updated data back to a new JSON file
function saveJSONFile(filePath, data) {
    return new Promise((resolve, reject) => {
        fs.writeFile(filePath, JSON.stringify(data, null, 4), 'utf8', (err) => {
            if (err) reject(err);
            else resolve();
        });
    });
}

// Function to get data for a given IHB number from data.json
async function getIHBData(ihbNumber) {
    try {
        const data = await loadJSONFile('./data.json');

        // Find IHB ownership and transactions related to the IHB number
        const ownershipData = [];
        const transactionHistory = [];

        // Loop through users and their IHB ownership and transactions
        data.users.forEach(user => {
            user.IHB_ownership.forEach(ownership => {
                if (ownership.IHB_number === parseInt(ihbNumber)) {
                    ownershipData.push({
                        client_id: user.client_id,
                        IHB_number: ownership.IHB_number,
                        percentage: ownership.percentage
                    });
                }
            });

            user.transaction_history.forEach(transaction => {
                if (transaction.IHB_number === parseInt(ihbNumber)) {
                    transactionHistory.push(transaction);
                }
            });
        });

        return {
            ownershipData,
            transactionHistory
        };

    } catch (error) {
        console.error('Error loading or processing data.json:', error);
    }
}

// Function to process an NFC scan and save the data to nfc_data+.json
async function processNFCSCAN() {
    try {
        // Load the existing NFC data from nfc_data.json
        const nfcData = await loadJSONFile('./nfc_data.json');
        
        // Get details for the scanned IHB number
        const ihbDetails = await getIHBData(ihbNumber);

        // Find the corresponding NFC entry to update
        const nfcEntry = nfcData.find(entry => entry.IHB_number === parseInt(ihbNumber));

        if (nfcEntry) {
            // Add ownership and transaction data to the NFC entry
            nfcEntry.ownership_data = ihbDetails.ownershipData;
            nfcEntry.transaction_history = ihbDetails.transactionHistory;

            // Save the updated NFC data to a new file: nfc_data+.json
            await saveJSONFile('./nfc_data+.json', nfcData);
            console.log(`Successfully updated nfc_data+.json with IHB number ${ihbNumber}`);
        } else {
            console.log(`No NFC entry found for IHB number ${ihbNumber}`);
        }

    } catch (error) {
        console.error('Error processing NFC scan:', error);
    }
}

// Trigger NFC scan processing
processNFCSCAN();