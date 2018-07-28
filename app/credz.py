"""
File contains functions 
"""
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
import argparse
import httplib2
from apiclient.discovery import build

#handles OAuth2.0 and defines SCOPES for appropriate credentials , returns credentials
def getCredentials():
    #Google API Oauth2 client access
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]
    CLIENT_SECRET= 'client_secret.json'
    #Must get access to Google Drive and Google Sheets APIs through Oauth2 authentication.
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    flags = parser.parse_args()
    store = Storage('credentials.json') #Checks if credentials previously stored
    credentials = store.get() #gets credentials if already exist
    if not credentials or credentials.invalid: #will enter branch if no credentials exist
        #Flow is created using client_secret.json to communicate with API
        flow = flow_from_clientsecrets(CLIENT_SECRET,
                                scope=SCOPES,
                                redirect_uri='http://google.com')
        credentials = tools.run_flow(flow, store, flags) #tools.run_flow retrieves credentials and stores them
    return credentials