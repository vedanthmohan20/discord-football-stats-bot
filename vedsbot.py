# Football data provided by the Football-Data.org API

import json
import http.client
from discord.ext import tasks
from datetime import datetime
from datetime import timedelta
from discord.ext import commands

TOKEN = "YOUR_BOT_TOKEN"
APIKEY = "YOUR_API_KEY" # you can get it for free from football-data.org
MATCH_ALERT_CHANNEL = "YOUR_CHANNEL_ID" # REMOVE THE QUOTES. enter the channel id to which you want to send the match alerts
# Enter the team codes of the teams for which you want to recieve daily match alerts. Eg: if you want alerts for Man Utd and Barcelona
# matchs, teamMatchAlertList = [66, 81]
# popular English team codes: THFC=73, MUFC=66, MCFC=65, LFC=64, CFC=61, AFC=57
# popular Spanish team codes: MAD=86, FCB=81, ATM=78
# popular Italian team codes: JUV=109, INT=108, ACM=98 
# popular German team codes: BAY=5, BVB=4
# popular French team codes: PSG=524
teamMatchAlertList = []

# function to return the appropriate json from the Football-Data.org API
def get_json(url):
	connection = http.client.HTTPConnection('api.football-data.org')
	headers = { 'X-Auth-Token': APIKEY }
	connection.request('GET', url, None, headers )
	response = json.loads(connection.getresponse().read().decode())
	return response

# function to return the short form standings for the given competition
def get_short_table(competitionCode):
    # adjusting the competition code
    if competitionCode == "LL": competitionCode = "PD"
    elif competitionCode == "BL" or competitionCode == "FL": competitionCode += "1"
    
    # getting the standings json for the provided competition
    url = "/v2/competitions/{}/standings".format(competitionCode)
    response = get_json(url)

	# getting the length of the longest name (to format the final output)
    longestName = 0
    for team in response["standings"][0]["table"]:
        if len(team["team"]["name"]) > longestName:
            longestName = len(team["team"]["name"])

    # creating the short form competition standings
    tableHeader = "`\n# | TEAM NAME" + " " * (longestName-9) + " | MP | PO`\n"
    tableBody = "\n```"
    for team in response["standings"][0]["table"]:
        pos, name, mp, po = str(team["position"]), team["team"]["name"], str(team["playedGames"]), str(team["points"])
        tableRow = pos + " "*(2-len(pos)) + "| " + name + " "*(longestName-len(name)) + " | " + mp + " "*(2-len(mp)) + " | " + po + "\n"
        tableBody += tableRow
    tableBody += "```"

    return tableHeader + tableBody

# function to return the long form standings for the given competition
def get_long_table(competitionCode):
    # adjusting the competition code
    if competitionCode == "LL": competitionCode = "PD"
    elif competitionCode == "BL" or competitionCode == "FL": competitionCode += "1"
    
    # getting the standings json for the provided competition
    url = "/v2/competitions/{}/standings".format(competitionCode)
    response = get_json(url)

	# getting the length of the longest name (to format the final output)
    longestName = 0
    for team in response["standings"][0]["table"]:
        if len(team["team"]["name"]) > longestName:
            longestName = len(team["team"]["name"])

    # creating the long form competition standings
    tableHeader = "`\n# | TEAM NAME" + " " * (longestName-9) + " | MP | MW | MD | ML | PO | GD |FORM `\n"
    tableBody = "\n```"
    for team in response["standings"][0]["table"]:
        pos, name, mp, mw = str(team["position"]), team["team"]["name"], str(team["playedGames"]), str(team["won"])
        md, ml, po, gd = str(team["draw"]), str(team["lost"]), str(team["points"]), str(team["goalDifference"])
        tableRow = pos + " "*(2-len(pos)) + "| " + name + " "*(longestName-len(name)) + " | " + mp + " "*(2-len(mp)) + " | " + mw
        tableRow += " "*(2-len(mw)) + " | " + md + " "*(2-len(md)) + " | " + ml + " "*(2-len(ml)) + " | " + po + " "*(2-len(po)) + " |"
        tableRow += gd + " "*(4-len(gd)) + "|"
        for i in range(0, len(team["form"]), 2):
            tableRow += team["form"][i]
        tableRow += "\n"
        tableBody += tableRow
    tableBody += "```"

    return tableHeader + tableBody
    
# function to return the team codes of all teams in a given competition in the given season
def get_competition_team_codes(competitionCode, season):
    # adjusting the competition code
    if competitionCode == "LL": competitionCode = "PD"
    elif competitionCode == "BL" or competitionCode == "FL": competitionCode += "1"

    # getting the team codes json for the provided competition
    url = "/v2/competitions/{}/teams".format(competitionCode)
    if season != "": url += "?season={}".format(season)
    response = get_json(url)
    if "error" in response or "errorCode" in response: return "There is no data available for the given season."

    # Sorting the teams in the competition lexicographically
    teamCode_team = {}
    longestId = 0
    for team in response["teams"]:
        teamCode_team[team["id"]] = team["name"]
        longestId = max(longestId, len(str(team["id"])))
    teamCode_team = sorted(teamCode_team.items(), key = lambda kv:(kv[1], kv[0]))

    # creating the final list of teams and their codes
    competitionTeamCodes = "```\n"
    for key in teamCode_team:
        competitionTeamCodes += " "*(longestId-len(str(key[0]))) + str(key[0]) + " " + key[1] + "\n"
    competitionTeamCodes += "```"

    return competitionTeamCodes

# function to return the fixtures of the given team for the next two weeks
def get_team_fixtures(teamCode):
    # getting the team's fixtures
    dateFrom = str(datetime.today().strftime("%Y-%m-%d"))
    dateTo = str((datetime.today() + timedelta(days = 14)).strftime("%Y-%m-%d"))
    url = "/v2/teams/{}/matches?status=SCHEDULED&dateFrom={}&dateTo={}".format(teamCode, dateFrom, dateTo)
    response = get_json(url)
    if "errorCode" in response: return "Invalid team code."
    if response["count"] == 0: return "There are no fixtures scheduled for this team."

    # creating the team's scheduled fixtures list
    teamFixtures = "```\n"
    for match in response["matches"]:
        competitionName = match["competition"]["name"]
        if competitionName == "Primera Division": competitionName = "La Liga" 

        # converting match time from utc to ist (+5.5h)
        utcString = match["utcDate"][2:10] + " " + match["utcDate"][11:16]
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        # converting the date and time to the desired format
        istDate = ist.strftime('%a %d %h')
        istTime = ist.strftime("%I:%M %p")

        # getting and adding the current scheduled match's information to the list of scheduled matches
        matchInfo = istDate + " | "
        matchInfo += competitionName + "\n"
        matchInfo += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n"
        matchInfo += istTime + "\n\n"
        teamFixtures += matchInfo
    teamFixtures += "```"

    if teamFixtures == "```\n```": return "This team has no remaining matches for the season."
    return teamFixtures

# funcion to return the scheduled fixtures of the latest matchday of the given competition
def get_competition_fixtures(competitionCode):
    # adjusting the competition code
    if competitionCode == "LL": competitionCode = "PD"
    elif competitionCode == "BL" or competitionCode == "FL": competitionCode += "1"

    # getting the scheduled competition fixtures json
    url = "/v2/competitions/{}/matches?status=SCHEDULED".format(competitionCode)
    response = get_json(url) # getting the particular competitions fixtures json
    if response["count"] == 0: return "There are no fixtures scheduled for this competition."

    # creating the scheduled fixtures message
    competitionFixtures = "`MATCHDAY {}`\n```\n".format(response["matches"][0]["season"]["currentMatchday"])
    for match in response["matches"]:
        # converting match time from utc to ist (+5.5h)
        utcString = match["utcDate"][2:10] + " " + match["utcDate"][11:16]
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        # converting the date and time to the desired format
        istDate = ist.strftime('%a %d %h')
        istTime = ist.strftime("%I:%M %p")

        # getting and adding the current match to the list of scheduled fixtures
        if match["matchday"] <= match["season"]["currentMatchday"]:
            matchInfo = istDate + " | " + istTime + "\n"
            matchInfo += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n\n"
            competitionFixtures += matchInfo
        else: break
    competitionFixtures += "```"

    return competitionFixtures

# function to return the next 0 ≤ {limit} ≤ 20 scheduled fixtures of the given special competition
def get_special_competition_fixtures(specialCompetitionCode, limit):
    # adjusting the limit
    if limit == "": limit = 3
    if int(limit) <= 0: return "What the hell was the point of that?" 
    if int(limit) > 20: limit = 20

    # getting the provided special competitions's scheduled fixtures json
    url = "/v2/competitions/{}/matches?status=SCHEDULED&limit={}".format(specialCompetitionCode, limit)
    response = get_json(url)
    if response["count"] == 0: return "There are no fixtures scheduled for this competition."
    
    # creating the list of scheduled fixtures
    specialCompetitionFixtures = "```\n"
    for match in response["matches"]:
        # converting match time from utc to ist (+5.5h)
        utcString = match["utcDate"][2:10] + " " + match["utcDate"][11:16]
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        # converting the date and time to the desired format
        istDate = ist.strftime('%a %d %h')
        istTime = ist.strftime("%I:%M %p")

        # getting and adding the information for the current match to the list of scheduled fixtures
        matchStage = match["stage"].split("_")
        matchInfo = ""
        for word in matchStage:
            matchInfo += word + " "
        if match["group"] != None and (matchInfo.strip(" ").lower() == "quarter finals" or matchInfo.strip(" ").lower() == "semi finals" or matchInfo.strip(" ").lower() == match["group"].lower()):
            matchInfo = match["group"] + "\n"
        else:
            if match["group"] != None: matchInfo += "| " + match["group"] + "\n"
            else: matchInfo += "\n"
        matchInfo += istDate + " | " + istTime + "\n"
        matchInfo += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n\n"
        specialCompetitionFixtures += matchInfo
    specialCompetitionFixtures += "```"

    if specialCompetitionFixtures == "```\n```": return "There are no fixtures available for the given competition."
    return specialCompetitionFixtures

# function to return the details of the match that is in play for a given team
def get_team_live(teamCode):
    # getting the live match json
    url = "/v2/teams/{}/matches?status=LIVE".format(teamCode)
    response = get_json(url)
    if "errorCode" in response: return "Invalid team code."
    if response["count"] == 0: return "This team is not playing a match right now."

    # creating the live score message
    liveScore = "```\n"
    for liveMatch in response["matches"]:
        competitionName = liveMatch["competition"]["name"]
        if competitionName == "Primera Division": competitionName = "La Liga" 
        if liveMatch["status"] == "PAUSED": liveScore += "Half-Time"
        elif liveMatch["score"]["halfTime"]["homeTeam"] == None: liveScore += "First Half"
        else: liveScore += "Second Half"

        # getting the game minute
        utcString = liveMatch["utcDate"][2:10] + " " + liveMatch["utcDate"][11:16] # getting match time as string in utc
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        gameMinute = ""
        if liveScore == "First Half": 
            gameMinute = str(datetime.now() - ist)[2:4]
            if int(gameMinute) > 45: gameMinute = "45+" + str(int(gameMinute)-45)
            gameMinute += "'"
            gameMinute = gameMinute.lstrip("0")
        elif liveScore == "Second Half":
            gameMinute = str(datetime.now() - ist - timedelta(minutes=15))
            if gameMinute[0] == "0": gameMinute = int(gameMinute[2:4])
            else: gameMinute = 60 + int(gameMinute[2:4])
            if gameMinute > 90: gameMinute = "90+" + str(gameMinute-90)
            gameMinute = str(gameMinute) + "'"

        liveScore += " | " + competitionName + "\n"
        liveScore += liveMatch["homeTeam"]["name"] + " vs. " + liveMatch["awayTeam"]["name"] + "\n"
        liveScore += str(liveMatch["score"]["fullTime"]["homeTeam"]) + ":" + str(liveMatch["score"]["fullTime"]["awayTeam"])
        if "Half-Time" not in liveScore: liveScore += " | " + gameMinute
    liveScore += "\n```"

    return liveScore

# function to return all the matches that are in play in a given competition
def get_competition_live(competitionCode):
    # getting the live match json
    competitions = {"wc":2000, "cl":2001, "bl":2002, "ll":2014, "fl":2015, "sa":2019, "pl":2021}
    url = "/v2/competitions/{}/matches?status=LIVE".format(competitions[competitionCode])
    response = get_json(url)
    if response["count"] == 0: return "There are no matches in play right now."

    # creating the live score message
    liveScores = "```\n"
    for liveMatch in response["matches"]:
        if liveMatch["status"] == "PAUSED": liveMatchScore = "Half-Time\n"
        elif liveMatch["score"]["halfTime"]["homeTeam"] == None: liveMatchScore = "First Half"
        else: liveMatchScore = "Second Half"
        
        # getting the game minute
        utcString = liveMatch["utcDate"][2:10] + " " + liveMatch["utcDate"][11:16] # getting match time as string in utc
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        gameMinute = ""
        if liveMatchScore == "First Half": 
            gameMinute = str(datetime.now() - ist)[2:4]
            if int(gameMinute) > 45: gameMinute = "45+" + str(int(gameMinute)-45)
            gameMinute += "'"
            gameMinute = gameMinute.lstrip("0")
        elif liveMatchScore == "Second Half":
            gameMinute = str(datetime.now() - ist - timedelta(minutes=15))
            if gameMinute[0] == "0": gameMinute = int(gameMinute[2:4])
            else: gameMinute = 60 + int(gameMinute[2:4])
            if gameMinute > 90: gameMinute = "90+" + str(gameMinute-90)
            gameMinute = str(gameMinute) + "'"
        if "Half-Time" not in liveMatchScore: liveMatchScore += " | " + gameMinute + "\n"

        # adding the match's information to the live score message
        liveMatchScore += liveMatch["homeTeam"]["name"] + " vs. " + liveMatch["awayTeam"]["name"] + "\n"
        liveMatchScore += str(liveMatch["score"]["fullTime"]["homeTeam"]) + ":" + str(liveMatch["score"]["fullTime"]["awayTeam"]) + "\n\n"
        liveScores += liveMatchScore
    liveScores += "```"

    return liveScores

# function to return the past 0 ≤ {limit} ≤ 20 match results of the given team
def get_team_results(teamCode, limit):
    # preliminary adjustment of the limit
    if limit == "": limit = 3
    if int(limit) <= 0: return "What the hell was the point of that?"
    url = "/v2/teams/{}/matches?status=FINISHED".format(teamCode)
    response = get_json(url)
    if "errorCode" in response: return "Invalid team code."
    if response["count"] == 0: return "No results data available."

    # final adjustment of the limit and getting the team results json
    if int(limit) > response["count"]: limit = response["count"]
    if int(limit) > 20: limit = 20
    url = "/v2/teams/{}/matches?status=FINISHED&limit={}".format(teamCode, limit)
    response = get_json(url)

    # creating the team's results list
    resForm = "`"
    teamResults = "```\n"
    for match in response["matches"][::-1]:
        # converting match time from utc to ist (+5.5h)
        utcString = match["utcDate"][2:10] + " " + match["utcDate"][11:16] # getting match time as string in utc
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        # converting the date to the desired format
        istDate = ist.strftime('%a %d %h')

        # getting the match winner's name
        res = match["score"]["winner"]
        if res == "DRAW": 
            resForm += "D "
            res = "Draw | "
        elif res == "HOME_TEAM" and match["homeTeam"]["id"] == int(teamCode): 
            resForm += "W "
            res = "Win | "
        elif res == "AWAY_TEAM" and match["awayTeam"]["id"] == int(teamCode): 
            resForm += "W "
            res = "Win | "
        else: 
            resForm += "L "
            res = "Loss | "

        # getting and adding the match information to the list of team results
        competitionName = match["competition"]["name"]
        if competitionName == "Primera Division": competitionName = "La Liga" 
        matchInfo = res + str(match["score"]["fullTime"]["homeTeam"]) + ":" + str(match["score"]["fullTime"]["awayTeam"]) + "\n"
        matchInfo += istDate + " | " + competitionName + "\n"
        matchInfo += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n\n"
        teamResults += matchInfo
    teamResults += "```"
    resForm += "`\n"

    return resForm + teamResults

# function to return the results of a given competition for the past 0 ≤ {limit} ≤ 10 days
def get_competition_results(competitionCode, limit):
    # adjusting the limit
    if limit == "": limit = 3
    if int(limit) > 10: limit = 10
    if int(limit) <= 0: return "What the hell was the point of that?"

    # getting season start date
    url = "/v2/competitions/{}/matches?status=SCHEDULED".format(competitionCode)
    response = get_json(url)
    startDate = datetime.strptime(response["matches"][0]["season"]["startDate"], "%Y-%m-%d")

    # adjusting and getting the dates
    dateTo = str(datetime.today() - timedelta(hours=5.5))[:10]
    dateFrom = datetime.today() - timedelta(days=int(limit)+1, hours=5.5)
    if dateFrom.date() < startDate.date(): dateFrom = startDate
    dateFrom = str(dateFrom)[:10]

    # getting the results json
    url = "/v2/competitions/{}/matches?status=FINISHED&dateFrom={}&dateTo={}".format(competitionCode, dateFrom, dateTo)
    response = get_json(url)

    # creating the results list
    competitionResults = "```\n"
    for match in response["matches"][::-1]:
        # getting the match winner's name
        matchWinner = match["score"]["winner"]
        if matchWinner == "DRAW": matchWinner = "Draw"
        elif matchWinner == "HOME_TEAM": matchWinner = match["homeTeam"]["name"]
        else: matchWinner = match["awayTeam"]["name"]
        
        # converting match time from utc to ist (+5.5h)
        utcString = match["utcDate"][2:10] + " " + match["utcDate"][11:16] # getting match time as string in utc
        utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        # converting the date and time to the desired format
        istDate = ist.strftime('%a %d %h')
        istTime = ist.strftime("%I:%M %p")

        # getting and adding the current match's information to the results list
        matchInfo = istDate + " | " + istTime + "\n"
        matchInfo += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n"
        matchInfo += str(match["score"]["fullTime"]["homeTeam"]) + ":" + str(match["score"]["fullTime"]["awayTeam"]) + " | " + matchWinner + "\n\n"
        competitionResults += matchInfo
    competitionResults += "```"

    if competitionResults == "```\n```": return "No results available in the given time interval."
    return competitionResults

# function to return the past 0 ≤ {limit} ≤ 20 match results of the given special competition
def get_special_competition_results(specialCompetitionCode, limit):
    # adjusting the limit
    if limit == "": limit = 3
    if int(limit) > 20: limit = 20
    if int(limit) == 0 or int(limit) < 0: return "What the hell was the point of that?"

    # getting the results json
    url = "/v2/competitions/{}/matches?status=FINISHED".format(specialCompetitionCode)
    response = get_json(url)

    # creating the results list
    specialCompetitionResults = "```\n"
    for matchNumber in range(int(limit)):
        match = response["matches"][::-1][matchNumber]
        # getting the match winner's name
        matchWinner = match["score"]["winner"]
        if matchWinner == "DRAW": matchWinner = "Draw"
        elif matchWinner == "HOME_TEAM": matchWinner = match["homeTeam"]["name"]
        else: matchWinner = match["awayTeam"]["name"]

        # converting match time from utc to ist (+5.5h)
        utc =  match["utcDate"][2:10] + " " + match["utcDate"][11:16]
        utc = datetime.strptime(utc, '%y-%m-%d %H:%M')
        ist = utc + timedelta(hours=5.5)
        # converting the date and time to the desired format
        istDate = ist.strftime('%a %d %h')
        if specialCompetitionCode == 2000: istDate = ist.strftime('%a %d %h %Y')
        istTime = ist.strftime("%I:%M %p")

        # getting and adding the current match's information to the list of match results
        matchStage = match["stage"].split("_")
        matchInfo = ""
        for word in matchStage:
            matchInfo += word + " "
        if match["group"] != None and (matchInfo.strip(" ").lower() == "quarter finals" or matchInfo.strip(" ").lower() == "semi finals" or matchInfo.strip(" ").lower() == match["group"].lower()):
            matchInfo = match["group"] + "\n"
        else:
            if match["group"] != None: matchInfo += "| " + match["group"] + "\n"
            else: matchInfo += "\n"
        matchInfo += istDate + " | " + istTime + "\n"
        matchInfo += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n"
        matchInfo += str(match["score"]["fullTime"]["homeTeam"]) + ":" + str(match["score"]["fullTime"]["awayTeam"]) + " | " + matchWinner + "\n\n"
        specialCompetitionResults += matchInfo
    specialCompetitionResults += "```"

    return specialCompetitionResults

# function to return the list of top scorers for a given competition
def get_scorers(competitionCode):
    # getting the list of teams in the competition
    url ="/v2/competitions/{}/teams".format(competitionCode)
    teams = get_json(url)["teams"]

    # getting the length of the longest team abbreviation (to format the final output)
    longestTLA = 0
    for team in teams:
        if team["tla"] == None: team["tla"] = "???"
        longestTLA = max(longestTLA, len(team["tla"]))

    # getting the top scorers json
    url = "/v2/competitions/{}/scorers?limit=10".format(competitionCode)
    response = get_json(url)

    # getting the length of the longest name (to format the final output)
    longestName = 0
    for scorer in response["scorers"]:
        longestName = max(longestName, len(scorer["player"]["name"]))

    # creating the list of top scorers
    topScorersHeader = "`\n# |TEAM | PLAYER NAME" + " "*(longestName - 11) + " | GO`\n"
    topScorers = "\n```"
    for playerNumber in range(response["count"]):
        playerTeam = response["scorers"][playerNumber]["team"]["id"]
        for team in teams:
            if team["id"] == playerTeam:
                teamAbr = team["tla"]
                break
        playerInfo = str(playerNumber+1) + " "*(2-len(str(playerNumber+1))) + "| " + teamAbr + " "*(longestTLA-len(teamAbr)) + " | "
        playerInfo += response["scorers"][playerNumber]["player"]["name"] + " "*(longestName-len(response["scorers"][playerNumber]["player"]["name"]))
        playerInfo += " | " + str(response["scorers"][playerNumber]["numberOfGoals"]) + "\n"
        topScorers += playerInfo
    topScorers += "```"

    return topScorersHeader+topScorers

# function to return whether there are any matches today or tomorrow for the selected teams
def get_match_alert():
    if not teamMatchAlertList: return ""

    # creating the match alert message
    matchesAlertMessage = "```\n"
    for teamCode in teamMatchAlertList:
        # getting the particular competitions fixtures for today and tomorrow
        dateFrom = str(datetime.today().strftime("%Y-%m-%d"))
        dateTo = str((datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"))
        url = "/v2/teams/{}/matches?status=SCHEDULED&dateFrom={}&dateTo={}".format(teamCode, dateFrom, dateTo)
        response = get_json(url)
        if response["count"] == 0: continue

        for match in response["matches"]:
            competitionName = match["competition"]["name"]
            if competitionName == "Primera Division": competitionName = "La Liga" 

            # converting match time from utc to ist (+5.5h)
            utcString = match["utcDate"][2:10] + " " + match["utcDate"][11:16] # getting match time in utc
            utc = datetime.strptime(utcString, '%y-%m-%d %H:%M')
            ist = utc + timedelta(hours=5.5)
            # getting the time in the desired format
            istTime = ist.strftime("%I:%M %p")
            
            # adding the match to the match alert message
            if ist.date() == datetime.today().date(): matchAlertMessage = "Today | " + competitionName + "\n"
            elif ist.date() == (datetime.today() + timedelta(days=1)).date(): matchAlertMessage = "Tomorrow | " + competitionName + "\n"
            else: break
            matchAlertMessage += match["homeTeam"]["name"] + " vs. " + match["awayTeam"]["name"] + "\n"
            matchAlertMessage += istTime + "\n\n"

            matchesAlertMessage += matchAlertMessage
    matchesAlertMessage += "```"
    
    if matchesAlertMessage == "```\n```": matchesAlertMessage = "There are no upcoming matches for your selected teams."
    return matchesAlertMessage

# COMMANDS
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)
bot = commands.Bot(command_prefix=".", help_command=help_command)

# command to get codes
@bot.command(name="codes",
brief="Shows team or competition codes.",
help="{No argument}: The codes of all available competitions.\n\n[competitionCode](Optional): The code of the competition for which you want to get the team codes.\n\n[season](Optional): The season from which you want to get the competition's team codes.")
async def send_competition_codes(ctx, competitionCode="", season=""):
    msg="Invalid command."
    competitions = ["pl", "ll", "sa", "bl", "fl", "cl", "wc"]
    if competitionCode == "": msg = "Competition Codes:\n```\nPremier League: pl\nLa Liga: ll\nSerie-A: sa\nBundesliga: bl\nLigue 1: fl\nUEFA Champions League: cl\nFIFA World Cup: wc\n```"
    elif competitionCode not in competitions: msg = "Invalid competition."
    else: msg = get_competition_team_codes(competitionCode.upper(), season)
    await ctx.channel.send(msg)

# command to get competition tables
@bot.command(name="table",
brief="Shows a competition's standings.",
help="[standingsType]: 's' or 'l'; specifies whether you want the short or long form competition table.\n\n[competitionCode]: The code of the competition for which you want to get the table.")
async def send_competition_table(ctx, standingsType="", competitionCode=""):
    msg = "Invalid command."
    competitions = ["pl", "ll", "sa", "bl", "fl"]
    if standingsType == "s" and competitionCode in competitions: msg = get_short_table(competitionCode.upper())
    elif standingsType == "l" and competitionCode in competitions: msg = get_long_table(competitionCode.upper())
    await ctx.channel.send(msg)

# command to get fixtures
@bot.command(name="fix",
brief="Shows team or competition fixtures.",
help="[code]: The code of the team or competition for which you want to get the fixtures.\nIn case of team code, it gives you the fixtures of that team for the next 2 weeks.\nIn case of competition code, it gives you the remaining fixtures of that competition for the current matchday.\n\n[limit](Optional): Lists the next 0 ≤ [limit] ≤ 20 fixtures of the selected Special Competition (CL or WC).")
async def send_fixtures(ctx, code="", limit=3):
    msg = "Invalid command."
    specialCompetitions = ["cl", "wc"]
    competitions = ["pl", "ll", "sa", "bl", "fl"]
    if code.isdigit(): msg = get_team_fixtures(int(code))
    elif code in specialCompetitions: msg = get_special_competition_fixtures(code.upper(), limit)
    elif code in competitions: msg = get_competition_fixtures(code.upper())
    await ctx.channel.send(msg)

# command to get live match information
@bot.command(name="live",
brief="Shows matches that are in play.",
help="[code]: The code of the team or competition for which you want the live fixtures.")
async def send_live_fixtures(ctx, code=""):
    msg = "Invalid command."
    competitions = ["pl", "ll", "sa", "bl", "fl", "cl", "wc"]
    if code in competitions: msg = get_competition_live(code)
    elif code.isdigit(): msg = get_team_live(int(code))
    await ctx.channel.send(msg)

# command to get results
@bot.command(name="res",
brief="Shows team or competition results.",
help="[code]: The code of the team or competition for which you want the results.\n\n[limit](Optional): In case of a team code as the [code], it lists the past 0 ≤ [limit] ≤ 20 match results of the team. [limit] = 3 by default.\nIn case of a competition code as the [code], it lists the results of the competition for the past 0 ≤ [limit] ≤ 10 days. [limit] = 3 by default.\nIn case of a special competition code (CL or WC) as the [code], it lists the past 0 ≤ [limit] ≤ 20 match results of the competition. [limit] = 3 by default.")
async def send_results(ctx, code="", limit=""):
    msg = "Invalid command."
    specialCompetitions = {"wc":2000, "cl":2001}
    competitions = {"bl":2002, "ll":2014, "fl":2015, "sa":2019, "pl":2021}
    if code.isdigit(): msg = get_team_results(int(code), limit)
    elif code in competitions: msg = get_competition_results(competitions[code], limit)
    elif code in specialCompetitions: msg = get_special_competition_results(specialCompetitions[code], limit)
    await ctx.channel.send(msg)

# command to get top scorers
@bot.command(name="scorers",
brief="Shows the top scorers of a competition.",
help="[competitionCode]: The code of the competition for which you want the list of top 10 goal scorers.")
async def send_top_scorers(ctx, competitionCode=""):
    msg = "Invalid command."
    competitions = {"wc":2000, "cl":2001, "bl":2002, "ll":2014, "fl":2015, "sa":2019, "pl":2021}
    if competitionCode in competitions: msg = get_scorers(competitions[competitionCode])
    await ctx.channel.send(msg)

@bot.command(name="creatorsNote",
brief="A note from the creator.")
async def send_top_scorers(ctx):
    msg = "I hope you enjoy using this bot!"
    await ctx.channel.send(msg)

# calling the get_match_alert() function once every 24 hours. # If you do not want match alerts, delete lines [636,644] and 651
@tasks.loop(hours=24)
async def sendMatchAlert():
    if MATCH_ALERT_CHANNEL != "YOUR_CHANNEL_ID":
        channel = bot.get_channel(MATCH_ALERT_CHANNEL)
        matchAlert = get_match_alert()
        if matchAlert != "": await channel.send("@everyone\n" + matchAlert)

@sendMatchAlert.before_loop
async def before():
    await bot.wait_until_ready()

# printing to the cmd when the bot in online
@bot.event
async def on_ready():
    print("{0.user} is awake.".format(bot))

sendMatchAlert.start()
bot.run(TOKEN)
