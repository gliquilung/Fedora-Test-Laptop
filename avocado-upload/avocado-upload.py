#!/usr/bin/python3
import pyinotify
import pycurl, json
import zipfile, os, requests
import time

destinationServer = 'testuser@avocado.bewaar.me:/home/testuser'
zipFileDir = '/home/testuser/result-zips/'
watchDir = '/root/avocado/job-results/'
testName = ""
testDir = ""
maxWait = 10 # max seconds to wait for results.json to be generated

# Create a zipfile from given directory.
def zipDir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))

# This function willl look into the JSON file and returns:
# - outcome = Result of the test changed to ResultsDB standards.
# - testcase.name = Identifier test
# - link to the zip file that contains the complete result
def extractJSON(file, fileName):
    tryCount = 0
    global maxWait
    while not os.path.exists(file) and tryCount <= maxWait:
        time.sleep(1)
        tryCount += 1

    if not os.path.isfile(file):
        return #return for now

    with open(file) as data_file:
        data = json.load(data_file)
        for test in data['tests']:
            # Change the outcome to ResultsDB standards.
            outcome = 'NEEDS_INSPECTION'
            if test['status'] ==  'PASS':
                outcome = 'PASSED'
            if test['status'] ==  'FAIL':
                outcome = 'FAILED'
            if test['status'] ==  'ERROR':
                outcome = 'NEEDS_INSPECTION'
            if test['status'] ==  'SKIP':
                outcome = 'INFO'
            testcaseName = test['test']
            pushResults(outcome, testcaseName, fileName)

# Upload a zip file using scp.
def uploadZip(dest, zipFile):
    scpInstruction = "scp " + zipFile + " " + dest #TODO: this should be made to work
    #os.system(scpInstruction)

#Push values to ResultsDB
def pushResults(outcome, name, fileName):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    payload = {
            'outcome':outcome,
            'testcase': {
                "name": name,
                #TODO: not use ref_url, but use new object with new key/value pair
                "ref_url": destinationServer + fileName
                }
            }

    r = requests.post('http://localhost/resultsdb/api/v2.0/results',
            data=json.dumps(payload),
            headers=headers)

# Loop forever and handle events.
class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        global testDir, testName
        if 'job-' in event.name:
            testDir = event.pathname
            testName = event.name
        if 'latest' not in event.name:
            return
        filePath = testDir
        fileName = testName

        zipFilePath = zipFileDir + fileName + ".zip"

        # Creating zip file from results.
        zipf = zipfile.ZipFile(zipFilePath, 'w', zipfile.ZIP_DEFLATED)
        zipDir(filePath, zipf)
        zipf.close()

        # Uploading the zip file with scp.
        uploadZip(destinationServer, zipFilePath)

        # Extract results from json and push results to resultsdb
        extractJSON(filePath + "/results.json", fileName)

# Instanciate a new WatchManager (will be used to store watches).
wm = pyinotify.WatchManager()
# Create a mask for events, to make Inotify only trigger at creation or moves
mask = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO
# Set the manager to watch the correct dir and apply mask
wdd = wm.add_watch(watchDir, mask)
# Create EventHandler class
handler = EventHandler()
# Create a Notifier with the pynotify watch manager and set our custom class as the handler when changes occur
notifier = pyinotify.Notifier(wm, handler)
# Start looping on the watched dir(s) to trigger handler
notifier.loop()

