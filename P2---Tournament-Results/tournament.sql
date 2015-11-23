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
    Name text);

--Create Players table
CREATE TABLE Players (
    PlayerID serial primary key,
    Name text);

--Create Standings table
CREATE TABLE Standings (
    RowID serial,
    -- TournamentID int references Tournament ON DELETE CASCADE,
    PlayerID int references Players ON DELETE CASCADE,
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

--Create Ordered Standings View
CREATE VIEW Standings_Ordered AS
    SELECT
        S.PlayerID,
        P.Name,
        S.Wins,
        S.Draws,
        S.Wins+S.Losses+S.Draws as Matches
    FROM
        Standings S
    INNER JOIN
        Players P on S.PlayerID=P.PlayerID
    ORDER BY
        S.Wins DESC, S.Draws DESC, Matches;
