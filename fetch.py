#!python3
###############################################################################
# fetch.py - Data fetching/scraping stuff for LCSA 
# jamesj223

###############################################################################
# Imports

import requests, bs4, re, time

from database import dbQuery

###############################################################################
# User Input / Config

debug = False

verbose = False

# Include Mid Year / Winter
includeMidYearComps = False

# Include T20
includeT20Comps = False

# Include Womens Only Comps
includeWomensOnlyComps = False

# Inclue Veterans Comps 
includeVeteransComps = False

# Include Juniors Comps
includeJuniorsComps = False

# TODO Add something to the template(s) listing which comps were included/excluded from data

# Sleep Duration after each HTTP request
sleepDuration = 1

# Placeholder value for missing information
unknown = "Unknown"

###############################################################################
# Functions

# Fetches a url using requests and then extracts the 'soup' for the loaded page
def getSoup(url):

    attempts = 0
    while attempts <= 5:
        try:
            a = url
            if debug:
                    print(('Downloading page %s' % url))

            res = requests.get(a)
            res.raise_for_status()
            if debug:
                print("Returned status code: " + str( res ))
            soup = bs4.BeautifulSoup(res.text, "html.parser")
            return soup

        except Exception:
            #sleep for a second then try again
            time.sleep(1)
            attempts += 1


# Fetches player info, and populates the PlayerInfo table
def fetchPlayerInfo(playerID):

    soup = getSoup( "www.fake-cricket-stats-website.com" )

    # Get Player Name
    fullName = soup.select("#selector")[0].text
    
    firstName = fullName.split(" ", 1)[0]
    lastName = fullName.split(" ", 1)[1]

    if debug:
        print("First Name: " + firstName)
        print("Last Name: " + lastName)

    # Get Number of Matches Played
    numMatches = int(soup.select("#selector")[0].text)

    if debug:
        print("Matches played: " + str(numMatches))

    # Insert into PlayerInfo table
    playerDB = "Player Databases/" + str(playerID) + ".db"
            
    query = "INSERT OR IGNORE INTO PlayerInfo (PlayerID, FirstName, LastName, NumMatches) VALUES (?,?,?,?)"
    values = (playerID, firstName, lastName, numMatches)
    dbQuery(playerDB,query,values)

    query = "UPDATE PlayerInfo SET NumMatches=? WHERE PlayerID = ?"
    values = (numMatches, playerID)
    dbQuery(playerDB,query,values)

    if debug:
        print("PlayerInfo Table Updated.")

    # Get clubs
    clubList = soup.select('selector')

    if debug:
        print(clubList)

    for thing in clubList:
        if debug:
            print(thing.contents)
        query = "INSERT OR IGNORE INTO Clubs (ClubID, ClubName) VALUES (?,?)"
        values = ( thing['value'], thing.contents[0].get_text(strip=True).replace("'","") )
        dbQuery(playerDB,query,values)

# Returns the list of clubIDs for clubs that a player has played for
def getClubList(playerID):
    if debug:
        print("getClubList("+str(playerID)+")")

    playerDB = "Player Databases/" + str(playerID) + ".db"

    clubList = dbQuery(playerDB, "SELECT * from Clubs")

    return clubList


# Fetches the list of all of the season a player has played for a club
def getSeasonList(playerID):#, clubID):

    if debug:
        print("getSeasonList("+str(playerID)+")")

    seasonList = []

    clubList = getClubList(playerID)

    for club in clubList:

        clubID = club[0]

        soup = getSoup( "www.fake-cricket-stats-website.com" )

        childList = soup.find_all('#selector')

        for child in childList:
            parent = child.find_parent("#selector")

            if not parent.has_attr('#selector'):
                continue

            onclick = parent['onclick']
            front = 10 + len( str(playerID) ) + len( str( clubID) )
            end = 15
            seasonID = onclick[front:len(onclick)-end]
            seasonRow = soup.find_all('tr', onclick=parent['onclick'])[0]
            text = next(seasonRow.children, None).text

            if ("/" not in text) and (not includeMidYearComps):
                continue

            if (clubID, seasonID, text) not in seasonList:
                # Returning tuple due to season duplication bug
                seasonList.append( (clubID, seasonID, text) )

    def returnThird(elem):
        return elem[2]          

    return sorted(seasonList, key=returnThird )

def getInningsID(matchID, inningsNum):
    letters = "ZABCD"
    return str(matchID)+letters[inningsNum]

# First pass at populating the player database. Fetches as much information as possible without opening individual scorecard views
def populateDatabaseFirstPass(playerID, difference=0):

    seasonList = getSeasonList(playerID)

    playerDB = "Player Databases/" + str(playerID) + ".db"

    matchList = []

    battingInningsID = 1#select (count *) from Batting ?

    bowlingInningsID = 1 

    #clubList = getClubList(playerID)

    # Small difference, only grab 2 most recent seasons
    if difference <= 10:
        seasonList = seasonList[-2:]

    # For each season in list, get list of matches, and add them to matchList
    for clubID, seasonID, seasonText in seasonList:

        # Debugging 2x Last Season bug
        #print str(club) + ", " + str(season)
        #continue
        # End

        if 1:
        #for club in clubList:

            #clubID = str(club)#[0])
            #print clubID

            soup = getSoup( "www.fake-cricket-stats-website.com" )
    
            seasonText = soup.select("#selector")[0].get_text(strip=True)
            #print seasonText
    
            matches = soup.select("#selector")
    
            prevMatchInfo = {}
            #if True:
            #   match = matches[2]
            for match in matches:
                matchOnclickText = match['onclick']
                #print matchOnclickText
                matchID = matchOnclickText[7:len(str(matchOnclickText))-2]
    
                innings = 0
    
                tds = match.select("td")
    
                superDebug = False
                if superDebug:
                    print(str(len(tds)))
                    i = 0
                    for thing in tds:
                        print(str(i) + " : " + str(thing))
                        i += 1
    
                # Fetch Match Specific Info
    
                grade = tds[0].get_text(strip=True).replace("'","")
                
                if grade == "":
                    innings = 2
                    if debug:
                        print("Multi Innings Match - Fetching Previous Info")
                    grade = prevMatchInfo['grade']
                    Round = prevMatchInfo['Round']
                    opponent = prevMatchInfo['opponent']
                    ground = prevMatchInfo['ground']
                    homeOrAway = prevMatchInfo['homeOrAway']
                    winOrLoss = prevMatchInfo['winOrLoss']
                    fullScorecardAvailable = prevMatchInfo['fullScorecardAvailable']
                    captain = prevMatchInfo['captain']
    
    
                else:
                    grade = tds[0].get_text(strip=True).replace("'","")
                    
                    innings = 1
    
                    Round = tds[1].get_text(strip=True)
    
                    opponent = tds[3].select("span")[0].get_text(strip=True).replace("'","")
    
                    ground = unknown
    
                    homeOrAway = unknown
                    regex = re.findall( r'(red|green)', tds[4].select("img")[0]["src"] )[0]
                    if regex == "green":
                        homeOrAway = "Home"
                    elif regex == "red":
                        homeOrAway = "Away"
    
                    winOrLoss = unknown
                    
                    fullScorecardAvailable = unknown
    
                    captain = unknown
    
                # Fetch Batting Specific Info
    
                batting = match.select("td.batting")
    
                if (batting[0].get_text(strip=True) != '') and (batting[1].get_text(strip=True) != '') and (batting[2].get_text(strip=True) != 'dnb'):
                    battingRuns = int(batting[0].get_text(strip=True))
                    battingPos = int(batting[1].get_text(strip=True))
                    battingOut = batting[2].get_text(strip=True)
    
                # Fetch Bowling Specific Info
    
                bowling = match.select("td.bowling")
    
                if bowling[0].get_text(strip=True)!= '':
                    
                    bowlingOvers = bowling[0].get_text(strip=True)
    
                    temp = bowling[1].get_text(strip=True)

                    if temp != '':
                        bowlingMaidens = int(temp)
                    else:
                        bowlingMaidens = 0
                    
                    temp = bowling[2].get_text(strip=True)
                    if temp != '':
                        bowlingWickets = int(temp)
                    else:
                        bowlingWickets = 0
    
                    temp = bowling[3].get_text(strip=True)
                    if temp != '':    
                        bowlingRuns = int(temp)
                    else:
                        if debug:
                            print("I dont think stats from this match should be included.")
                        bowlingRuns = 0
    
                # Fetch Fielding Specific Info
                # len fielding 5
                # Catches, CatchesWK, RunoutUnassisted, RunoutAssisted, Stumping
    
                fielding = match.select("td.fielding")
    
                ### DB Inserts into various tables
                ##
                # 
    

                # Comp/Grade Inclusion/Exclusion Checks
                loweredGradeString = grade.lower()
                excludedComp = False

                #  T20 Comps
                if ("t20" in loweredGradeString) and (not includeT20Comps):
                    excludedComp = True

                # Veterans Comps
                if ("veteran" in loweredGradeString) and (not includeVeteransComps):
                    excludedComp = True

                # Women's Only Comps
                if ("women" in loweredGradeString) and (not includeWomensOnlyComps):
                    excludedComp = True

                # Juniors Comps
                juniorStrings = ["under", "u11","u12","u13","u14","u15","u16","u17","u18","u19","u21"]
                if (not includeJuniorsComps):
                    for js in juniorStrings:
                        if js in loweredGradeString:
                            excludedComp = True
                            continue

                if not excludedComp:

                    #Matches
                    if matchID not in matchList:
                        # It wont be in DB so insert
                        # Consider changing "INSERT OR IGNORE" to "INSERT OR REPLACE"
                        #query = "INSERT OR IGNORE INTO Matches (MatchID, ClubID, Season, Round, Grade, Opponent, Ground, HomeOrAway, WinOrLoss, FullScorecardAvailable, Captain ) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
                        query = "INSERT OR REPLACE INTO Matches (MatchID, ClubID, Season, Round, Grade, Opponent, Ground, HomeOrAway, WinOrLoss, FullScorecardAvailable, Captain ) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
                        values = (matchID, clubID, seasonText, Round, grade, opponent, ground, homeOrAway, winOrLoss, fullScorecardAvailable, captain)
                        dbQuery(playerDB,query,values)
        
                        matchList.append(matchID)
        
                        # If verbose Print Match Info 
                        if verbose:
        
                            #Match Info
                            print("MatchID: " + str(matchID))
                            print("ClubID: " + str(clubID))
                            print("Season: " + seasonText)
                            print("Round: " + str(Round))
                            print("Grade: " + str(grade))
                            print("Innings: " + str(innings))# Not in Matches Table
                            print("Opponent: " + opponent)
                            print("Ground: " + ground)
                            print("HomeOrAway: " + homeOrAway)
                            print("WinOrLoss: " + winOrLoss)
                            print("FullScorecardAvailable: " + fullScorecardAvailable)
                            print("Captain: " + captain)
        
                    #Batting
                    if batting[0].get_text(strip=True) != '' and batting[2].get_text(strip=True) != 'dnb':

                        battingInningsID = getInningsID(matchID,innings)

                        # Consider changing "INSERT OR IGNORE" to "REPLACE"
                        #query = "INSERT OR IGNORE INTO Batting (BattingInningsID, MatchID, Innings, Runs, Position, HowDismissed, Fours, Sixes, TeamWicketsLost, TeamScore, TeamOversFaced) VALUES (?,?,?,?,?,?,null,null,null,null,null)"
                        query = "INSERT OR REPLACE INTO Batting (BattingInningsID, MatchID, Innings, Runs, Position, HowDismissed, Fours, Sixes, TeamWicketsLost, TeamScore, TeamOversFaced) VALUES (?,?,?,?,?,?,null,null,null,null,null)"
                        values = (battingInningsID, matchID, innings, battingRuns, battingPos, battingOut)#, unknown, unknown, unknown, unknown, unknown)
                        dbQuery(playerDB,query,values)
        
                        #battingInningsID += 1
        
                        # If Debug Print Batting/Innings Info
                        if verbose:
                            print("Batting Figures:")
                            print("\tRuns: " + str(battingRuns))
                            print("\tPosition: " + str(battingPos))
                            print("\tHow out: " + battingOut)
        
        
                    #Bowling
                    if bowling[0].get_text(strip=True) != '':
        
                        bowlingInningsID = getInningsID(matchID,innings)

                        # Consider changing "INSERT OR IGNORE" to "REPLACE"
                        #query = "INSERT OR IGNORE INTO Bowling (bowlingInningsID, MatchID, Innings, Overs, Wickets, Runs, Maidens) VALUES (?,?,?,?,?,?,?)"
                        query = "INSERT OR REPLACE INTO Bowling (bowlingInningsID, MatchID, Innings, Overs, Wickets, Runs, Maidens) VALUES (?,?,?,?,?,?,?)"
                        values = (bowlingInningsID, matchID, innings, bowlingOvers, bowlingWickets, bowlingRuns, bowlingMaidens)#, unknown, unknown, unknown, unknown, unknown)
                        dbQuery(playerDB,query,values)

                        #bowlingInningsID += 1

                        # If Debug Print Bowling/Innings Info
                        if verbose:
                            print("Bowling Figures:")
                            print("\tOvers: " + bowlingOvers)
                            print("\tMaidens: " + str(bowlingMaidens))
                            print("\tWickets: " + str(bowlingWickets))
                            print("\tRuns: " + str(bowlingRuns))
        
                    #Fielding
                    #if fielding[0].string.encode("ascii", "ignore") != '':
                    #   print "Fielding Figures:"
        
                    # Fetch High Level Batting, Bowling and Fielding stats
                    # Insert into relevant tables.
    
                prevMatchInfo = {
                    'matchID': matchID,
                    'clubID': clubID,
                    'seasonText': seasonText,
                    'Round': Round,
                    'grade': grade,
                    'opponent': opponent,
                    'ground': ground,
                    'homeOrAway': homeOrAway,
                    'winOrLoss': winOrLoss,
                    'fullScorecardAvailable': fullScorecardAvailable,
                    'captain': captain
                }
    
                #print ""
    
            # Courtesy sleep, to reduce load on x. 
            time.sleep(sleepDuration)

# Second pass at populating the player database. Goes through scorecards (if available) for all games in matchList
def populateDatabaseSecondPass(playerID):
    print("TODO")

# Third pass at populating the player database. Specifically concerning the TeamMates and TeamMatesMatches tables.
def populateDatabaseThirdPass(playerID):
    print("TODO")