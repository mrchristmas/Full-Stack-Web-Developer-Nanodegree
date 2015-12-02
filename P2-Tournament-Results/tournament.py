#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    c =  db.cursor()
    c.execute("DELETE FROM Matches;")
    db.commit()
    db.close()


def deletePlayers():
    """Remove all the player records from the database."""
    db = connect()
    c =  db.cursor()
    c.execute("DELETE FROM Players;")
    db.commit()
    db.close()

def countPlayers():
    """Returns the number of players currently registered."""
    db = connect()
    c =  db.cursor()
    c.execute("SELECT count(*) as Count FROM Players;")
    count = c.fetchone()
    db.close()
    return int(count[0])

def registerPlayer(name):
    #Adds a player to the tournament database.
    db = connect()
    c =  db.cursor()
    c.execute("INSERT INTO Players (Name) VALUES (%s)", (name,))
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
    db = connect()
    c =  db.cursor()

    c.execute("SELECT PlayerID, Name, Wins, Matches FROM Standings_Ordered;")
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
    db = connect()
    c =  db.cursor()

    #
    if draw != 0:
        c.execute("INSERT INTO Matches (Player1ID, Player2ID, WinnerID)"
        "VALUES %s;", ((winner, loser, 0),))

        c.execute("UPDATE Players"
        " SET Draws = Draws+1"
        " WHERE PlayerID in %s;",((winner,loser),))
    else:
        c.execute("INSERT INTO Matches (Player1ID, Player2ID, WinnerID)"
            "VALUES %s;", ((winner, loser, winner),))

        c.execute("UPDATE Players"
            " SET Wins = Wins+1"
            " WHERE PlayerID = %s;",(winner,))

        c.execute("UPDATE Players"
            " SET Losses = Losses+1"
            " WHERE PlayerID = %s;",(loser,))

    db.commit()
    db.close()


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    The pairing system will not allow for a rematch.  Thas is, a player may not
    play the same opponent more than once per tournament.  If all players have
    already played each other, then the pairings will allow for rematches.

    """
    matches = []

    # Pull list of players
    players = playerStandings()

    # Pair players, accounting for no re-matches
    while len(players)>1:
        player1 = players.pop(0)
        i = 0
        newPair = ()
        while len(newPair) < 2:
            if i == len(players):
                player2 = players.pop(0)
                newPair = (player1[0], player1[1], player2[0], player2[1])
                matches.append(newPair)
            else:
                player2check = players[i]
                if (player2check[0] in pastOpponents(player1[0])):
                    i = i + 1
                else:
                    player2 = players.pop(i)
                    newPair = (player1[0], player1[1], player2[0], player2[1])
                    matches.append(newPair)
    return matches


def pastOpponents(player):
    # Returns list of players which 'player' has already played
    db = connect()
    c = db.cursor()
    c.execute(
        " SELECT Player2ID Players"
        " FROM Matches"
        " WHERE Player1ID = %s AND Player1ID <> Player2ID"
        " UNION"
        " SELECT Player1ID Players"
        " FROM Matches"
        " WHERE Player2ID = %s AND Player1ID <> Player2ID;"
        , ((player), (player),))

    opponents = c.fetchall()

    db.close()

    return [row[0] for row in opponents]


def getByePlayer():
    """ Returns player who is eligible for a bye.  Typically this will be the
    player in last place.  If this player has already had a bye, then
    the next-to-last place player receives the bye.  This process continues
    to move up the standings until it finds a player without a bye.
    """
    db = connect()
    c = db.cursor()
    c.execute("SELECT PlayerID FROM Player_Eligible_For_Bye;")
    player = c.fetchone()[0]
    db.close()

    return player


def recordBye(player):
    # Records a bye for given player
    db = connect()
    c =  db.cursor()

    # Insert 'bye' record into Matches table. Player1 = Player2
    c.execute("INSERT INTO Matches (Player1ID, Player2ID, WinnerID)"
        "VALUES %s;", ((player, player, player),))

    # Update standings for player on bye
    c.execute("UPDATE Players"
        " SET Wins = Wins+1"
        " WHERE PlayerID = %s;",(player,))

    db.commit()
    db.close()
