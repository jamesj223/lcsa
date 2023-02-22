#!python3
###############################################################################
# cricket.py - A scraper and a stats analyzer for local cricket
# jamesj223

###############################################################################
# Imports

import os

from cricket import *

###############################################################################
# User Input

debug = False

wipe = False # TODO Determine whether to wipe based on schema change or not
fetch = True # Deprecated?
analysis = True
#rebuildIndex = True # Deprecated

# Get Player ID
#playerID = int(input("Enter PlayerID: "))

# Comma Separated Player List
playerIDList = [

]

###############################################################################
# Main

startTime = datetime.now()
print("Start - " + str(startTime))

print("")

createDirectory("Player Databases")

createDirectory("Player Stats")

numPlayers = str(len(playerIDList))

print(numPlayers + " players in playerIDList")

playerLoopCounter = 0

for playerID in playerIDList:

    playerDB = "Player Databases/" + str(playerID) + ".db"

    createDatabase(playerID, wipe)

    oldGamesPlayed = stats_PlayerInfo(playerID)

    fetchPlayerInfo(playerID)

    newGamesPlayed = stats_PlayerInfo(playerID)

    difference = newGamesPlayed - oldGamesPlayed

    # fetch flag deprecated. Replaced with difference check.
    #if fetch:

    # difference check disabled to try a new behaviour. 
    # Default behaviour will now be: if difference is less than 10 (including 0 now) fetch the 2 most recent seaons.
    # Combined with changing the sql from "INSERT OR IGNORE" to "REPLACE"
    #if difference:
    if True:

        populateDatabaseFirstPass(playerID, difference)

        #populateDatabaseSecondPass(playerID)

        #populateDatabaseThirdPass(playerID)

    if analysis:

        # Open/Clean Player Stats File
        playerName = getPlayerName(playerID)
        playerStats = open("Player Stats/" + str(playerID) + "-" + playerName.replace(' ', '-').lower() + ".html", "w")
        setGlobals(playerStats)
        writeHTMLTemplatePart1()
        playerStats.close()

        # Re Open in append mode, and then set as global
        playerStats = open("Player Stats/" + str(playerID) + "-" + playerName.replace(' ', '-').lower() + ".html", "a")
        setGlobals(playerStats) 

        idAndNameString = str(playerID) + " - " + playerName
        writeHTMLTemplatePart2(idAndNameString, newGamesPlayed)

        ### Batting

        ## Normal Stats
        stats_Recent(playerID, "Batting", 5)
        stats_Overall(playerID, "Batting")
        stats_Batting_Graphs(playerID)

        stats_Club(playerID,"Batting")
        #stats_Opponent(playerID,"Batting")
        stats_Grade(playerID,"Batting")
        #stats_HomeOrAway(playerID,"Batting")

        ## Batting Only Functions
        stats_Batting_DismissalBreakdown(playerID)
        stats_Batting_Position(playerID)
        #stats_Batting_NohitBrohitLine(playerID)
        #stats_Batting_Bingo(playerID)

        ## Move specific functions to bottom of page
        stats_Season(playerID, "Batting")
        stats_JuniorSenior(playerID, "Batting")

        writeHTMLTemplatePart3()

        ### Bowling

        ## Normal Stats
        stats_Recent(playerID, "Bowling", 5)
        stats_Overall(playerID, "Bowling")
        stats_Bowling_Graphs(playerID)

        stats_Club(playerID,"Bowling")
        #stats_Opponent(playerID,"Bowling")
        stats_Grade(playerID,"Bowling")
        #stats_HomeOrAway(playerID,"Bowling")

        ## Bowling Only
        stats_Bowling_Workload(playerID)

        ## Move specific functions to bottom of page
        stats_Season(playerID, "Bowling")
        stats_JuniorSenior(playerID, "Bowling")

        writeHTMLTemplatePart4()
        playerStats.close()

    playerLoopCounter += 1
    print(str(playerLoopCounter) + " players completed out of " + numPlayers)

rebuildIndex()

endTime = datetime.now()
print("End - " + str(endTime))
print("Took: " + str( endTime - startTime ))
