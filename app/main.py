"""
Author: Rikitaro Suzuki
Created: May 6th, 2018
Modified: June 3rd,2018
Description: Program scrapes review content from Yelp for all TIC owned restaurants and uploads data to google sheets located in the TIC Google Drive.
"""
#file handles Oauth2.0 authentication and returns useable credentials to access Google Drive and Google Sheets APIs.
from credz import getCredentials
#file scrapes Yelp content 
from yelpScraper import requestReviewInfoUnOfficial
import datetime
# API and Oauthclient libraries
import httplib2
from apiclient.discovery import build

def main():
    #Key = spreadsheet name, value = unique yelp ID used to access Yelp website
    businessID = {"cha-an":"cha-an-new-york", "hasaki":"hasaki-new-york", "curry-ya_EastVillage":"curry-ya-new-york", 
                "curry-ya_MidTown": "curry-ya-new-york-3","curry-ya_Harlem": "curry-ya-new-york-2", "shabu-tatsu":"shabu-tatsu-east-village-new-york",
                "hi-collar": "hi-collar-new-york-2","otafuku":"otafuku-new-york-2", "rai-rai-Ken_EastVillage": "rai-rai-ken-new-york-7", 
                "rai-rai-Ken_Harlem": "rai-rai-ken-new-york-6", "yonekichi_EastVillage" : "yonekichi-new-york-6", "yonekichi_MidTown": "yonekichi-new-york-9", 
                "sakagura":"sakagura-new-york", "decibel": "sake-bar-decibel-new-york", "soba-ya": "soba-ya-new-york", "kiosku" : "kiosku-new-york-2"}
    yelpReviews = []
    #gets authorization and Credentials to use Google APIs Drive and Sheets
    credentials = getCredentials()
    #Point of interaction with google after being granted access to APIs
    DRIVE = build('drive','v3',http=credentials.authorize(httplib2.Http())) #Endpoint to access Drive APIs
    SHEETS = build('sheets','v4', http=credentials.authorize(httplib2.Http())) #Endpoint to access Sheets APIs
    spreadSheetIDList = spreadSheetIDGetter(DRIVE)
    #iterates through the 17 different restaurants
    for spreadSheetName,YelpID in businessID.items():
         #This function call returns a list of review data about the user and the review for a specific restaurant
        yelpReviews = requestReviewInfoUnOfficial(YelpID) #scrapes yelp pages to retrieve all reviews
        spreadSheetID = spreadSheetIDList[spreadSheetName] #uses drive API to retrieve unique google-sheets IDs
        spreadSheetUpdater(SHEETS, spreadSheetID, yelpReviews) #updates the spreadsheet with new reviews non-existent
        #makeCSVfile(reviews,key)
    
    print("DONE\n")

#Uploads valid review information to google spreadsheets if review does not exist already
def spreadSheetUpdater(SHEETS, spreadSheetID, reviews):
    #gets existing values from corresponding spreadsheet
     
    lastEnt = lastEntry(SHEETS,spreadSheetID) #gets the row number for last entry
    rangeName = ['A{0}:A'.format(lastEnt),'B{0}:B'.format(lastEnt),'H{0}:H'.format(lastEnt)]
    # Name = A:A Location = B:B Date = H:H 
    storedReviews = SHEETS.spreadsheets().values().batchGet(spreadsheetId = spreadSheetID, ranges = rangeName).execute()
    storedReviews = storedReviews.get('valueRanges')
    
    name = storedReviews[0]['values']
    location = storedReviews[1]['values']
    date = storedReviews[2]['values']
    latestEntry = [name[0][0],location[0][0],date[0][0]]

    latestEntryDate = datetime.datetime.strptime(latestEntry[2],"%Y-%m-%d")
    for x in range(len(reviews)-1,0,-1):
        #compares datetime objects only allowing most recent and not existing in the spreadsheet
        reviewsDate = datetime.datetime.strptime(reviews[x][7],"%Y-%m-%d")
        #
        if latestEntryDate > reviewsDate or (latestEntry[0] == reviews[x][0] and latestEntry[1] == reviews[x][1] and latestEntryDate == reviewsDate):#compares if last entry date is 
            print("passingThrouuugh\n")
            continue
        else:
            print("Updating this Cell:\n")
            spreadSheetInsert(SHEETS, spreadSheetID, reviews[x])
    return 0


def spreadSheetInsert(SHEETS, spreadSheetID, review):  
    range_ = "A2:I2"
    value_input_option = "USER_ENTERED"
    insert_data_option = "INSERT_ROWS"
    value_range_body = {
        "values":[review]
    }
    resp = SHEETS.spreadsheets().values().append(spreadsheetId=spreadSheetID, range=range_, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=value_range_body).execute()
    print(str(resp))

#Accesses Google Drive and finds all spreadsheet IDs located in 'Yelp Review Data' folder
#returns dictionary in format {name : spreadsheetId}
def spreadSheetIDGetter(DRIVE):
    spreadSheetDict = {}
    # '1AKYwNQrkZ-sxmeemmNFrhONaFBHnhcjH' is unique folder ID of 'Yelp Review Data'. Retrieves list of all restaurant spreadsheet names and IDs
    files = DRIVE.files().list(q="'1AKYwNQrkZ-sxmeemmNFrhONaFBHnhcjH' in parents and mimeType='application/vnd.google-apps.spreadsheet'").execute()
    for x in range(len(files['files'])):
        spreadSheetDict[files['files'][x]['name']] = files['files'][x]['id']
    return spreadSheetDict


def lastEntry(SHEETS, spreadSheetID):
    rangeTemp = 'A2:A'
    storedReviews = SHEETS.spreadsheets().values().batchGet(spreadsheetId = spreadSheetID, ranges = rangeTemp).execute()
    storedReviews = storedReviews.get('valueRanges')
    name = storedReviews[0]['values']
    return len(name) + 1



main()




#Returns valid reviews in same dictionary format as parameter with addition of 'category' and 'comment' as fields added to a single review
"""def userInterface(Revs): #Parameter is dictionary where key = businessName, Value = reviews
    category = ["service", "food/drink", "price", "cleanliness", "atmosphere", "other"]
    validReviews = {}
    for biz,reviews in Revs.items():
        validReviews[biz] = [] #saves businessName and instantiates a list for said key
        for rev in reviews:
            print("{0:*^40}".format(biz))
            validInput = False
            while not validInput:
                userInput = input("Enter S to submit or N to not Submit: ")
                if userInput.lower() == "s" or userInput.lower() == "n":
                    validInput = True

            if userInput == "s":
                validInput = False
                while not validInput:
                    catUser = input("Enter category or enter 'Cancel':\n- Service    - Food/Drink    - Price\n- Cleanliness    - Atmosphere    - Other\nEnter: ")
                    if catUser.lower() in category:
                        validInput = True
                        comment = input("Add a comment: ")
                        rev.append(catUser)
                        rev.append(comment)
                        validReviews[biz].append(rev)
                        print("Review Added!\n")
                    elif catUser.lower() == "cancel":
                        validInput = True
            else:
                print("")
            print("Next Review\n\n")
    return validReviews

    """