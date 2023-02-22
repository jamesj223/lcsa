#!python3
###############################################################################
# cricket.py - A scraper and a stats analyzer for local cricket
# jamesj223

###############################################################################
# Imports

import os, requests, bs4, re, sqlite3, time, string, random

from numpy import median, nan, arange
import matplotlib.pyplot as plt

from datetime import datetime

###############################################################################
# User Input / Config

debug = False

# So I can have debug on, but not get the mass row update output
dbDebug = False

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

# Show All
showAll = True

###############################################################################
# DB Schemas

# Add fetched level? That way stats functions know whether they can run
# Could have the stats functions call the relevant fetch function if it hasn't already been run
# Maybe later
playerInfoTable = "PlayerInfo (PlayerID INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, NumMatches INTEGER)"

clubsTable = "Clubs (ClubID INTEGER PRIMARY KEY, ClubName TEXT)"

matchesTable = "Matches (MatchID INTEGER PRIMARY KEY, ClubID INTEGER, Season TEXT, Round INTEGER, Grade TEXT, Opponent TEXT, Ground TEXT, HomeOrAway TEXT, WinOrLoss TEXT, FullScorecardAvailable TEXT, Captain TEXT, FOREIGN KEY (ClubID) REFERENCES Clubs(ClubID))"

# Changing BattingInningsID from IntegerPK  to TextPK. Will be MatchID+Innings (ABCD)
battingTable = "Batting (BattingInningsID TEXT PRIMARY KEY, MatchID INTEGER, Innings INTEGER, Runs INTEGER, Position INTEGER, HowDismissed TEXT, Fours INTEGER, Sixes INTEGER, TeamWicketsLost INTEGER, TeamScore INTEGER, TeamOversFaced TEXT, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

# Changing BowlingInningsID from IntegerPK  to TextPK. Will be MatchID+Innings (ABCD)
bowlingTable = "Bowling (BowlingInningsID TEXT PRIMARY KEY, MatchID INTEGER, Innings INTEGER, Overs TEXT, Wickets INTEGER, Runs INTEGER, Maidens INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

fieldingTable = "Fielding (FieldingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Catches INTEGER, RunOuts INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

# Not Yet Implemented

teamMatesTable = "TeamMates (PlayerID INTEGER PRIMARY KEY, FirstName TEXT, LastName Text)"

teamMatesMatchesTable = "TeamMatesMatches (MatchID INTEGER, PlayerID INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID), FOREIGN KEY (PlayerID) REFERENCES TeamMates(PlayerID))"

# Placeholder value for missing information

unknown = "Unknown"

###############################################################################
# Functions

def setGlobals(playerStatsFromMain):
    global playerStats
    playerStats = playerStatsFromMain

########################################
### Phase 1 - Fetch data

# Creates a directory d if it doesnt already exist
def createDirectory(d,parent=None):
    if not os.path.exists(d):
        os.mkdir(d)

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

# Creates the player database. Specifically the PlayerInfo, Matches, Batting, Bowling and Fielding tables
def createDatabase(playerID, wipe=False):
    
    playerDB = "Player Databases/" + str(playerID) + ".db"

    # If Database doesnt exist, create one.
    if not os.path.exists(playerDB):
        open(playerDB, 'a').close()

    if wipe:
        if debug:
            print("Dropping all existing tables.")

        dbQuery(playerDB,"DROP TABLE IF EXISTS PlayerInfo;")
        dbQuery(playerDB,"DROP TABLE IF EXISTS Clubs;")
        dbQuery(playerDB,"DROP TABLE IF EXISTS Matches;")
        dbQuery(playerDB,"DROP TABLE IF EXISTS Batting;")
        dbQuery(playerDB,"DROP TABLE IF EXISTS Bowling;")
        dbQuery(playerDB,"DROP TABLE IF EXISTS Fielding;")

    dbQuery(playerDB,"CREATE TABLE IF NOT EXISTS " + playerInfoTable + ";")
    dbQuery(playerDB,"CREATE TABLE IF NOT EXISTS " + clubsTable + ";")
    dbQuery(playerDB,"CREATE TABLE IF NOT EXISTS " + matchesTable + ";")
    dbQuery(playerDB,"CREATE TABLE IF NOT EXISTS " + battingTable + ";")
    dbQuery(playerDB,"CREATE TABLE IF NOT EXISTS " + bowlingTable + ";")
    dbQuery(playerDB,"CREATE TABLE IF NOT EXISTS " + fieldingTable + ";")

# Runs the supplied query against the specified database
def dbQuery(database, query, values=() ):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    if len(values) > 0:
        c.execute(query,values)
    elif len(values) == 0:
        c.execute(query)
    else:
        if debug:
            print("Incorrect arguement for 'values' in function dbQuery")
    conn.commit()
    returnValue = c.fetchall()
    if dbDebug:
        print(str(c.rowcount) + " rows affected")
    conn.close()

    return returnValue

def getPlayerName(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"
    
    query = "SELECT FirstName, LastName FROM PlayerInfo"
    result = dbQuery(playerDB,query)

    fullName = str(result[0][0]) + " " + str(result[0][1])

    return fullName

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

# First pass at populating the player database. 
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
    
            time.sleep(sleepDuration)

# Second pass at populating the player database. 
def populateDatabaseSecondPass(playerID):
    print("TODO")

# Third pass at populating the player database. 
def populateDatabaseThirdPass(playerID):
    print("TODO")

########################################
### Phase 2 - Analyse data and present statistics

def stats_PlayerInfo(playerID):

    playerDB = "Player Databases/" + str(playerID) + ".db"
    games = dbQuery(playerDB, "SELECT NumMatches FROM PlayerInfo")
    if games:
        return games[0][0]
    else:
        return 0

####################
# Helper Functions for Stats

# Print function
def printStats(headers, stats, mode="H", newLine=True):

    if headers:
        playerStats.write('<thead class="table-light"><tr>')
        for header in headers:
            playerStats.write('<th scope="col">'+header+'</th>')
        playerStats.write("</tr></thead>")
        playerStats.write("<tbody><tr>")
    if stats:

        singleLineOutput = ""
        for stat in stats:
            #playerStats.write("<td>"+str(stat)+"</td>")
            singleLineOutput += "<td>"+str(stat)+"</td>"
        playerStats.write(singleLineOutput)
        playerStats.write("</tr>")


# Accordion Helper Star
def accordionHelperStart(caption, show=showAll, extraDivClass=""):
    # Print stats
    #playerStats.write('\n<br>\n')
    #playerStats.write('<div class="accordion-item">')
    playerStats.write('<div class="accordion-item '+extraDivClass+'">')

    # Generate random card/div ID
    divID = ''.join(random.choices(string.ascii_uppercase, k=10))
    #playerStats.write('<a class="btn btn-secondary" data-toggle="collapse" href="#'+divID+'" role="button" aria-expanded="false" aria-controls="'+divID+'">'+caption+'</a>')
    playerStats.write('<h2 class="accordion-header">')
      
    if show:
        playerStats.write('<button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#'+divID+'" aria-expanded="true" aria-controls="-collapseOne">'+caption+'</button></h2>')
        playerStats.write('<div class="accordion-collapse collapse show" id="' + divID + '" style="border-color:#DCDCDC">')
    else:
        playerStats.write('<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#'+divID+'" aria-expanded="true" aria-controls="-collapseOne">'+caption+'</button></h2>')
        playerStats.write('<div class="accordion-collapse collapse" id="' + divID + '" style="border-color:#DCDCDC">')

    playerStats.write('<div class="accordion-body">')

# Accordion Helper End
def accordionHelperEnd():
    # End accordion-body div
    playerStats.write("</div><!-- End accordion-body -->")
    # End accordion-collapse Div 
    playerStats.write("</div><!-- End accordion-collapse -->")
    # End accordion-item Div    
    playerStats.write("</div><!-- End accordion-item -->")

def disciplineHelper(discipline, inningsList, caption="Default Caption", show=showAll):

    headers = stats = ""

    # Get stats for all innings
    if discipline == "Batting":
        headers, stats = getBattingStats(inningsList)
    elif discipline == "Bowling":
        headers, stats = getBowlingStats(inningsList)

    accordionHelperStart(caption, show)
    if stats[0]:
        #playerStats.write( "<caption>"+caption+"</caption>" )
        playerStats.write('<div class="p-3 table-responsive">')
        playerStats.write('<table class="table table-bordered table-sm" style="background-color:white">')
        printStats(headers, stats)
        playerStats.write("</tbody></table>")
        playerStats.write("</div>")

    else:
        playerStats.write( '<p class="p-3">No stats available</p>' )

    accordionHelperEnd()

def multiLineDisciplineHelper(discipline, inningsList, indexHeader, indexColumn, indexCount, caption="Default Caption", extraDivClass="", accordionID=None):

    headers = stats = ""

    # Get stats for all innings
    if discipline == "Batting":
        headers, stats = getBattingStats(inningsList)
    elif discipline == "Bowling":
        headers, stats = getBowlingStats(inningsList)

    # Output table and headers first time only
    if indexCount == 0:
        accordionHelperStart(caption, showAll, extraDivClass)
        playerStats.write('<div class="p-3 table-responsive">')
        playerStats.write('<table class="table table-bordered table-sm" style="background-color:white">')
        #playerStats.write('<table class="table table-bordered table-sm caption-top">')
        #playerStats.write( "<caption>"+caption+"</caption>" )
        printStats( (indexHeader,) + headers, False )

    # Print stats
    if stats[0]:
        printStats(False, (indexColumn,) + stats)

        #playerStats.write("</table></div>")
    #else:
    #   playerStats.write( "<p>No stats available</p>" )    


# Calculate and return batting stats for a list of innings
def getBattingStats(inningsList):
    #headers = ("Innings", "High Score", "Not Outs", "Ducks", "25s", "50s", "100s", "Aggregate", "Average")
    headers = ("Innings", "High Score", "Not Outs", "Ducks", "25s", "50s", "100s", "Aggregate", "Average", "25+ Scores", "25+ %", "Duck %")

    # Initialise and zero all variables
    numInnings = highScore = notOuts = ducks = twentyFives = fifties = hundreds = aggregate = 0
    average = 0.0

    # Iterate over innings list
    for innings in inningsList:
        
        numInnings += 1

        if innings[3] > highScore:
            highScore = innings[3]

        if (innings[5] == 'no') or (innings[5] == 'rtno'):
            notOuts += 1

        if (innings[3] == 0) and (innings[5] != 'no'):
            ducks += 1

        if (innings[3] >= 25) and (innings[3] < 50):
            twentyFives += 1

        if (innings[3] >= 50) and (innings[3] < 100):
            fifties += 1

        if innings[3] >= 100:
            hundreds += 1

        aggregate += innings[3]

    # Calculate Batting Average (rounded to 2 decimal places)
    try:
        rawAverage = aggregate / (numInnings - notOuts) 
        average = round(rawAverage, 2)
    except ZeroDivisionError:
        average = "N/A"

    twentyFivePlus = twentyFives + fifties + hundreds

    twentyFivePlusPercent = percentageHelper(twentyFivePlus, numInnings)
    duckPercent = percentageHelper(ducks, numInnings)

    # Compile stats into tuple
    stats = (numInnings, highScore, notOuts, ducks, twentyFives, fifties, hundreds, aggregate, average, twentyFivePlus, twentyFivePlusPercent, duckPercent)

    return headers, stats

# Calculate and return bowling stats for a list of innings
def getBowlingStats(inningsList):
    # OLD
    #headers = ("Innings", "Overs", "Wickets", "Runs", "Maidens", "Average", "Strike Rate", "Economy")
    headers = ("Innings", "Overs", "Maidens", "Wickets", "Runs", "5WI", "Average", "Strike Rate", "Economy")

    # Initialise and zero all variables
    numInnings = runs = maidens = wickets = fivefa = 0
    overs = average = strikeRate = economy = 0.0

    # Iterate over innings list
    for innings in inningsList:
        
        numInnings += 1

        overs += int( float( innings[3] ) ) # Fix this
        wickets += innings[4]
        maidens += innings[6]
        runs += innings[5]
        if innings[4] >= 5:
            fivefa += 1

    # Calculate Bowling Average (rounded to 2 decimal places)
    try:
        rawAverage = runs / wickets
        average = round(rawAverage, 2)
    except ZeroDivisionError:
        average = "N/A"

    # Calculate Bowling Strike Rate (rounded to 2 decimal places)
    try:
        balls = (overs * 6) # fix this
        rawStrikeRate = balls / wickets 
        strikeRate = round(rawStrikeRate, 2)
    except ZeroDivisionError:
        strikeRate = "N/A"

    # Calculate Bowling Economy (rounded to 2 decimal places)
    try:
        rawEconomy = runs / overs # fix this
        economy = round(rawEconomy, 2)
    except ZeroDivisionError:
        economy = "N/A"

    # Compile stats into tuple
    stats = (numInnings, overs, maidens, wickets, runs, fivefa, average, strikeRate, economy)

    return headers, stats

# Analyse all innings for player, for a given discipline
def stats_Overall(playerID, discipline):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    caption = discipline + " - Overall Summary"

    inningsList = dbQuery(playerDB,"SELECT * FROM "+ discipline)# Batting")

    disciplineHelper(discipline, inningsList, caption)

# Stats by Season
def stats_Season(playerID, discipline):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    caption = discipline + " - Stats by Season"

    seasonList = dbQuery(playerDB, "SELECT DISTINCT Season FROM Matches")

    indexCount = 0

    for season in sorted(seasonList):

        seasonString = str( season[0] )

        matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Season='" + season[0] + "'")

        formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

        inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 

        multiLineDisciplineHelper(discipline, inningsList, "Season", seasonString, indexCount, caption, "season")

        indexCount += 1

    playerStats.write("</tbody></table>")
    playerStats.write("</div>")

    accordionHelperEnd()


# Stats by Opponent
def stats_Opponent(playerID, discipline):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    caption = discipline + " - Stats by Opponent"

    opponentList = dbQuery(playerDB, "SELECT DISTINCT Opponent FROM Matches ORDER BY Opponent ASC")

    indexCount = 0

    for opponent in opponentList:

        matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Opponent='" + opponent[0] + "'")

        formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

        inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 
        
        multiLineDisciplineHelper(discipline, inningsList, "Opponent", opponent[0], indexCount, caption, "opponent")

        indexCount += 1

    playerStats.write("</tbody></table>")
    playerStats.write("</div>")

    accordionHelperEnd()

# Stats by Grade
def stats_Grade(playerID, discipline):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    caption = discipline + " - Stats by Grade"

    gradeList = dbQuery(playerDB, "SELECT DISTINCT Grade FROM Matches ORDER BY Grade ASC")

    indexCount = 0

    for grade in sorted(gradeList):

        gradeString = str( grade[0] )

        matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Grade='" + grade[0] + "'")

        formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

        inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 
        
        multiLineDisciplineHelper(discipline, inningsList, "Grade", gradeString, indexCount, caption, "grade")

        indexCount += 1
    
    playerStats.write("</tbody></table>")
    playerStats.write("</div>")

    accordionHelperEnd()

# Stats by HomeOrAway - FIX THIS FOR HTML OUTPUT
def stats_HomeOrAway(playerID, discipline):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    playerStats.write( discipline + " - Stats by Home/Away"+"\n" )

    playerStats.write( "Home"+"\n" )
    matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE HomeOrAway='Home'")
    formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"
    inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 
    disciplineHelper(discipline, inningsList)
    #headers, stats = getBattingStats(inningsList)
    #printStats(headers, stats)

    playerStats.write( "Away"+"\n" )
    matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE HomeOrAway='Away'")
    formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"
    inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 
    disciplineHelper(discipline, inningsList)
    #headers, stats = getBattingStats(inningsList)
    #printStats(headers, stats)
    
    playerStats.write("\n")

# Stats by Club
def stats_Club(playerID, discipline):

    playerDB = "Player Databases/" + str(playerID) + ".db"

    caption = discipline + " - Stats by Club"

    clubList = getClubList(playerID)

    indexCount = 0
    for clubID, clubName in clubList:

        matchList = dbQuery(playerDB, "SELECT * FROM Matches where ClubID =" + str(clubID) )

        formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

        inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline+ " WHERE MatchID IN " + formattedMatchList) 
        
        multiLineDisciplineHelper(discipline, inningsList, "Club", clubName, indexCount, caption, "club")

        indexCount += 1
        
    playerStats.write("</tbody></table>")
    playerStats.write("</div>")

    accordionHelperEnd()

def recentHelper(playerDB, discipline, numSeasons, seasonList, caption="Default Caption"):
    matchList = []

    for season in sorted(seasonList)[-numSeasons:]:

        matchList += dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Season='" + season[0] + "'")

    formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

    inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 

    disciplineHelper(discipline, inningsList, caption, True)
    
    playerStats.write("\n")

# Stats for past X seasons
def stats_Recent(playerID, discipline, numSeasons):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    #playerStats.write( discipline + " - Recent Stats"+"\n" )

    seasonList = dbQuery(playerDB, "SELECT DISTINCT Season FROM Matches")

    # Call Overall Stats
    #stats_Batting_Overall(playerID)

    # Stats for Last Season
    caption = discipline + " - Last/Current Season"
    recentHelper(playerDB, discipline, 1, seasonList, caption)

    # Stats for Last X Seasons
    caption =  discipline + " - Last " + str(numSeasons) + " Seasons"
    recentHelper(playerDB, discipline, numSeasons+1, seasonList, caption)
    
    playerStats.write("\n")

# Stats for past juniors/seniors
def stats_JuniorSenior(playerID, discipline):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    #playerStats.write( discipline + " - Junior/Senior Stats"+"\n" )

    gradeList = dbQuery(playerDB, "SELECT DISTINCT Grade FROM Matches")

    # Strings to look for in grade name
    juniorStrings = ["under", "11","12","13","14","15","16","17","18","19","21"]#"20" - T20 gets flagged if we leave that in.

    juniorList = []
    seniorList = []

    for grade in gradeList:
        
        for string in juniorStrings:
            if string in grade[0].lower():
                
                if grade[0] not in juniorList:
                    juniorList += [grade[0]]

        if grade[0] not in juniorList:
            seniorList += [grade[0]]
        
    juniorMatchList = []
    seniorMatchList = []

    for grade in juniorList:

        juniorMatchList += dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Grade='" + grade + "'")

    for grade in seniorList:

        seniorMatchList += dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Grade='" + grade + "'")

    if juniorMatchList and seniorMatchList:

        #playerStats.write('<br><br>')
        #playerStats.write('<div class="card">')

        # Juniors
        matchList = juniorMatchList

        formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"   

        inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 

        caption = discipline + " Junior Stats"
        #disciplineHelper(discipline, inningsList, caption)

        headers = stats = ""

        # Get stats for all innings
        if discipline == "Batting":
            headers, stats = getBattingStats(inningsList)
        elif discipline == "Bowling":
            headers, stats = getBowlingStats(inningsList)

        accordionHelperStart(caption, showAll)
        if stats[0]:
            #playerStats.write( "<caption>"+caption+"</caption>" )
            playerStats.write('<div class="p-3 table-responsive">')
            playerStats.write('<table class="table table-bordered table-sm" style="background-color:white">')
            printStats(headers, stats)
            playerStats.write("</tbody></table>")
            playerStats.write("</div>")

        else:
            playerStats.write( '<p class="p-3">No stats available</p>' )


        playerStats.write( '<p class="p-3">' )
        playerStats.write( "Stats from " + str(len(matchList)) + " games in the following Junior Grades: " + str([i for i in juniorList]) )
        playerStats.write( "</p>" )
        
        accordionHelperEnd()

        # Seniors

        matchList = seniorMatchList

        formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"   

        inningsList = dbQuery(playerDB, "SELECT * FROM " + discipline + " WHERE MatchID IN " + formattedMatchList) 

        caption = discipline + " Senior Stats"
        headers = stats = ""

        # Get stats for all innings
        if discipline == "Batting":
            headers, stats = getBattingStats(inningsList)
        elif discipline == "Bowling":
            headers, stats = getBowlingStats(inningsList)

        accordionHelperStart(caption, showAll)
        if stats[0]:
            #playerStats.write( "<caption>"+caption+"</caption>" )
            playerStats.write('<div class="p-3 table-responsive">')
            playerStats.write('<table class="table table-bordered table-sm" style="background-color:white">')
            printStats(headers, stats)
            playerStats.write("</tbody></table>")
            playerStats.write("</div>")

        else:
            playerStats.write( '<p class="p-3">No stats available</p>' )


        playerStats.write( '<p class="p-3">' )
        playerStats.write( "Stats from " + str(len(matchList)) + " games in the following Senior Grades: " + str([i for i in seniorList]) )
        playerStats.write( "</p>" )

        accordionHelperEnd()
        
        #playerStats.write('</div>')
    
    #playerStats.write("\n")

####################
## Batting Only Stats

# Batting stats by DismissalBreakdown
def stats_Batting_DismissalBreakdown(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    accordionHelperStart("Dismissal Breakdown", showAll)
    playerStats.write('<div class="p-3 table-responsive">')

    #playerStats.write('<br><br>')
    #playerStats.write('<div class="card">')
    playerStats.write('<table class="table table-bordered table-sm caption-top">')
   # playerStats.write( "<caption>"+"Dismissal Breakdown"+"</caption>" )

    dismissalStats = dbQuery(playerDB, "SELECT HowDismissed, COUNT(*) as Count from Batting GROUP BY HowDismissed ORDER BY Count DESC")

    headers = [ str(i[0]) for i in dismissalStats ]

    stats = [ i[1] for i in dismissalStats ]

    total = sum(stats)

    percentages = [percentageHelper(i,total) for i in stats]

    # Replace this with better print
    # Include % of innings and % of dismissals
    #printStats(headers, stats)
    printStats(headers, stats)
    printStats(False, percentages)
    playerStats.write("</tbody></table>")
    playerStats.write("</div>")
    accordionHelperEnd()


def percentageHelper(smallNumber, bigNumber):

    a = float(smallNumber)
    b = float(bigNumber)

    try:
        percentage = a/b
        return "{:.1%}".format(percentage)
    except ZeroDivisionError:
        return "N/A"

# Batting stats by Batting Position
def stats_Batting_Position(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    #playerStats.write('<br><br>')
    #playerStats.write('<div class="card">')
    #playerStats.write( "<caption>"+"Batting Position"+"</caption>" )
    accordionHelperStart("Batting Position", showAll)
    playerStats.write('<div class="p-3 table-responsive">')
    playerStats.write('<table class="table table-bordered table-sm caption-top">')
    
    inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE Position IN (1,2)") 

    headers, stats = getBattingStats(inningsList)

    printStats(("Position",)+headers, False, "H", False)
    #playerStats.write("\n")
    printStats(False, ("Opening",)+stats, "H",True)

    for i in range(3,12):
        inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE Position="+str(i)) 
        headers, stats = getBattingStats(inningsList)
        printStats(False, ("# " + str(i),)+stats, "H",True)

    playerStats.write("</tbody></table>")

    # Get Average Batting Position
    abp = dbQuery(playerDB, "SELECT AVG(Cast(Position as Float)) From Batting")[0][0]#SUM(Position)
    abpString = "N/A"
    if abp != None:
        abpString = str( round(abp,2) )

    playerStats.write( '<p class="p-3">')
    playerStats.write( "Average Batting Position: " + abpString +"\n" )
    playerStats.write('<br>')

    #playerStats.write("</p><p>")

    # Get Mode Batting Position
    posString = ""
    if abp != None:
        posList = dbQuery(playerDB, "SELECT Position From Batting")
        formattedPosList = [ i[0] for i in posList ]
        # Replace 1 and 2 with "Opening"
        fixedForOpeningList = ["Opening" if x<3 else x for x in formattedPosList]
        mode = max(set(fixedForOpeningList), key=fixedForOpeningList.count)
        posString = str(mode)
    playerStats.write( "Mode Batting Position: " + posString +"\n" )
    
    playerStats.write("</p>")
    playerStats.write('</div>')
    accordionHelperEnd()

# Batting stats by NohitBrohitLine - FIX THIS FOR HTML OUTPUT
def stats_Batting_NohitBrohitLine(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    playerStats.write( "Nohit/Brohit Line!"+"\n" )

    # Is median the best way to find this line?
    # Or find the number with the biggest difference in average? 
    # Would probably have to exclude 0 
    # Find the score where players get "stuck"
    # IE I think I get out a lot around 13, once I'm passed that I'm good

    line = median( dbQuery(playerDB, "SELECT Runs from Batting ORDER BY Runs ASC") )

    playerStats.write( str( line ) +"\n" )
    
    averageWhenCrossLine = "TODO"

    playerStats.write("\n")

# Batting stats by Bingo - FIX THIS FOR HTML OUTPUT
def stats_Batting_Bingo(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    playerStats.write( "Bingo!"+"\n" )

    bingoList = dbQuery(playerDB, "SELECT DISTINCT Runs FROM Batting ORDER BY Runs ASC")

    formattedBingoList = [ i[0] for i in bingoList ]

    missingNumbers = []

    for i in range( 0, formattedBingoList[-1]+1 ):
        if i not in formattedBingoList:
            missingNumbers.append(i)

    # Make this a table 0 to high score. Colour the squares in?
    # And number them with how many times you've hit each score
    playerStats.write( "Hit"+"\n" )
    playerStats.write( str( formattedBingoList ) + "\n" )
    playerStats.write( "Miss"+"\n" )
    playerStats.write( str( missingNumbers )  +"\n" )

    # Find next bingo number
    
    playerStats.write("\n")

####################
## Bowling Only Stats

# Scrap this and bring these stats into Discipline Helper?
# Would allow viewing these stats for recent/season/grade etc
# Bowling Workload stats - FIX THIS FOR HTML OUTPUT
def stats_Bowling_Workload(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    overs = dbQuery(playerDB, "SELECT SUM(Cast(Overs as Int)) FROM Bowling")[0][0]
    #print overs
    innings = dbQuery(playerDB, "SELECT COUNT(Cast(Overs as Int)) FROM Bowling")[0][0]
    #print innings
    maxOvers = dbQuery(playerDB, "SELECT Max(Cast(Overs as Int)) FROM Bowling")[0][0]
    #print maxOvers
    games = dbQuery(playerDB, "SELECT NumMatches FROM PlayerInfo")[0][0]
    #print games

    if overs:
        opg = round(overs/games ,2)
        opi = round(overs/innings,2)
    else:
        opg = "N/A"
        opi = "N/A"

    accordionHelperStart("Bowling - Overs Bowled Per Game", showAll) 

    playerStats.write('<div class="p-3 table-responsive">')

    playerStats.write("<p>")

    playerStats.write( "Average Overs Bowled Per Game: " + str( opg ) + "<br />")
    playerStats.write( "Average Overs Bowled Per Innings: " + str( opi ) + "<br />")
    playerStats.write( "Max Overs Bowled In One Innings: " + str(maxOvers) + "<br />")
    
    playerStats.write("</p>")

    playerStats.write("</div>")

    accordionHelperEnd()

####################
## Graphs

# Calculate/Graph Batting - Running Average and TIRA (Twenty Innings Running Average)
def stats_Batting_Graphs(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    createDirectory("Player Stats/images")
    imageFileName = "images/" + str(playerID) + '-Batting.png'

    caption = "Batting Graphs"

    inningsList = dbQuery(playerDB,"SELECT * FROM "+ "Batting")

    playerStats.write('<div class="accordion-item">')

    # Generate random card/div ID
    divID = ''.join(random.choices(string.ascii_uppercase, k=10))
    #playerStats.write('<a class="btn btn-secondary" data-toggle="collapse" href="#'+divID+'" role="button" aria-expanded="false" aria-controls="'+divID+'">'+caption+'</a>')
    playerStats.write('<h2 class="accordion-header">')
      
    show = True  
    if show:
        playerStats.write('<button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#'+divID+'" aria-expanded="true" aria-controls="-collapseOne">'+caption+'</button></h2>')
        playerStats.write('<div class="accordion-collapse collapse show" id="' + divID + '" style="border-color:#DCDCDC">')
    else:
        playerStats.write('<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#'+divID+'" aria-expanded="true" aria-controls="-collapseOne">'+caption+'</button></h2>')
        playerStats.write('<div class="accordion-collapse collapse" id="' + divID + '" style="border-color:#DCDCDC">')

    playerStats.write('<div class="accordion-body">')

    inningsCount = 0
    notOuts = 0
    totalRuns = 0
    highScore = 0
    listA = [] # X Axis - Innings numbers. 1,2,3,4... etc
    listB = [] # Y Axis - Runs Manhattan
    listC = [] # Y Axis - Running Average
    listD = [] # Y Axis - TIRA (Twenty Innings Running Average)

    tiraRunsWindow = []
    tiraNotOutWindow = []

    if inningsList:
        # Create Runs Manhattan
        for innings in inningsList:
            
            inningsCount += 1

            listA.append( inningsCount )
            listB.append( innings[3] )

            highScore = max(highScore,innings[3])

            totalRuns += innings[3]
            tiraRunsWindow.append(innings[3])
            
            if (innings[5] == 'no') or (innings[5] == 'rtno'):
                notOuts += 1
                tiraNotOutWindow.append(1)
            else:
                tiraNotOutWindow.append(0)
            
            try:
                rawAverage = totalRuns / (inningsCount - notOuts) 
                runningAverage = round(rawAverage, 2)
            except ZeroDivisionError:
                runningAverage = nan

            listC.append(runningAverage)

            #listD

            # If len(runsWindow) is > 20, pop(0)
            if len(tiraRunsWindow) > 20:
                tiraRunsWindow.pop(0)
                tiraNotOutWindow.pop(0)
            # If len(runsWindow) == 20 try caluclate and add to listD
            if len(tiraRunsWindow) == 20:
                try:
                    rawAverage = sum(tiraRunsWindow) / (20 - sum(tiraNotOutWindow)) 
                    tiraAverage = round(rawAverage, 2)
                except ZeroDivisionError:
                    tiraAverage = nan
                listD.append(tiraAverage)
            # else add nan 
            else:
                listD.append(nan)



        playerStats.write( "<p>" )

        fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_facecolor('#DCDCDC')

        plt.ylabel('Runs')
        plt.xlabel('Innings')

        plt.bar(listA, listB,  label='Runs', zorder=2)
        plt.plot(listA, listC, color='#e66020', label='Average', linewidth=3, zorder=4)
        plt.fill_between(listA, listC, color='#e66020', alpha=0.30, zorder=1)
        plt.plot(listA, listD, color='#6f9c41', label='TIRA', linewidth=2, zorder=3)
        plt.fill_between(listA, listD, color='#6f9c41', alpha=0.30, zorder=1)

        # White background legend
        legend = plt.legend(loc='upper right')
        frame = legend.get_frame()
        frame.set_facecolor('white')

        # Gridlines. Major every 10, minor every 5
        major_ticks_x = arange(0, inningsCount, 10)
        minor_ticks_x = arange(0, inningsCount, 5)
        major_ticks_y = arange(0, highScore+10, 10)
        minor_ticks_y = arange(0, highScore+10, 5)

        ax.set_xticks(major_ticks_x)
        ax.set_xticks(minor_ticks_x, minor=True)
        ax.set_yticks(major_ticks_y)
        ax.set_yticks(minor_ticks_y, minor=True)
        ax.tick_params(labelbottom=True, labelleft=True, labelright=True)
        plt.grid(axis='y', which='both', zorder=0)

        # Plot hoirzontal lines at 25, 50 and 100
        plt.plot(listA, [25]*len(listA), color='#000000', linewidth=1, zorder=1)
        plt.plot(listA, [50]*len(listA), color='#000000', linewidth=1, zorder=1)
        plt.plot(listA, [100]*len(listA), color='#000000', linewidth=1, zorder=1)

        # Make sure 0,0 is in the bottom left
        plt.xlim(xmin=0, xmax=inningsCount+1)
        plt.ylim(ymin=0, ymax=highScore+10)

        plt.savefig('Player Stats/'+imageFileName)

        plt.close('all')

        playerStats.write( '<a href="'+imageFileName+'">')
        playerStats.write( '<img src="'+imageFileName+'" class="img-fluid" alt="'+imageFileName+'">' )
        playerStats.write( "</a>" )
        playerStats.write( "</p>" )

    else:
        playerStats.write( "<p>No stats available</p>" )

    accordionHelperEnd()

# Calculate/Graph Bowling - Running Average and TIRA (Twenty Innings Running Average)
def stats_Bowling_Graphs(playerID):

    playerDB = "Player Databases/" + str(playerID) + ".db"

    createDirectory("Player Stats/images")
    imageFileName = "images/" + str(playerID) + '-Bowling.png'

    caption = "Bowling Graphs"

    inningsList = dbQuery(playerDB,"SELECT * FROM "+ "Bowling")

    playerStats.write('<div class="accordion-item">')

    # Generate random card/div ID
    divID = ''.join(random.choices(string.ascii_uppercase, k=10))
    #playerStats.write('<a class="btn btn-secondary" data-toggle="collapse" href="#'+divID+'" role="button" aria-expanded="false" aria-controls="'+divID+'">'+caption+'</a>')
    playerStats.write('<h2 class="accordion-header">')
      
    show = True  
    if show:
        playerStats.write('<button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#'+divID+'" aria-expanded="true" aria-controls="-collapseOne">'+caption+'</button></h2>')
        playerStats.write('<div class="accordion-collapse collapse show" id="' + divID + '" style="border-color:#DCDCDC">')
    else:
        playerStats.write('<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#'+divID+'" aria-expanded="true" aria-controls="-collapseOne">'+caption+'</button></h2>')
        playerStats.write('<div class="accordion-collapse collapse" id="' + divID + '" style="border-color:#DCDCDC">')

    playerStats.write('<div class="accordion-body">')

    inningsCount = 0
    totalWickets = 0
    totalRuns = 0
    maxGraphHeight = 10
    listA = [] # X Axis - Innings numbers. 1,2,3,4... etc
    listB = [] # Y Axis - Wickets Manhattan
    listC = [] # Y Axis - Running Average
    listD = [] # Y Axis - TIRA (Twenty Innings Running Average)

    listE = [] # Wickets Scatterplot X
    listF = [] # Wickets Scatterplot Y

    tiraRunsWindow = []
    tiraWicketsWindow = []

    if inningsList:
        # Create Runs Manhattan
        for innings in inningsList:
            
            inningsCount += 1

            wickets = innings[4]
            runs = innings[5]

            listA.append( inningsCount )

            listB.append( wickets )

            for i in range(wickets):
                listE.append( inningsCount )
                listF.append( i + 0.5 )

            #highScore = max(highScore,innings[3])

            totalRuns += runs
            totalWickets += wickets

            tiraRunsWindow.append(runs)
            tiraWicketsWindow.append(wickets)
            
            try:
                rawAverage = totalRuns / totalWickets 
                runningAverage = round(rawAverage, 2)
            except ZeroDivisionError:
                runningAverage = nan

            listC.append(runningAverage)

            #listD

            tiraAverage = nan
            # If len(runsWindow) is > 20, pop(0)
            if len(tiraRunsWindow) > 20:
                tiraRunsWindow.pop(0)
                tiraWicketsWindow.pop(0)
            # If len(runsWindow) == 20 try caluclate and add to listD
            if len(tiraRunsWindow) == 20:
                try:
                    rawAverage = sum(tiraRunsWindow) / sum(tiraWicketsWindow)
                    tiraAverage = round(rawAverage, 2)
                except ZeroDivisionError:
                    tiraAverage = nan
                listD.append(tiraAverage)
            # else add nan 
            else:
                listD.append(nan)

            maxGraphHeight = max(maxGraphHeight, runningAverage, tiraAverage)

        playerStats.write( "<p>" )

        fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
        ax = fig.add_subplot(1, 1, 1)
        ax.set_facecolor('#DCDCDC')

        plt.ylabel('Average')
        plt.xlabel('Innings')

        #plt.bar(listA, listB,  label='Wickets', zorder=2)
        plt.scatter(listE, listF, color='#e66020', label='Wickets', zorder=2)
        plt.plot(listA, listC, color='#1f77b4', label='Average', linewidth=3, zorder=4)
        plt.fill_between(listA, listC, color='#1f77b4', alpha=0.30, zorder=1)
        plt.plot(listA, listD, color='#6f9c41', label='TIRA', linewidth=2, zorder=3)
        plt.fill_between(listA, listD, color='#6f9c41', alpha=0.30, zorder=1)

        # White background legend
        legend = plt.legend(loc='upper right')
        frame = legend.get_frame()
        frame.set_facecolor('white')

        # Gridlines. Major every 10, minor every 5
        major_ticks_x = arange(0, inningsCount, 10)
        minor_ticks_x = arange(0, inningsCount, 5)
        major_ticks_y = arange(0, maxGraphHeight+5, 5)
        minor_ticks_y = arange(0, maxGraphHeight+5, 1)

        ax.set_xticks(major_ticks_x)
        ax.set_xticks(minor_ticks_x, minor=True)
        ax.set_yticks(major_ticks_y)
        ax.set_yticks(minor_ticks_y, minor=True)
        ax.tick_params(labelbottom=True, labelleft=True, labelright=True)
        plt.grid(axis='y', which='both', zorder=0)

        # Plot hoirzontal lines at 5
        plt.plot(listA, [5]*len(listA), color='#000000', linewidth=1, zorder=1)

        # Make sure 0,0 is in the bottom left
        plt.xlim(xmin=0, xmax=inningsCount+1)
        plt.ylim(ymin=0, ymax=maxGraphHeight+5)

        plt.savefig('Player Stats/'+imageFileName)

        plt.close('all')

        playerStats.write( '<a href="'+imageFileName+'">')
        playerStats.write( '<img src="'+imageFileName+'" class="img-fluid" alt="'+imageFileName+'">' )
        playerStats.write( "</a>" )
        playerStats.write( "</p>" )

    else:
        playerStats.write( "<p>No stats available</p>" )

    accordionHelperEnd()



####################
## HTML Printing Functions

def writeHTMLTemplatePart1():
    playerStats.write("""<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- New js and css -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.min.js" integrity="sha384-QJHtvGhmr9XOIpI6YVutG+2QOK9T+ZnN4kzFN1RtK3zEFEIsxhlmWl5/YESvpZ13" crossorigin="anonymous"></script>
    
    <!-- Accordion CSS -->
    <style>
    .accordion-button {color: black;background-color:#a9a9a9;}
    .accordion-button:not(.collapsed) {color: black;background-color: #DCDCDC;}
    .accordion-button:not(.collapsed)::after {background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23000'%3e%3cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e");}
    .accordion-button:focus {border-color: #5cb85c;  box-shadow: none; -webkit-box-shadow: none;}
    </style>

    <!-- Table Freeze CSS -->
    <style>
    table { display: block; overflow-x: auto;  }
    th:first-child { position:sticky; left:0px; background-color:#f8f9fa; border: 1px #dee2e6; background-clip: padding-box;}
    td:first-child { position:sticky; left:0px; background-color:#ffffff; border: 1px #dee2e6; background-clip: padding-box;}
    </style>
    """)


def writeHTMLTemplatePart2(idAndName, gamesPlayed):
    part2Template = """\n<title>{0}</title>
  </head>
  <body>

<nav class="navbar navbar-expand-lg justify-content-between" style="background-color:#fcd91d">

    <div class="p-2"> <a class="nav-item" href="javascript:history.back()" style="color:black">&#8592; Back</a> </div>
    <div class="p-2"> <h3 class="navbar-brand">{0}</h3> </div>
    <div class="p-2"> <span class="navbar-text collapse navbar-collapse">{1} games</span> </div>

</nav>

<main class="bd-main" style="background-color:#A9A9A9">
<div class="container-lg p-3">

<ul class="nav nav-tabs" id="myTab" role="tablist">
  <li class="nav-item" role="presentation">
    <a class="nav-link active" id="batting-tab" data-bs-toggle="tab" href="#batting" role="tab" aria-controls="batting" aria-selected="true" style="color:black">Batting</a>
  </li>
  <li class="nav-item" role="presentation">
    <a class="nav-link" id="bowling-tab" data-bs-toggle="tab" href="#bowling" role="tab" aria-controls="bowling" aria-selected="false" style="color:black">Bowling</a>
  </li>
</ul>
<div class="tab-content bg-white" id="myTabContent">
  <!-- Batting Content Tab -->
  <div class="tab-pane fade show active" id="batting" role="tabpanel" aria-labelledby="batting-tab">
    <div class="card p-3">
    <div class="accordion">"""
    playerStats.write(part2Template.format(idAndName, gamesPlayed))

def writeHTMLTemplatePart3():
    playerStats.write("""\n
    </div><!-- End Accordion -->
    </div><!-- End Card -->
    </div><!-- End tab-pane batting -->


    <!-- Bowling Content Tab -->
    <div class="tab-pane fade" id="bowling" role="tabpanel" aria-labelledby="bowling-tab">
    <div class="card p-3">
    <div class="accordion">""")

def writeHTMLTemplatePart4():
    playerStats.write("""\n
    </div><!-- End Accordion -->
    </div><!-- End Card -->
    </div><!-- End End tab-pane bowling -->

    </div><!-- End tab-content -->
    </div><!-- End container p-3-->
    </main>""")
    # Hide specific cards unless viewing from localhost
    playerStats.write("""\n<script>
if (!(location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.hostname === "")){
    //alert("It's a local server!");

    // Grade
    var gradeCards = document.getElementsByClassName("grade");
    for (var i = 0; i < gradeCards.length; i++) {
        gradeCards[i].hidden = true;
        };

    // Club
    //var clubCards = document.getElementsByClassName("club");
    //for (var i = 0; i < clubCards.length; i++) {
    //    clubCards[i].hidden = true;
    //    };

    // Opponent
    var opponentCards = document.getElementsByClassName("opponent");
    for (var i = 0; i < opponentCards.length; i++) {
        opponentCards[i].hidden = true;
        };

}
</script>""")
    playerStats.write("""\n</body></html>""")
    #playerStats.write("""\n</div></div></main></body></html>""")


def rebuildIndex():

    now = datetime.now()

    template1 = """
    <html>
    <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.min.js" integrity="sha384-QJHtvGhmr9XOIpI6YVutG+2QOK9T+ZnN4kzFN1RtK3zEFEIsxhlmWl5/YESvpZ13" crossorigin="anonymous"></script>
    </head>
    <body style="background-color:#A9A9A9">
    <nav class="navbar navbar-expand-lg" style="background-color:#fcd91d">
        <div class="container-fluid">
            <!-- Old Navbar -->
            <!--a class="nav-item" href="javascript:history.back()" style="color:black"></a-->
            <!--h2 class="navbar-brand" align="left">{0}</h2-->
            <!--span class="navbar-text"></span-->

            <!-- New Navbar -->
            <!--div class="p-2"> <a class="nav-item" href="javascript:history.back()" style="color:black"></a> </div-->
            <div class="p-2"> <h3 class="navbar-brand">{0}</h3> </div>
            <div class="p-2"> <span class="navbar-text collapse navbar-collapse">Last updated: {1}</span> </div>


        </div>
    </nav>
    <main class="bd-main" style="background-color:#A9A9A9">
    <div class="container-lg p-3">
    <div class="card p-3">
    """

    template2 = """</div></main></body></html>"""

    EXCLUDED = ['index.html', 'sorttable.js', '.DS_Store', 'images']

    import os

    fnames = [fname for fname in sorted(os.listdir("Player Stats"))
              if fname not in EXCLUDED]
    #print fnames
    sorted_fnames = sorted(fnames, key = lambda x: int(x.split("-")[0])  )
    #print sorted_fnames

    header = "Local Cricket Stats Assistant"

    index = open("Player Stats/index.html", "w")
    index.write(template1.format(header, now))
    index.write('<div class="p-3 table-responsive">')
    index.write('<table class="table table-bordered">')
    #index.write( "<caption>"+caption+"</caption>" )
    index.write("<tbody>")
    for name in sorted_fnames:
        index.write('<tr><td><a href="'+name+'"><div style="height:100%;width:100%">'+name+'</div></a></td></tr>')
    index.write("</tbody>")
    index.write("</table></div></div>")
    index.write(template2)
    index.close

####################
## TO DO

## Need Fetch Pass 2

# Stats by Ground
def stats_Ground(playerID):
    print("TODO")

# Stats by PercentOfTeam
def stats_Batting_PercentOfTeam(playerID):
    print("TODO")

    # % of Team Runs for each game
    # Min, Max, Average

    # % of Team Overs faced for each game
    # Min, Max, Average
    # FOW data doesn't have overs (when it is even there)

## Need Fetch Pass 3

# Stats by TeamMate
def stats_TeamMate(playerID, minGames):
    print("TODO")

# Stats by Captain
def stats_Captain(playerID, minGames):
    print("TODO")
