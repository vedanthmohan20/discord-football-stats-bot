To run the bot type "py vedsbot.py" in your command prompt.

List of functionalities offered by the bot:
CODES: Shows team or competition code.
  .codes - Lists codes of all available competitions.
  .codes {competitionCode} - Lists codes of all teams in the given competition.
  .codes {competitionCode} {season} - Lists codes of all teams in the given competition in the given season (YYYY).

TABLES:  Shows a competitions standings.
  .table {s} {competitionCode} - Lists the short form standings of the competition.
  .table {l} {competitionCode} - Lists the long form standings of the competition.

FIXTURES: Shows the upcoming fixtures of a team or competition.
  .fix {teamCode} - Lists all scheduled fixtures for the next 2 weeks of the team.
  .fix {competitionCode} - Lists all scheduled fixtures of the latest matchday of the competition.
  .fix {specialCompetitionCode} {limit} - Lists the next 0 ≤ {limit} ≤ 20 scheduled fixtures of the special competition.

LIVE: Shows matches that are in play.
  .live {teamCode} - Lists the match that is currently in play for the team if there is one.
  .live {competitionCode} - Lists the live matches in the competition.

RESULTS:  Shows the past match results of a team or competition.
  .res {teamCode} - Lists the past 3 match results of the team.
  .res {teamCode} {limit} - Lists the past 0 ≤ {limit} ≤ 20 match results of the team.
  .res {competitionCode} - Lists the results of the competition for the past 3 days.
  .res {competitionCode} {limit} - Lists the results of the competition for the past 0 ≤ {limit} ≤ 10 days.
  .res {specialCompetitionCode} - Lists the past 3 match results of the special competition.
  .res {specialCompetitionCode} {limit} - Lists the past 0 ≤ {limit} ≤ 20 match results of the special competition.
  
SCORERS: Shows the top scorers of a competition.
  .scorers {competitionCode} - Lists the top 10 goal scorers of the competition.

Available competitions: Premier League (England), La Liga (Spain), Serie-A (Italy), Bundesliga (Germany), Ligue 1 (France)
Available special competitions: UEFA Champions League (Europe), FIFA World Cup (World)

Codes of popular teams:
MUFC : 66, MCFC : 65, LFC : 64, CFC : 61, AFC : 57, THFC : 73
MAD : 86, FCB : 81, ATM : 78
JUVE : 109, ACM : 98, INT : 108
BAY : 5, BVB : 4
PSG : 524