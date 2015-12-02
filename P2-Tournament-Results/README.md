# Project 2 - Tournament Results
Python module that uses a PostgreSQL database to keep track of players, matches, and results in a tournament.

The tournament uses the Swiss system for pairing up players in each round: players are not eliminated, and each player should be paired with another player with the same number of wins, or as close as possible.

This project consists of two parts: defining the database schema (SQL table definitions), and writing the code that will use it.

### How can I get the code?
Feel free to Fork your own version of this code and play around within the three files.

### What are the technical requirements?
* Python 2.7 (libraries: psycopg2, bleach)
* PostgreSQL
* psql

### What's Included
Within the download you'll find the following files:
```
tournament.sql
tournament.py
tournament_test.py
EC_test.py
sim.py
```

### How do I run the application?
1. Initialize the database using psql in command line:  psql -f tournament.sql
2. Validate the tournament.py module and the tournament database schema, by running the unit tests file in command line:  python tournament_test.py
3. Optionally, run a simulator to create random tournament results:  python sim.py
Query the results in the tournament database:  select * from standings_ordered;
4. Optionally, execute the individual functions within the tournament.py module to interact with the database.


### Application Features
* Keep track of players and results for a Swiss-Style tournament (popular with Chess, Go, and MTG tournaments)
* Automatically determine round-by-round pairings - each player is paired with an opponent who has won the same number of matches
* Pairings will seek to prevent rematches between players with similar records
* If an odd number of participants is registered, the application intelligently assigns a 'bye' to the appropriate player
* Standings keeps track of players' Wins, Losses, and even Draws
* Match results are tracked for history and later data discovery
