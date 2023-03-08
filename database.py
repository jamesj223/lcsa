#!python3
###############################################################################
# database.py - Database stuff for LCSA 
# jamesj223

###############################################################################
# Imports

import os, sqlite3

###############################################################################
# User Input / Config

debug = False

verbose = False

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

# Creates a directory d if it doesnt already exist
def createDirectory(d,parent=None):
    if not os.path.exists(d):
        os.mkdir(d)

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
    if verbose:
        print(str(c.rowcount) + " rows affected")
    conn.close()

    return returnValue

# Get player name from the database
def getPlayerName(playerID):
    playerDB = "Player Databases/" + str(playerID) + ".db"
    
    query = "SELECT FirstName, LastName FROM PlayerInfo"
    result = dbQuery(playerDB,query)

    fullName = str(result[0][0]) + " " + str(result[0][1])

    return fullName
