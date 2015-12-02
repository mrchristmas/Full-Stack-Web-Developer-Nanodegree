#!/usr/bin/env python
#
# sim.py -- simulation of a Swiss-system tournament
#

from tournament import *
from random import getrandbits

def playMatch(player1, player2):
    """
    Generates and reports the results of a 2 player match;
    Probability of winning is assumed equal for each player.
    """
    if not getrandbits(1):
        reportMatch(player1, player2)
    else:
        reportMatch(player2, player1)

def playRound():
    """
    Plays a complete round, by generating match results for all pairings.
    """
    players = swissPairings()
    for row in players:
        playMatch(row[0], row[2])
    recordBye(getByePlayer())


if __name__ == '__main__':
    # Begin execution of code
    deleteMatches()
    deletePlayers()
    registerPlayer("Agnes")
    registerPlayer("Bertha")
    registerPlayer("Cynthia")
    registerPlayer("Dolores")
    registerPlayer("Edith")
    registerPlayer("Francine")
    registerPlayer("Gertrude")
    registerPlayer("Helga")
    registerPlayer("Izzy")

    tournament_round = 1

    db = connect()
    c = db.cursor()

    count = countPlayers()

    while count>1:
        print 'Playing Round %s...' % tournament_round
        playRound()

        c.execute("SELECT COUNT(*) FROM Players WHERE Losses=0;")
        count = c.fetchone()[0]

        tournament_round = tournament_round + 1

    db.close()

    print 'Simulation complete.'
