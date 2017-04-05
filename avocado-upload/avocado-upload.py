#!/usr/bin/python3
import pyinotify
import pycurl, json
import time
import zipfile,os,requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen

filePath = '/root/avocado/job-results/latest'
destinationServer = 'gliquilung@avocado.bewaar.me:/home/'

#Code to create a zipfile
def zipDir(path, ziph,fn):
    print("Creating Zipfile: "+ fn)
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))


#This function willl look into the JSON file and returns
#outcome = Result of the test
#testcase.name = Identifier test
#link to the zip that contains the complete package
def extractJSON(file,fileName):
    print("extractJSON function called")
    with open(file) as data_file:
        data = json.load(data_file)
        for test in data ['tests']:
            if test['status'] ==  'PASS':
                outcome = 'PASSED'
            else:
                outcome = test['status']
            testcaseName = test['id']
            print("Writing test: " +testcaseName + " with status " + outcome)
            pushResults(outcome,testcaseName,fileName)

#Code to upload a zip file using SCP
def uploadZip(dest, zipFile):
    print("Upload Zip funcion called")
    scpInstruction = "scp " + zipFile + " " + dest
    os.system(scpInstruction)

#Push values to ResultsDB
def pushResults(outcome,name,fileName):
    print("Pushing results")
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    
    payload = {
            'outcome':outcome,
            'testcase': {
                "name": name,
                "ref_url" :destinationServer+fileName
                }
            }

    r = requests.post('http://localhost/resultsdb/api/v2.0/results',
            data=json.dumps(payload),
            headers=headers)
    print("Testcase: %s" % name)
    print(r.text)


#Pynotify Code
# Instanciate a new WatchManager (will be used to store watches).

wm = pyinotify.WatchManager()
# Associate this WatchManager with a Notifier (will be used to report and
# process events).
#notifier = pyinotify.Notifier(wm)

# Add a new watch on /tmp for ALL_EVENTS.
mask=pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO

#wm.update_watch(wdd['/home/nick'], mask)
#wm.update_watch(42, mask=mask)
# Loop forever and handle events.
class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print("Creating:", event.pathname)
        #Creating Zip file
        fileName = 'test-'+ time.strftime("%Y%m%d%H%M")
        zipf = zipfile.ZipFile(fileName + ".zip", 'w', zipfile.ZIP_DEFLATED)
        zipDir(filePath, zipf,fileName)
        zipf.close()
        #Extract results from json and push results to resultsdb
        extractJSON(filePath + "/results.json",fileName)
        uploadZip(destinationServer,fileName)

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd=wm.add_watch('/root/avocado/job-results', mask)

notifier.loop()

