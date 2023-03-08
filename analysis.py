#!python3
###############################################################################
# analysis.py - Data analysis stuff for LCSA 
# jamesj223

###############################################################################
# Imports

import os, re, time, string, random

from numpy import median, nan, arange
import matplotlib.pyplot as plt

from datetime import datetime

from database import dbQuery, createDirectory
from fetch import getClubList

###############################################################################
# User Input / Config

debug = False

verbose = False

# Have accordions expanded or collapsed by default
showAll = True

###############################################################################
# Functions

def setGlobals(playerStatsFromMain):
    global playerStats
    playerStats = playerStatsFromMain

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
    # New - Updated to match order. + 5WI
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

def dismissalBreakdownHelper(playerID,numSeasons=False):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    playerStats.write('<table class="table table-bordered table-sm caption-top">')
    #playerStats.write( "<caption>"+"Dismissal Breakdown"+"</caption>" )

    if numSeasons:

        matchList = []

        seasonList = dbQuery(playerDB, "SELECT DISTINCT Season FROM Matches")

        for season in sorted(seasonList)[-numSeasons:]:

            matchList += dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Season='" + season[0] + "'")
            formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"
        
        dismissalStats = dbQuery(playerDB, "SELECT HowDismissed, COUNT(*) as Count from Batting WHERE MatchID IN " + formattedMatchList + "GROUP BY HowDismissed ORDER BY Count DESC")

    else:
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

# Batting stats by DismissalBreakdown
def stats_Batting_DismissalBreakdown(playerID):
    
    accordionHelperStart("Dismissal Breakdown", showAll)
    playerStats.write('<div class="p-3 table-responsive">')

    playerStats.write('Last/Current Season')
    dismissalBreakdownHelper(playerID,1)

    playerStats.write('Overall')
    dismissalBreakdownHelper(playerID)
    
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

# Batting stats by Bingo - Output a colour coded bingo table of scores a player as made
def stats_Batting_Bingo(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    accordionHelperStart("Batting Bingo", showAll)

    bingoList = dbQuery(playerDB, "SELECT DISTINCT Runs FROM Batting ORDER BY Runs ASC")

    formattedBingoList = [ i[0] for i in bingoList ]

    missingNumbers = []

    playerStats.write('<div class="p-3 table-responsive">')
    playerStats.write('<table class="table table-bordered table-sm caption-top">')
    playerStats.write('<tbody>')
    for i in range( 0, formattedBingoList[-1]+1 ):
        if i % 10 == 0:
            playerStats.write('<tr style="border: 1px solid black;">')
        if i in formattedBingoList:
            playerStats.write('<td style="border: 1px solid black; background-color: lightgreen;">'+str(i)+'</td>')
        else:
            playerStats.write('<td style="border: 1px solid black; background-color: tomato;">'+str(i)+'</td>')
        
    playerStats.write('</tbody></table>')
    
    playerStats.write("</div>")

    accordionHelperEnd()

# Currently outputing as a table. I think this information would work better as a graph
# Or maybe show every 10 runs? 0,1,10,20 etc
# Probably not point showing it past 50 tbh
# Batting stats by NohitBrohitLine
def stats_Batting_NohitBrohitLine(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"

    caption = "Nohit/Brohit Line"

    discipline = "Batting"

    highScore = dbQuery(playerDB, "SELECT max(Runs) FROM Batting")[0][0]

    scoreList = dbQuery(playerDB, "SELECT DISTINCT Runs FROM Batting ORDER BY Runs ASC")
    formattedscoreList = [ i[0] for i in scoreList ]

    stepList = [0,1,10,20,30,40,50]

    indexCount = 0
    for i in stepList:#range(0, highScore):
        #if i in formattedscoreList:

        inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE Runs >= " + str(i) )

        multiLineDisciplineHelper(discipline, inningsList, "Score >=", str(i), indexCount, caption, "brohit")

        indexCount += 1
    
    playerStats.write("</tbody></table>")
    playerStats.write("</div>")

    accordionHelperEnd()

####################
## Bowling Only Stats

def bowlingWorkloadHelper(playerID, numSeasons=False):

    playerDB = "Player Databases/" + str(playerID) + ".db"

    if numSeasons:

        matchList = []

        seasonList = dbQuery(playerDB, "SELECT DISTINCT Season FROM Matches")

        for season in sorted(seasonList)[-numSeasons:]:

            matchList += dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Season='" + season[0] + "'")
            formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

        overs = dbQuery(playerDB, "SELECT SUM(Cast(Overs as Int)) FROM Bowling WHERE MatchID IN " + formattedMatchList)[0][0]
        innings = dbQuery(playerDB, "SELECT COUNT(Cast(Overs as Int)) FROM Bowling WHERE MatchID IN " + formattedMatchList)[0][0]
        maxOvers = dbQuery(playerDB, "SELECT Max(Cast(Overs as Int)) FROM Bowling WHERE MatchID IN " + formattedMatchList)[0][0]
        games = len(matchList)


    else:
        overs = dbQuery(playerDB, "SELECT SUM(Cast(Overs as Int)) FROM Bowling")[0][0]
        innings = dbQuery(playerDB, "SELECT COUNT(Cast(Overs as Int)) FROM Bowling")[0][0]
        maxOvers = dbQuery(playerDB, "SELECT Max(Cast(Overs as Int)) FROM Bowling")[0][0]
        games = dbQuery(playerDB, "SELECT NumMatches FROM PlayerInfo")[0][0]

    if overs:
        opg = round(overs/games ,2)
        opi = round(overs/innings,2)
    else:
        opg = "N/A"
        opi = "N/A"

    playerStats.write("<p>")

    playerStats.write( "Average Overs Bowled Per Game: " + str( opg ) + "<br />")
    playerStats.write( "Average Overs Bowled Per Innings: " + str( opi ) + "<br />")
    playerStats.write( "Max Overs Bowled In One Innings: " + str(maxOvers) + "<br />")
    
    playerStats.write("</p>")


# Scrap this and bring these stats into Discipline Helper?
# Would allow viewing these stats for recent/season/grade etc
# Bowling Workload stats - FIX THIS FOR HTML OUTPUT
def stats_Bowling_Workload(playerID):

    accordionHelperStart("Bowling - Overs Bowled Per Game", showAll) 

    playerStats.write('<div class="p-3 table-responsive">')

    playerStats.write('Last/Current Season')
    bowlingWorkloadHelper(playerID,1)

    playerStats.write('Overall')
    bowlingWorkloadHelper(playerID)

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
    var clubCards = document.getElementsByClassName("club");
    for (var i = 0; i < clubCards.length; i++) {
        clubCards[i].hidden = true;
        };

    // Opponent
    var opponentCards = document.getElementsByClassName("opponent");
    for (var i = 0; i < opponentCards.length; i++) {
        opponentCards[i].hidden = true;
        };

}
document.addEventListener("keydown", function(){
    var x=event.keyCode || event.which;
    if(x==72)
    {
    var accordions = document.getElementsByClassName("accordion-item");
    for (var i = 0; i < accordions.length; i++)
    {
        accordions[i].hidden = false;
    }
    }
}) 
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
    # Hard/potentially impossible to calculate
    # FOW data doesn't have overs (when it is even there)

## Need Fetch Pass 3

# Stats by TeamMate
def stats_TeamMate(playerID, minGames):
    print("TODO")

## Need Additional Information

# Stats by Captain
def stats_Captain(playerID):
    print("TODO")


## Template 
# Stats by THING
def stats_THING(playerID):
    print("TODO")
