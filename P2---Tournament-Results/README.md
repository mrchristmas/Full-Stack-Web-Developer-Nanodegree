# Project 2 - Tournament Results
Python module that uses the PostgreSQL database to keep track of players and matches in a game tournament.

The game tournament will use the Swiss system for pairing up players in each round: players are not eliminated, and each player should be paired with another player with the same number of wins, or as close as possible.

This project has two parts: defining the database schema (SQL table definitions), and writing the code that will use it.

### How can I get the code?
Feel free to Fork your own version of this code and play around within the three files.

### What are the technical requirements?
Python 2.7
Python libraries: psycopg2
PostgreSQL
psql

### What's Included
Within the download you'll find the following files:
```
tournament.py
tournament.sql
tournament_test.py
```

### How do I run the application?
First step is to initialize the database, by running tournament.sql (this can be done via psql in the command line).
The tournament_test.py file contains a series of unit tests to validate the tournament.py module and the tournament database schema.
Optionally, execute the individual functions within the tournament.py module to interact with the database.

### Application Features
* Keep track of players and results for a Swiss-Style tournament (popular with Chess, Go, and MTG tournaments)
* Automatically determine round-by-round pairings - each player is paired with an opponent who has won the same number of matches
* If an odd number of participants is registered, the application intelligently assigns a 'bye' to the appropriate player
* Standings keeps track of players' Wins, Losses, and even Draws
* Match results are tracked for history and later data discovery
