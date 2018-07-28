from __future__ import print_function
from apiclient.discovery import build
import httplib2
# Setup Oauthclient
import argparse
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
 
def main():
    flag = True
    """Google API Oauth2 client access"""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]
    CLIENT_SECRET= 'client_secret.json'
    #Must connect to google drive to identify file IDs for manipulation
    # Authorize server-to-server interactions from Google Compute Engine.
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    flags = parser.parse_args()
    store = Storage('credentials.json')
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = flow_from_clientsecrets(CLIENT_SECRET,
                                scope=SCOPES,
                                redirect_uri='http://google.com')
        credentials = tools.run_flow(flow, store, flags)
        #store = Storage('credentials.json')
        #store.put(credentials)

    DRIVE = build('drive','v3',http=credentials.authorize(httplib2.Http()))
    while flag:
        print("Enter Q to quit")
        userInput = input("Enter Query: ")
        if userInput == "Q":
            exit(0)
        driveQuery = queryDrive(DRIVE,userInput)
        print("Query: "+str(driveQuery)+"\n")


def queryDrive(DRIVE, query):
    file = DRIVE.files().list(q="{0}".format(query)).execute()
    return file
main()