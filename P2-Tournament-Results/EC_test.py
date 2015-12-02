#!/usr/bin/env python
#
# Test cases for tournament.py

from tournament import *
from random import getrandbits

def testRematches():
    deleteMatches()
    deletePlayers()
    registerPlayer("Agnes")
    registerPlayer("Bertha")
    registerPlayer("Cynthia")
    registerPlayer("Dolores")

    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]

    reportMatch(id1, id2)
    reportMatch(id3, id4)

    """
    Standings after Round 1
    id1     1   0
    id3     1   0
    id2     0   1
    id4     0   1
    """

    reportMatch(id3, id1)
    reportMatch(id2, id4)

    """
    Standings after Round 2
    id3     2   0
    id1     1   1
    id2     1   1
    id4     0   2
    """

    pairings = swissPairings()

    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings

    correct_pairs = set([frozenset([id3, id2]), frozenset([id1, id4])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])

    if correct_pairs != actual_pairs:
        raise ValueError(
            "Pairings resulted in a re-match after two rounds.")


    reportMatch(id2, id3)
    reportMatch(id4, id1)

    """
    Standings after Round 3
    id2     2   1
    id3     2   1
    id1     1   2
    id4     1   2
    """

    pairings = swissPairings()

    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings

    correct_pairs = set([frozenset([id3, id2]), frozenset([id1, id4])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])

    if correct_pairs != actual_pairs:
        raise ValueError(
            "Pairings resulted in a re-match after three rounds.")
    print "EC1. Pairings correctly did not include any rematches."


def testCheckByes():
    deleteMatches()
    deletePlayers()
    registerPlayer("Agnes")
    registerPlayer("Bertha")
    registerPlayer("Cynthia")
    registerPlayer("Dolores")
    registerPlayer("Edith")

    #Give everyone a win except for last place player
    standings = playerStandings()
    [id1, id2, id3, id4, id5] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4)

    pairings = swissPairings()
    if len(pairings) != 2:
        raise ValueError(
            "For five players, swissPairings should return two pairs of two.")

    if id5 != getByePlayer():
        raise ValueError(
            "Last place player is not the player to be given bye.")

    recordBye(id5)

    standings = playerStandings()

    #Again, give everyone a win except for id5
    standings = playerStandings()
    [id1, id2, id3, id4, id5] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id2, id3)
    reportMatch(id3, id4)
    reportMatch(id4, id1)

    print "EC2. Given five players, two pairs created and bye given to correct player."


def testReportMatches():
    deleteMatches()
    deletePlayers()
    registerPlayer("Bruno Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    registerPlayer("Diane Grant")
    registerPlayer("Edgar Mier")
    registerPlayer("Frank Stevens")

    #Pull initial standings
    standings = playerStandings()
    [id1, id2, id3, id4, id5, id6] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4)
    reportMatch(id5, id6, 1)

    #Pull updated standings, including draws
    db = connect()
    c = db.cursor()
    c.execute("SELECT PlayerID, Name, Wins, Draws, Matches FROM Standings_Ordered;")
    standings = c.fetchall()
    db.close()

    #Test match results
    for (i, n, w, d, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id4) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
        elif i in (id5, id6) and d !=1:
            raise ValueError("Each match draw should have one draw recorded.")
    print "EC3. Players in matches resulting in a draw have updated standings."


if __name__ == '__main__':
    testRematches()
    testCheckByes()
    testReportMatches() #Includes test for Draws
    print "Success!  All tests pass!"
