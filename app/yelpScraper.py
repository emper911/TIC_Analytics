import datetime
#Webscraper libraries
import requests
import textwrap
from bs4 import BeautifulSoup
from lxml import html


def requestReviewInfoUnOfficial(businessID):
    """Function performs webscraping of yelp pages looking for review data of an individual restuaraunt and returns a list of all reviews. Function is named unofficial due to there being no access via Yelp's API."""
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


def getPageNumber(soup):
    """Function gets number of review pages for each restaurant. parameter is the beautiful soup parsed html page, returns number of pages to be used"""
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




def makeCSVfile(reviews, businessName):
    """Makes a csv file with list of review info. Function currently not in use. Was used to initialize database and upload to spreadsheets."""
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
