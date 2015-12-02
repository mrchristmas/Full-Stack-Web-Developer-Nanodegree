-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

--Drop if exists and Create tournament database
\c vagrant
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament

--Create Tournament table
CREATE TABLE Tournament (
    TournamentID serial primary key,
    Name varchar);

--Create Players table
CREATE TABLE Players (
    PlayerID serial primary key,
    -- TournamentID int references Tournament ON DELETE CASCADE,
    Name varchar,
    Wins int DEFAULT 0,
    Draws int DEFAULT 0,
    Losses int DEFAULT 0,
    OMW int DEFAULT 0);

--Create Matches table
CREATE TABLE Matches (
    MatchID serial primary key,
    -- TournamentID int references Tournament ON DELETE CASCADE,
    Player1ID int references Players(PlayerID) ON DELETE CASCADE,
    Player2ID int references Players(PlayerID) ON DELETE CASCADE,
    WinnerID int);

-- Create Ordered Standings View
/* This view pulls tournament standings ordered in terms of player
points, accounting for total matches played.  Assuming two players
with the same number of wins and draws, the better player is the one
who has played fewer matches.
*/
CREATE VIEW Standings_Ordered AS
    SELECT
        PlayerID,
        Name,
        Wins,
        Losses,
        Draws,
        Wins+Losses+Draws as Matches
    FROM
        Players
    ORDER BY
        Wins DESC, Draws DESC, Matches;


CREATE VIEW Player_Eligible_For_Bye AS
    SELECT
        PlayerID,
        Name,
        Wins,
        Losses,
        Draws,
        Wins+Losses+Draws as Matches
    FROM
        Players P
    LEFT JOIN
        Matches M1 on P.PlayerID=M1.Player1ID and P.PlayerID=M1.Player2ID
    LEFT JOIN
        Matches M2 on P.PlayerID=M2.Player1ID and P.PlayerID=M2.Player2ID
    WHERE
        M1.Player1ID is null and M2.Player1ID is null
    ORDER BY
        Matches, Wins, Draws
    LIMIT 1;
