#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import bleach


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()
    c.execute("DELETE FROM Matches;")
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()
    c.execute("DELETE FROM Players;")
    db.commit()
    db.close()

def countPlayers():
    """Returns the number of players currently registered."""
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()
    c.execute("SELECT count(*) as Count FROM Standings;")
    count = c.fetchone()
    db.close()
    return int(count[0])

def registerPlayer(name):
    #Adds a player to the tournament database.
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()
    c.execute("INSERT INTO Players (Name) VALUES (%s);", (bleach.clean(name),))
    c.execute("INSERT INTO Standings (PlayerID)"
        "SELECT MAX(PlayerID) FROM Players;")
    db.commit()
    db.close()

def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()

    c.execute("SELECT * FROM Standings_Ordered;")
    standings = c.fetchall()
    db.close()
    return standings

def reportMatch(winner, loser, draw=0):
    """Records the outcome of a single match between two players.
    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
      draw (optional):  if specified and non-zero, assume draw.
    """
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()

    #
    if draw != 0:
        c.execute("INSERT INTO Matches (Player1ID, Player2ID, WinnerID)"
        "VALUES (%s, %s, %s);", ((winner,), (loser,), 0))
        db.commit()

        c.execute("UPDATE Standings"
        " SET Draws = Draws+1"
        " WHERE Standings.PlayerID in %s;",((winner,loser),))
        db.commit()

    else:
        c.execute("INSERT INTO Matches (Player1ID, Player2ID, WinnerID)"
            "VALUES (%s, %s, %s);", ((winner,), (loser,), (winner,)))
        db.commit()

        c.execute("UPDATE Standings"
            " SET Wins = Wins+1"
            " WHERE Standings.PlayerID = %s;",(winner,))
        db.commit()

        c.execute("UPDATE Standings"
            " SET Losses = Losses+1"
            " WHERE Standings.PlayerID = %s;",(loser,))
        db.commit()

    db.close()

def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    """

    # Pull list of players
    players = playerStandings()

    # Check if tournament contains an odd number of players
    if len(players) % 2 != 0:
        #Number of players is odd, so identify who receives a bye
        #Find a player eligible for a bye
        i = 1
        while i<len(players):
            if checkForBye(players[-i][0])==True:
                i = i+1
            else:
                # Record a bye for eligible player
                recordBye(players[-i][0])
                # Remove player from the list of players awaiting pairings
                del players[-i]
                break

    # Proceed to pair as normal
    num_matches = len(players) / 2
    matches = []

    for i in range(0, num_matches):
        matches.append((players[i*2][0],players[i*2][1],players[i*2+1][0],players[i*2+1][1]))

    return matches


def checkForBye(player):
    # Checks the Matches table in tournament database
    # If Player1 = Player2, then it is assumed that the match was a bye
    # Returns True if player has already had a bye
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()
    c.execute("SELECT Count(1)"
        " FROM Matches"
        " WHERE Player1ID=Player2ID and Player1ID=%s;", (player,))
    count = int(c.fetchone()[0])
    db.close()

    if count != 0:
        return True
    else:
        return False

def recordBye(player):
    # Records a bye for given player
    db = psycopg2.connect("dbname=tournament")
    c =  db.cursor()

    # Insert 'bye' record into Matches table. Player1 = Player2
    c.execute("INSERT INTO Matches (Player1ID, Player2ID, WinnerID)"
        "VALUES (%s, %s, %s);", ((player,), (player,), (player,)))
    db.commit()

    # Update standings for player on bye
    c.execute("UPDATE Standings"
        " SET Wins = Wins+1"
        " WHERE Standings.PlayerID = %s;",(player,))
    db.commit()

    db.close()
    print "Bye recorded for PlayerID=%s" % (player)
