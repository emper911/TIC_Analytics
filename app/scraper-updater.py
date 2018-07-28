"""
Author: Rikitaro Suzuki
Created: May 6th, 2018
Modified: June 3rd,2018
Description: Program scrapes review content from Yelp for all TIC owned restaurants and uploads data to google sheets located in the TIC Google Drive.
"""
import datetime
#Webscraper libraries
import requests
import textwrap
from bs4 import BeautifulSoup
from lxml import html
# API and Oauthclient libraries
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
import argparse
import httplib2
from apiclient.discovery import build

def main():
    #Key = spreadsheet name, value = unique yelp ID used to access Yelp website
    businessID = {"cha-an":"cha-an-new-york", "hasaki":"hasaki-new-york", "curry-ya_EastVillage":"curry-ya-new-york", 
                "curry-ya_MidTown": "curry-ya-new-york-3","curry-ya_Harlem": "curry-ya-new-york-2", "shabu-tatsu":"shabu-tatsu-east-village-new-york",
                "hi-collar": "hi-collar-new-york-2","otafuku":"otafuku-new-york-2", "rai-rai-Ken_EastVillage": "rai-rai-ken-new-york-7", 
                "rai-rai-Ken_Harlem": "rai-rai-ken-new-york-6", "yonekichi_EastVillage" : "yonekichi-new-york-6", "yonekichi_MidTown": "yonekichi-new-york-9", 
                "sakagura":"sakagura-new-york", "decibel": "sake-bar-decibel-new-york", "soba-ya": "soba-ya-new-york", "kiosku" : "kiosku-new-york-2"}
    reviews = []
    #gets authorization and Credentials to use Google APIs Drive and Sheets
    credentials = getCredentials()
    #Point of interaction with google after being granted access to APIs
    DRIVE = build('drive','v3',http=credentials.authorize(httplib2.Http())) #Endpoint to access Drive APIs
    SHEETS = build('sheets','v4', http=credentials.authorize(httplib2.Http())) #Endpoint to access Sheets APIs
    spreadSheetIDList = spreadSheetIDGetter(DRIVE)
    #iterates through the 17 different restaurants
    for spreadSheetName,YelpID in businessID.items():
         #This function call returns a list of review data about the user and the review for a specific restaurant
        reviews = requestReviewInfoUnOfficial(YelpID) #scrapes yelp pages to retrieve all reviews
        spreadSheetID = spreadSheetIDList[spreadSheetName] #uses drive API to retrieve unique google-sheets IDs
        spreadSheetUpdater(SHEETS, spreadSheetID, reviews) #updates the spreadsheet with new reviews non-existent
        #makeCSVfile(reviews,key)
    

    
    print("DONE\n")

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

#Function performs webscraping of yelp pages looking for review data for an individual restuaraunt and returns a list of all reviews
def requestReviewInfoUnOfficial(businessID):
    reviewList = []
    #7 variables recorded from each review
    #reviewList.append(["name","location","friend-count","review-count","photo-count", "elite-year", "rating","date","comment"])
    #url for first page
    url = "https://www.yelp.com/biz/{0}?sort_by=date_desc&start=0".format(businessID)
    page = requests.get(url)
    #Uses beautifulsoup library to retrieve page and parsers html tree
    soup = BeautifulSoup(page.content, 'html.parser')
    #finds number of review pages to iterate through for the individual restaurant 
    pageNum = getPageNumber(soup)
    print("{0} Number of pages: {1}".format(businessID,pageNum))
    #increments of 20, each review page for a restaurant contains 20 reviews per a page
    for i in range(0,40,20): #currently only looking at first 2 pages since database already exists and program now justs updates. 
        print(i)
        if i != 0: #for all pages that follow, must update soup
            url = "https://www.yelp.com/biz/{0}?sort_by=date_desc&start={1}".format(businessID,i)
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')

        #finds div with list of reviews, list is further organized as an array of divs 
        reviewers = soup.find_all('div', class_= "review review--with-sidebar")
        numReviews = len(reviewers)
        
        for i in range(numReviews):#iterates through list of reviews organized by divs
            review = getSingleReview(reviewers[i])
            reviewList.append(review)
          
    return reviewList

#Parameter is beautiful soup parsed version of Yelp page, 
def getPageNumber(soup):
    """parameter is beautiful soup parsed html page, returns number of pages to be used"""
    pageNum = 0
    pageNum = soup.find('div',class_="page-of-pages arrange_unit arrange_unit--fill").text
    pageNum = "".join([pageNum[x] for x in range(len(pageNum)) if pageNum[x] not in [" ","\n"]])#If printed should be eg. "Page 1 of 75"
    pageNum = pageNum[len(pageNum)-3:]
    pageNum = "".join([pageNum[x] for x in range(len(pageNum)) if pageNum[x].isnumeric() == True])
    pageNum = int(pageNum) * 20 #multiples by 20 for URL formatting
    return pageNum

def getSingleReview(review):
    """parameter is a single review, sorts information and returns a list with variables: [name,location,friend-count,review-count,photo-count,elite-year,rating,date,comment]"""
    #Inside each review div contains information about the reviewer and information about the review itself.
    #Personal Details
    sidebarUserDetail = review.find('div',class_="media-story")
    #Review Details
    mainReviewDetail = review.find('div', class_= "review-content")
    
    #Personal Details
    userName = sidebarUserDetail.find('a', id="dropdown_user-name")
    if userName == None: #rare case if data came from qype, or other imported secondary datasets
        userName = "NA"
    else:
        userName = userName.text
    userLocation = sidebarUserDetail.find('li', class_="user-location responsive-hidden-small")
    if userLocation == None: #may never happen, safety first
        userLocation = "NA"
    else:
        userLocation = userLocation.b.text

    #friend count, review count, photo count and user elite variables highly dependent on user and may not exist. If not found will place a zero as placeholder
    userFriendsCount = sidebarUserDetail.find('li', class_="friend-count responsive-small-display-inline-block")
    if userFriendsCount == None:
        userFriendsCount = 0
    else:
        userFriendsCount = userFriendsCount.b.text
    userReviewsCount = sidebarUserDetail.find('li', class_="review-count responsive-small-display-inline-block")
    if userReviewsCount == None:
        userReviewsCount = 0
    else:
        userReviewsCount = userReviewsCount.b.text
    userPhotoCount = sidebarUserDetail.find('li', class_="photo-count responsive-small-display-inline-block")
    if userPhotoCount == None:
        userPhotoCount = 0
    else:
        userPhotoCount = userPhotoCount.b.text
    userElite = sidebarUserDetail.find("li", class_="is-elite responsive-small-display-inline-block")
    if userElite != None:
        userElite = userElite.a.text
        userElite = int(userElite[len(userElite)-2:])
    else:
        userElite = -1

    #Review Details
    userRating = mainReviewDetail.find('div', class_="i-stars")['title']
    userRating = userRating[0]
    #Date of Review and formatting to: YYYY-MM-DD
    userDate = mainReviewDetail.find('span', class_="rating-qualifier").text
    userDate = "".join([userDate[x] for x in range(len(userDate)) if userDate[x] not in [" ","\n"] and (userDate[x].isnumeric() or userDate[x] == "/")])
    userDate = userDate[-4:] + "-" + userDate[0:-5]
    userDate = userDate.replace("/","-")
    d = datetime.datetime.strptime(userDate,"%Y-%m-%d") #formats date to YYYY-MM-DD using datetime library
    userDate = d.strftime("%Y-%m-%d")
    #retrieved review comment and clean information of non-letter characters
    userComment = mainReviewDetail.p.text
    userComment = "".join([userComment[x] for x in range(len(userComment)) if userComment[x] not in [",",":",";","\"t"]])
    #return as list
    return [userName, userLocation, userFriendsCount, userReviewsCount, userPhotoCount, userElite, userRating, userDate, userComment]



#Makes a csv file with list of review info
#function currently not in use. Was used to initialize database and upload to spreadsheets. 
def makeCSVfile(reviews, businessName):

    fp = open("{0}_Yelp.csv".format(businessName),"w")
    if fp == None:
        print("Error opening file")
        exit(1)
    numReviews = len(reviews)
    for y in range(numReviews):
        numY = len(reviews[y])
        for x in range(numY - 1):
            fp.write(str(reviews[y][x])+"}")
        fp.write(str(reviews[y][x + 1])+"\n")
    fp.close()    


#Uploads valid review information to google spreadsheets if review does not exist already
def spreadSheetUpdater(SHEETS, spreadSheetID, reviews):
    #gets existing values from corresponding spreadsheet
    # Name = A:A Location = B:B Date = H:H  
    lastEnt = lastEntry(SHEETS,spreadSheetID) #gets the row number for last entry
    rangeName = ['A{0}:A'.format(lastEnt),'D{0}:D'.format(lastEnt),'H{0}:H'.format(lastEnt)]
    storedReviews = SHEETS.spreadsheets().values().batchGet(spreadsheetId = spreadSheetID, ranges = rangeName).execute()
    storedReviews = storedReviews.get('valueRanges')
    
    name = storedReviews[0]['values']
    reviewCount = storedReviews[1]['values']
    date = storedReviews[2]['values']
    latestEntry = [name[0][0],reviewCount[0][0],date[0][0]]
    
    for x in range(len(reviews)-1,0,-1):
        #compares datetime objects only allowing most recent and not existing in the spreadsheet
        latestEntryD = datetime.datetime.strptime(latestEntry[2],"%Y-%m-%d")
        reviewsDate = datetime.datetime.strptime(reviews[x][7],"%Y-%m-%d")
        #
        if latestEntryD > reviewsDate or (latestEntry[0] == reviews[x][0] and latestEntry[1] == reviews[x][3]):
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