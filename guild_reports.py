#Imports
import requests
from pprint import pprint
from datetime import date, datetime
import time
import mysql.connector
import pandas as pd
import numpy
import sys


start_script = time.time()

#Authenticating client.
client_id = "9d4c1a49-91d2-4b7b-8445-824e4f6bac1b"
client_secret = "0Y527wHR8EGP7T6Oa1TZdMvuxZFkVSrqYG1DLvIF"
data = {
    'grant_type': 'client_credentials',
}
response = requests.post(url = 'https://www.warcraftlogs.com/oauth/token', data=data, auth=(f'{client_id}', f'{client_secret}'))
response.raise_for_status()
access_token = (response.json())['access_token']


#Checks rate limit from API.
url =  'https://www.warcraftlogs.com/api/v2/client'

query = """{
            rateLimitData{
                limitPerHour,
                pointsSpentThisHour,
                pointsResetIn}
                }"""

headers = {
        'Authorization' : f'Bearer {access_token}'
    }

try:
    response1 = requests.post(url, json= {'query' : query}, headers = headers)
    response1.raise_for_status()
    data = response1.json()
    print(data)

except requests.HTTPError as e:
    print(f"Error code: {e} . Please try again later. The cooldown period for this script is an hour long from the moment it is first run.")
    sys.exit()


#Collecting information from user about the guild and the raid zone to collect information from.
while True:
    try:
        print("What is the ID of the raid zone you would like to collect information from? Enter \"2016\" for AQ40 or \"2013\" for BWL.")
        zoneID = int(input())
        if type(zoneID) == int:
            print("Thank you!")

        print("What is the name of your guild?")
        guildName = input()

        print("What is the ID of your guild?")
        guildID = int(input())
        if type(guildID) == int:
            print("Thank you!")

        print("Attempting to request data.")
        break

    except ValueError:
        print("Please enter an integer value for the raid zone and guild ID. Please enter a string value for the name of the guild.")
        print('-------------------------------------------')
        continue



#Runs a query to get general player/ raid data such as: buffs, kill times, deaths, consumables, etc.
def runQuery1(guildID, guildName, zoneID) -> dict:
    generalQuery = """
            query generalInfo($guildID : Int!, $guildName : String!, $zoneID : Int!){
                reportData{
                    reports(guildID : $guildID, guildName : $guildName, zoneID : $zoneID){
                        data{
                            playerDetails(includeCombatantInfo: true, endTime : 9999999999999),
                            startTime,
                            endTime,
                            fights(killType : Encounters){
                                startTime,
                                endTime,
                                name,
                                kill},
                            table(dataType : Deaths, endTime : 9999999999999)}
                                }
                            }
                        }"""

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    variables = {
        'guildID': guildID,
        'guildName': guildName,
        'zoneID' : zoneID}

    response = requests.post(url = url, json = {"query" : generalQuery, 'variables' : variables}, headers = headers)
    response.raise_for_status()
    player_data = response.json()

    return player_data


#Runs a different query to specifically get ranking data based on "damage per second" (dps) or "healing per second" (hps).
def runQuery2(metric, guildID, guildName, zoneID) -> dict:
    rankingsQuery = """
            query rankingsInfo($guildID : Int!, $guildName : String!, $metric : ReportRankingMetricType!, $zoneID : Int!){
                reportData{
                    reports(guildID : $guildID, guildName : $guildName, zoneID : $zoneID){
                        data{
                            rankings(compare: Rankings, playerMetric: $metric, timeframe : Historical)}  
                                }
                            }
                        }"""

    headers = {
        'Authorization' : f'Bearer {access_token}'
    }

    variables = {
        'guildID' : guildID,
        'guildName' : guildName,
        'metric' : metric,
        'zoneID' : zoneID}

    response = requests.post(url = url, json = {"query" : rankingsQuery, 'variables' : variables}, headers = headers)
    response.raise_for_status()
    ranking_data = response.json()

    return ranking_data


#Returns the number of reports a guild has uploaded to their profile.
def reportNum() -> int:
    report_num = len(player_data['data']['reportData']['reports']['data'])
    return report_num


#Returns the total time spent raiding from a report.
def raidTime(num) -> dict:
    raidEnd = round(int(player_data['data']['reportData']['reports']['data'][num]['endTime'])/1000)
    raidStart = round(int(player_data['data']['reportData']['reports']['data'][num]['startTime'])/1000)
    raidLength = raidEnd - raidStart
    raidLengthConverted = time.strftime('%H:%M:%S', time.gmtime(raidLength))
    timeDict = ({'date' : date,
                'raidLength' : raidLengthConverted})
    return timeDict


# Returns the date of a report.
def raidDate(num):
    start = int(player_data['data']['reportData']['reports']['data'][num]['startTime'])
    raidstart = start / 1000

    return datetime.fromtimestamp(raidstart).date()


#Returns the global buffs all players had active during a raid, according to a report.
def buffs(num, role_data, date) -> list:
    buff_data = []
    role_count = len(role_data)
    try:
        for num in range(role_count):
            name = role_data[num]['name']
            not_unique_buffs = ({
                'date' : date,
                'player': name
            })

            unique_buffs = ({
                'date' : date,
                'player': name
            })

            try:
                allWorldBuffsList = [rf'Spirit of Zandalar','Rallying Cry of the Dragonslayer', 'Might of Stormwind', 'Songflower Serenade', 'Fengus\' Ferocity', 'Slip\'kik\'s Savvy', 'Mol\'dar\'s Moxie', 'Sayge\'s Dark Fortune of Damage', 'Sayge\'s Dark Fortune of Intelligence', 'Sayge\'s Dark Fortune of Resistance', 'Cleansed Firewater', 'Songflower Lullaby', 'Blessing of Neptulon', 'Dark Fortune of Damage', 'Dreams of Zandalar', 'Might of Blackrock', 'Horn of the Dawn']
                for buff in role_data[num]['combatantInfo']['artifact']:
                    if buff['name'] in allWorldBuffsList:
                        not_unique_buffs[buff['name']] = 1
            except TypeError:
                continue

            if 'Rallying Cry of the Dragonslayer' or 'Blessing of Neptulon' in not_unique_buffs:
                unique_buffs['Rallying Cry of the Dragonslayer'] = 1
            if 'Spirit of Zandalar' or 'Dreams of Zandalar' in not_unique_buffs:
                unique_buffs['Spirit of Zandalar'] = 1
            if 'Might of Stormwind' or 'Might of Blackrock' in not_unique_buffs:
                unique_buffs['Might of Stormwind'] = 1
            if 'Songflower Serenade' or 'Songflower Lullaby' in not_unique_buffs:
                unique_buffs['Songflower Serenade'] = 1
            if 'Fengus\' Ferocity' or 'Blessing of Neptulon' in not_unique_buffs:
                unique_buffs['Fengus\' Ferocity'] = 1
            if 'Slip\'kik\'s Savvy' or 'Blessing of Neptulon' in not_unique_buffs:
                unique_buffs['Slip\'kik\'s Savvy'] = 1
            if 'Mol\'dar\'s Moxie' or 'Blessing of Neptulon' in not_unique_buffs:
                unique_buffs['Mol\'dar\'s Moxie'] = 1
            if 'Sayge\'s Dark Fortune of Damage' or 'Sayge\'s Dark Fortune of Intelligence' or 'Sayge\'s Dark Fortune of Resistance' or 'Dark Fortune of Damage' in not_unique_buffs:
                unique_buffs['Darkmoon Faire'] = 1

            if len(unique_buffs) > 2:
                buff_data.append(unique_buffs)
            else:
                continue

    except IndexError:
        print(rf'There aren\'t this many players')

    return buff_data


#Returns the names of all players and their corresponding IDs from a single report.
def getPlayerIDs(role_data, date) -> list:
    roleIDsNames = []
    for player in role_data:
        id = player['id']
        name = player['name']
        players = ({
            'id': int(id),
            'name' : name,
            'date' : date
        })
        roleIDsNames.append(players)

    return roleIDsNames


#Returns the consumables (items that, when used, enhance a player's combat abilities) of ell players within a raid's report.
def getConsumablesData(roleIDsNames, number, date, guildName, guildID, zoneID) -> list:
    cons_data = []
    try:
        for source in roleIDsNames:
            num = source['id']
            consQuery = """
                    query consInfo($guildID : Int!, $guildName : String!, $source : Int!, $zoneID : Int!){
                        reportData{
                            reports(guildID : $guildID, guildName : $guildName, zoneID : $zoneID){
                                data{
                                    table(dataType : Buffs, endTime : 9999999999999, sourceID : $source)}
                                    }
                                }
                            }"""


            variables = {
                'guildName' : guildName,
                'guildID' : guildID,
                'source' : num,
                'zoneID' : zoneID}

            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            response = requests.post(url = url, json = {"query" : consQuery, 'variables' : variables}, headers = headers)
            response.raise_for_status()
            spec_data = response.json()

            player_cons = {
                'name': source['name'],
                'id' : source['id'],
                'date' : date
            }


            all_roles_data = spec_data['data']['reportData']['reports']['data'][number]['table']['data']['auras']

            listOfConsumables = ['Fire Protection', 'Shadow Protection', 'Nature Protection', 'Frost Protection', 'Winterfall Firewater', 'Elixir of the Mongoose', 'Elixir of the Giants', 'Arcane Elixir', 'Frost Power', 'Greater Firepower', 'Shadow Power', 'Mana Regeneration', 'Increased Intellect', 'Greater Armor', 'Health II', 'Free Action', 'Invulnerability', 'Gordok Green Grog', 'Rumsey Rum Black Label', 'Cleansed Firewater']
            try:
                for consume in all_roles_data:
                    if consume['name'] in listOfConsumables:
                        player_cons[consume['name']] = consume['totalUses']
            except TypeError:
                print('There was an error here, please resolve this.')
                continue

            if len(player_cons) > 3:   #removes the dicts that contain players that slipped into the report but weren't present in the raid
                cons_data.append(player_cons)
            else:
                continue
            for character in cons_data:
                for item in listOfConsumables:
                    character.setdefault(item, 0)
    except requests.HTTPError as e:
        print(f"Error code: {e} . Please try again later. The cooldown period for this script is an hour long from the moment it is first run.")
        sys.exit()

    return cons_data


#Returns the time taken to kill each boss from a raid's report, as well as the overall time taken to clear the raid.
def getKillTimes(num, date, zoneID) -> list:
    boss_times_data = []
    boss_count = []
    bwl_bosses = ['Razorgore the Untamed', 'Vaelastrasz the Corrupt', 'Broodlord Lashlayer', 'Firemaw', 'Flamegor', 'Chromaggus', 'Nefarian']
    aq40_bosses = ['The Prophet Skeram', 'Silithid Royalty', 'Battleguard Sartura', 'Fankriss the Unyielding', 'Viscidus', 'Princess Huhuran', 'Twin Emperors', 'Ouro', 'C\'Thun']

    if zoneID == 2016:  #This zoneID corresponds to the raid "AQ40"
        bosses = aq40_bosses
    elif zoneID == 2013: #This zoneID corresponds to the raid "BWL"
        bosses = bwl_bosses

    kill_times_check = player_data['data']['reportData']['reports']['data'][num]['fights']

    for boss in kill_times_check:
        if boss['kill'] == True and boss['name'] in bosses:
            boss_count.append(boss)
    bosses_killed = len(boss_count)


    for encounterID in range(bosses_killed):
        startTime = boss_count[encounterID]['startTime']
        endTime = boss_count[encounterID]['endTime']
        name = boss_count[encounterID]['name']
        fight_length = round(int(endTime)/1000 - int(startTime)/1000)
        fights = ({
            'boss': name,
            'fight time': fight_length,
            'date': date
        })
        boss_times_data.append(fights)

    return boss_times_data


#Returns the number of deaths by each player across the entire raid, according to a report.
def getDeaths(num, date) -> list:
    check = player_data['data']['reportData']['reports']['data'][num]['table']['data']['entries']
    all_names = []
    deaths_list = []

    for x in check:
        name = x['name']
        all_names.append(name)
    unique_names = list(set(all_names))

    for name in unique_names:
        deaths = all_names.count(name)
        deaths_dict = ({
            'player' : name,
            'deaths' : deaths,
            'Date' : date
        })
        deaths_list.append(deaths_dict)

    return deaths_list


#Returns the parses achieved by each player, for each boss as well as the overall raid, from a raid report.
def getParses(num, role, roleRankingData, date) -> dict:
    healersList = []
    dpsList = []

    if role == 'dps':
        dpsData = roleRankingData
        dpsRanking = dpsData['data']['reportData']['reports']['data'][num]['rankings']['data']
        bossesCount = len(dpsRanking)
        for bossNum in range(bossesCount):  #healers
            bossName = dpsRanking[bossNum]['encounter']['name']
            numOfDps = len(dpsRanking[bossNum]['roles']['dps']['characters'])
            numOfTanks = len(dpsRanking[bossNum]['roles']['tanks']['characters'])
            for dpsNum in range(numOfDps):
                rankCheck = dpsRanking[bossNum]['roles']['dps']['characters'][dpsNum]['rankPercent']
                player = dpsRanking[bossNum]['roles']['dps']['characters'][dpsNum]['name']
                dps_dict = {
                    'player name': player,
                    'date' : date,
                    'rank': rankCheck,
                    'boss name': bossName
                }
                dpsList.append(dps_dict)
            for tanksNum in range(numOfTanks):
                rankCheck = dpsRanking[bossNum]['roles']['tanks']['characters'][tanksNum]['rankPercent']
                player = dpsRanking[bossNum]['roles']['tanks']['characters'][tanksNum]['name']
                tanks_dict = {
                    'player name': player,
                    'date': date,
                    'rank': rankCheck,
                    'boss name': bossName
                }
                dpsList.append(tanks_dict)

    elif role == 'healers':
        healersData = roleRankingData
        healersRanking = healersData['data']['reportData']['reports']['data'][num]['rankings']['data']
        bossesCount = len(healersRanking)
        for bossNum in range(bossesCount):  #healers
            bossName = healersRanking[bossNum]['encounter']['name']
            numOfHealers = len(healersRanking[bossNum]['roles']['healers']['characters'])
            for healerNum in range(numOfHealers):
                rankCheck = healersRanking[bossNum]['roles']['healers']['characters'][healerNum]['rankPercent']
                player = healersRanking[bossNum]['roles']['healers']['characters'][healerNum]['name']
                healers_dict = {
                    'player name' : player,
                    'date': date,
                    'rank' : rankCheck,
                    'boss name' : bossName
                }
                healersList.append(healers_dict)
    parseData = {
        'healersRankings' : healersList,
        'dpsRankings' : dpsList
    }

    return parseData


def report_checker(num, zoneID):
    boss_count = []
    bwl_bosses = ['Razorgore the Untamed', 'Vaelastrasz the Corrupt', 'Broodlord Lashlayer', 'Firemaw', 'Flamegor', 'Chromaggus', 'Nefarian']
    aq40_bosses = ['The Prophet Skeram', 'Silithid Royalty', 'Battleguard Sartura', 'Fankriss the Unyielding', 'Viscidus', 'Princess Huhuran', 'Twin Emperors', 'Ouro', 'C\'Thun']

    if zoneID == 2016:  #This zoneID corresponds to the raid "AQ40"
        bosses = aq40_bosses
    elif zoneID == 2013: #This zoneID corresponds to the raid "BWL"
        bosses = bwl_bosses

    kill_times_check = player_data['data']['reportData']['reports']['data'][num]['fights']

    for boss in kill_times_check:
        if boss['kill'] == True:
            boss_count.append(boss)
    bosses_killed = len(boss_count)

    if bosses_killed < len(bosses):
        print(f'Report {num} is invalid due to incompletion of raid. Please select a different report.')
        sys.exit()
    elif bosses_killed > len(bosses):
        print(f'Report {num} is invalid due to inclusion of multiple raid zones. Please either split the report to only include the single raid zone or select a different report.')
        sys.exit()
    else:
        print(f'Report {num} is valid.')
    return None



#Function calls that run the GraphQL queries that provide the API data.

try:
    player_data = runQuery1(guildID, guildName, zoneID)

    player_dps_data = runQuery2('dps', guildID, guildName, zoneID)
    player_hps_data = runQuery2('hps', guildID, guildName, zoneID)

except requests.HTTPError as e:
    print(f"Error code: {e} . If timed out, please try again later. If too many requests have been made, the cooldown period for this script is an hour long from the moment it is first run.")
    sys.exit()




#Returns the number of uploaded reports from a guild - determines the number of loops to be performed.
try:
    report_num = reportNum()

    options = []
    for num in range(report_num):
        formattedDate = raidDate(num).strftime('%d, %m, %Y')
        option = {num : formattedDate}
        options.append(option)

    if options == []:
        print("Guild either does not exist or it does not have any available reports to access.")
        sys.exit()

except TypeError:
    print('Cannot gather reports. Please check your inputs correspond with a guild and a raid.')
    sys.exit()

while True:
    try:
        choices_from_user = []
        print(f"Please select the number corresponding to the raid date of interest. You will have the option to select up to 3 numbers from the following: {options}")
        print("To start with, how many raids would you like data from?")
        num = int(input())
        if num > 3:
            print("3 raids is the maximum! Please select the number 3 or less.")
            continue
        for x in range(num):
            new_x = int(x) + 1
            print(f"Raid number {new_x} ?")
            choices_from_user.append(int(input()))

        choices_from_user = list(set(choices_from_user))

        for choice in choices_from_user:
            if choice not in range(report_num):
                print("Selections are not applicable. Please ensure that your choices are from the numbers provided.")
                continue
            else:
                print(f"Your options are as follows: {choices_from_user} . Data organisation will now begin.")
                break
        for report_num in choices_from_user:
            report_checker(report_num, zoneID)
        break
    except ValueError:
        print("Selections are not applicable. Please ensure that your choices are from the numbers provided.")



#The following variables are empty lists to append each report's data to.
entire_role_data = []

entire_deaths_data = []

entire_kill_times_data = []

entire_raid_times_data = []

entire_buffs_data = []

entire_cons_data = []

entire_parses_data = []

#Calls the various, defined functions to obtain the data of interest from each report of a guild.
try:
    for num in choices_from_user:


        dps_data = player_data['data']['reportData']['reports']['data'][num]['playerDetails']['data']['playerDetails']['dps']
        healers_data = player_data['data']['reportData']['reports']['data'][num]['playerDetails']['data']['playerDetails']['healers']
        tanks_data = player_data['data']['reportData']['reports']['data'][num]['playerDetails']['data']['playerDetails']['tanks']

        date = raidDate(num)
        raid_times = raidTime(num)
        entire_raid_times_data.append(raid_times)

        buffs_dps = buffs(num, dps_data, date)
        buffs_healers = buffs(num, healers_data, date)
        buffs_tanks = buffs(num, tanks_data, date)

        all_buffs = buffs_healers + buffs_tanks + buffs_dps
        entire_buffs_data += all_buffs

        healersIDsNames = getPlayerIDs(healers_data, date)

        healersCons = getConsumablesData(healersIDsNames, num, date, guildName, guildID, zoneID)

        tanksIDsNames = getPlayerIDs(tanks_data, date)

        tanksCons = getConsumablesData(tanksIDsNames, num, date, guildName, guildID, zoneID)

        dpsIDsNames = getPlayerIDs(dps_data, date)

        dpsCons = getConsumablesData(dpsIDsNames, num, date, guildName, guildID, zoneID)

        all_Cons = healersCons + tanksCons + dpsCons
        entire_cons_data += all_Cons

        single_kill_times = getKillTimes(num, date, zoneID)
        entire_kill_times_data += single_kill_times

        get_deaths = getDeaths(num, date)
        entire_deaths_data += get_deaths

        dps = getParses(num, 'dps', player_dps_data, date)
        healers = getParses(num, 'healers', player_hps_data, date)

        dpsParseList = dps['dpsRankings']
        healersParseList = healers['healersRankings']
        all_parses = dpsParseList + healersParseList
        entire_parses_data += all_parses

        print(rf'Report {num} done')
except IndexError:
    print(rf'This report doesn\'t exist')


#Initially assigns variables a value that reflects the raid zone information the user has requested, and then converts the gathered data into dataframes.
def creatingDataFrames(zoneID, entire_parses_data, entire_cons_data, entire_buffs_data, entire_deaths_data, entire_raid_times_data, entire_kill_times_data):

    bwlParsesDFOrder = [('player name', ''), ('date', ''), ('rank', 'Razorgore the Untamed'),
                        ('rank', 'Vaelastrasz the Corrupt'), ('rank', 'Broodlord Lashlayer'), ('rank', 'Firemaw'),
                        ('rank', 'Ebonroc / Flamegor'), ('rank', 'Chromaggus'), ('rank', 'Nefarian')]

    aqParsesDFOrder = [('player name', ''), ('date', ''), ('rank', 'The Prophet Skeram'), ('rank', 'Silithid Royalty'),
                       ('rank', 'Battleguard Sartura'), ('rank', 'Fankriss the Unyielding'), ('rank', 'Viscidus'),
                       ('rank', 'Princess Huhuran'), ('rank', 'Twin Emperors'), ('rank', 'Ouro'), ('rank', 'C\'thun')]

    bwlKillTimesDFOrder = ['Razorgore the Untamed', 'Vaelastrasz the Corrupt', 'Broodlord Lashlayer', 'Firemaw', 'Flamegor', 'Chromaggus', 'Nefarian']
    aqKillTimesDFOrder = ['The Prophet Skeram', 'Silithid Royalty', 'Battleguard Sartura', 'Fankriss the Unyielding', 'Viscidus', 'Princess Huhuran', 'Twin Emperors', 'Ouro', 'C\'Thun']

    if zoneID == 2016:
        parsesDFOrder = aqParsesDFOrder
        killTimesDFOrder = aqKillTimesDFOrder
        first_boss = 'The Prophet Skeram'

    elif zoneID == 2013:
        parsesDFOrder = bwlParsesDFOrder
        killTimesDFOrder = bwlKillTimesDFOrder
        first_boss = 'Razorgore'

    entireParsesDataDF = pd.DataFrame(entire_parses_data)
    entireParsesDFPivot = entireParsesDataDF.pivot_table(index = ['player name', "date"], values = ['rank'], columns = ["boss name"], aggfunc='first')
    entireParsesDFIndex = entireParsesDFPivot.reset_index()
    entireParsesDF = entireParsesDFIndex[parsesDFOrder]


    listOfConsumables = ['name', 'id', 'date', 'Fire Protection', 'Shadow Protection', 'Nature Protection', 'Frost Protection','Winterfall Firewater', 'Elixir of the Mongoose', 'Elixir of the Giants', 'Arcane Elixir','Frost Power', 'Greater Firepower', 'Shadow Power', 'Mana Regeneration', 'Increased Intellect','Greater Armor', 'Health II', 'Free Action', 'Invulnerability', 'Gordok Green Grog', 'Rumsey Rum Black Label', 'Cleansed Firewater']
    entireConsDataDF = pd.DataFrame(entire_cons_data)
    entireConsDF = entireConsDataDF[listOfConsumables]

    entireBuffsDF = pd.DataFrame(entire_buffs_data)

    entireDeathsDF = pd.DataFrame(entire_deaths_data)

    entireRaidTimesDF = pd.DataFrame(entire_raid_times_data)


    entireKillTimesDataDF = pd.DataFrame(entire_kill_times_data)
    entireKillTimesData1 = entireKillTimesDataDF.set_index(['date', 'boss', entireKillTimesDataDF.boss.eq(first_boss).cumsum()]).unstack(-2)
    entireKillTimesData1.index = entireKillTimesData1.index.droplevel(-1)
    entireKillTimesData1.columns = entireKillTimesData1.columns.droplevel(0)
    entireKillTimesData2 = entireKillTimesData1[killTimesDFOrder]
    entireKillTimesDF = entireKillTimesData2.reset_index()

    allDataFrames = {'entireParsesDF' : entireParsesDF, 'entireConsDF' : entireConsDF, 'entireBuffsDF' : entireBuffsDF, 'entireDeathsDF' : entireDeathsDF, 'entireRaidTimesDF' : entireRaidTimesDF, 'entireKillTimesDF': entireKillTimesDF}

    return allDataFrames


#The following functions: create the connection to the mysqlworkbench server, create tables and insert the data acquired.

#Returns the connection to the database.
def databaseConnection(zoneID, user, passwd):
    db_connection = None

    if zoneID == 2016:
        database = 'guildreportsaqzomb'
    elif zoneID == 2013:
        database = 'guildreportsBWLresist'

    try:
        db_connection = mysql.connector.connect(
            user=user,
            passwd=passwd,
            database= database
        )
        print('SQL database connection established')

    except mysql.connector.Error as error:
        print(f'Failed to connect with SQL database. Error message: {error}')

    return db_connection

#Re-usable function that inserts the supplied data into the corresponding table.
def executionFunct(db_connection, sqlStatement):

    try:
        cursorObj = db_connection.cursor()
        cursorObj.execute(operation = sqlStatement)
        db_connection.commit()
        print('Table successfully created')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')


#Creates a table that holds a guild's "raid time" data, across all of their reports for that instance.
def raidTimesTableCreation(db_connection):

    sqlStatement = """CREATE TABLE IF NOT EXISTS raidTime (
                            Date DATE,
                            `Raid clear time` TIME);"""

    executionFunct(db_connection, sqlStatement)


#Creates a table that holds a guild's "deaths" data, across all of their reports for that instance.
def deathsTableCreation(db_connection):

    sqlStatement = """CREATE TABLE IF NOT EXISTS deaths (
                            Names VARCHAR(255),
                            `Deaths count` INTEGER,
                            Date DATE);"""

    executionFunct(db_connection, sqlStatement)


#Creates a table that holds a guild's "kill_times" data (time taken to kill each boss), across all of their reports for that instance.
def killTimesTableCreation(db_connection, zoneID):

    bwl = ['Razorgore', 'Vaelastrasz', 'Broodlord', 'Firemaw', 'Flamegor', 'Chromaggus', 'Nefarian', 'BlankColumn1', 'BlankColumn2']
    aq = ['The Prophet Skeram', 'Silithid Royalty', 'Battleguard Sartura', 'Fankriss the Unyielding', 'Viscidus', 'Princess Huhuran', 'Twin Emperors', 'Ouro', 'C\'Thun']

    if zoneID == 2016:
        raid = aq
    if zoneID == 2013:
        raid = bwl

    sqlStatement = """CREATE TABLE IF NOT EXISTS kill_times (
                        Date DATE,
                        `{Boss1}` INTEGER,
                        `{Boss2}` INTEGER,
                        `{Boss3}` INTEGER,
                        `{Boss4}` INTEGER,
                        `{Boss5}` INTEGER,
                        `{Boss6}` INTEGER,
                        `{Boss7}` INTEGER,
                        `{Boss8}` INTEGER,
                        `{Boss9}` INTEGER);""".format(Boss1 = raid[0], Boss2 = raid[1], Boss3 = raid[2], Boss4 = raid[3], Boss5 = raid[4], Boss6 = raid[5], Boss7 = raid[6], Boss8 = raid[7], Boss9 = raid[8])

    executionFunct(db_connection, sqlStatement)


#Creates a table that holds a guild's "buffs" data, across all of their reports for that instance.
def buffsTableCreation(db_connection):

    sqlStatement = """CREATE TABLE IF NOT EXISTS buffs (
                            Date DATE,
                            Names VARCHAR(255),
                            `Rallying Cry of the Dragonslayer` INTEGER,
                            `Spirit of Zandalar` INTEGER,
                            `Might of Stormwind` INTEGER,
                            `Songflower Serenade` INTEGER,
                            `Fengus' Ferocity` INTEGER,
                            `Slip'kik's Savvy` INTEGER,
                            `Mol'dar's Moxie` INTEGER,
                            `Darkmoon Faire` INTEGER);"""

    executionFunct(db_connection, sqlStatement)


#Creates a table to hold a guild's "consumables" data, across all of their rports for that instance.
def consTableCreation(db_connection):

    sqlStatement = """CREATE TABLE IF NOT EXISTS consumables (
                            `Names` VARCHAR(255),
                            `IDs` INTEGER,
                            `Date` DATE,
                            `Fire Protection` INTEGER,
                            `Shadow Protection` INTEGER,
                            `Nature Protection` INTEGER,
                            `Frost Protection` INTEGER,
                            `Winterfall Firewater` INTEGER,
                            `Elixir of the Mongoose` INTEGER,
                            `Elixir of the Giants` INTEGER,
                            `Arcane Elixir` INTEGER,
                            `Frost Power` INTEGER,
                            `Greater Firepower` INTEGER,
                            `Shadow Power` INTEGER,
                            `Mana Regeneration` INTEGER,
                            `Increased Intellect` INTEGER,
                            `Greater Armor` INTEGER,
                            `Health II` INTEGER,
                            `Free Action` INTEGER,
                            `Invulnerability` INTEGER,
                            `Gordok Green Grog` INTEGER,
                            `Rumsey Rum Black Label` INTEGER,
                            `Cleansed Firewater` INTEGER);"""

    executionFunct(db_connection, sqlStatement)

#Creates a table to hold a guild's "parses" data, across all of their rports for that instance.
def parsesTableCreation(db_connection, zoneID):

    bwl = ['Razorgore', 'Vaelastrasz', 'Broodlord', 'Firemaw', 'Flamegor', 'Chromaggus', 'Nefarian', 'BlankColumn1', 'BlankColumn2']
    aq = ['The Prophet Skeram', 'Silithid Royalty', 'Battleguard Sartura', 'Fankriss the Unyielding', 'Viscidus', 'Princess Huhuran', 'Twin Emperors', 'Ouro', 'C\'thun']

    if zoneID == 2016:
        raid = aq
    if zoneID == 2013:
        raid = bwl

    sqlStatement = """CREATE TABLE IF NOT EXISTS parses (
                            `Names` VARCHAR(255),
                            `Date` DATE,
                            `{Boss1}` INTEGER,
                            `{Boss2}` INTEGER,
                            `{Boss3}` INTEGER,
                            `{Boss4}` INTEGER,
                            `{Boss5}` INTEGER,
                            `{Boss6}` INTEGER,
                            `{Boss7}` INTEGER,
                            `{Boss8}` INTEGER,
                            `{Boss9}` INTEGER);""".format(Boss1 = raid[0], Boss2 = raid[1], Boss3 = raid[2], Boss4 = raid[3], Boss5 = raid[4], Boss6 = raid[5], Boss7 = raid[6], Boss8 = raid[7], Boss9 = raid[8])

    executionFunct(db_connection, sqlStatement)


#Inserts the "consumables" data into its corresponding table.
def consDataInsertions(db_connection, entireConsDF):

    sqlStatement =  """INSERT INTO consumables (`Names`, `IDs`, `Date`, `Fire Protection`, `Shadow Protection`, `Nature Protection`, `Frost Protection`, `Winterfall Firewater`, `Elixir of the Mongoose`, `Elixir of the Giants`, `Arcane Elixir`, `Frost Power`, `Greater Firepower`, `Shadow Power`, `Mana Regeneration`, `Increased Intellect`, `Greater Armor`, `Health II`, `Free Action`, `Invulnerability`, `Gordok Green Grog`, `Rumsey Rum Black Label`, `Cleansed Firewater`)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

    consDataTuple = [tuple(cons) for cons in entireConsDF.to_numpy()]
    try:
        cursorObj = db_connection.cursor()
        cursorObj.executemany(sqlStatement, consDataTuple)
        db_connection.commit()
        print('Data insertion successful')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')


#Inserts the "deaths" data into its corresponding table.
def deathsDataInsertions(db_connection, entireDeathsDF):

    sqlStatement =  """INSERT INTO deaths (`Names`, `Deaths count`, `Date`)
                        VALUES (%s, %s, %s);"""

    deathsDataTuple = [tuple(deaths) for deaths in entireDeathsDF.to_numpy()]

    try:
        cursorObj = db_connection.cursor()
        cursorObj.executemany(sqlStatement, deathsDataTuple)
        db_connection.commit()
        print('Data insertion successful')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')


#Inserts the "kill times" data into its corresponding table.
def killTimesDataInsertions(db_connection, entireKillTimesDF, zoneID):

    bwl = "(`Date`, `Razorgore`, `Vaelastrasz`, `Broodlord`, `Firemaw`, `Flamegor`, `Chromaggus`, `Nefarian`)"
    aq = "(`Date`, `The Prophet Skeram`, `Silithid Royalty`, `Battleguard Sartura`, `Fankriss the Unyielding`, `Viscidus`, `Princess Huhuran`, `Twin Emperors`, `Ouro`, `C\'Thun`)"

    if zoneID == 2016:
        raid = aq
        params = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    if zoneID == 2013:
        raid = bwl
        params = "(%s, %s, %s, %s, %s, %s, %s, %s)"

    sqlStatement =  """INSERT INTO kill_times {raid}
                        VALUES {params};""".format(raid = raid, params= params)

    entireKillTimesDF = entireKillTimesDF.replace(numpy.nan, 0)
    killTimesDataTuple = [tuple(killTimes) for killTimes in entireKillTimesDF.to_numpy()]

    try:
        cursorObj = db_connection.cursor()
        cursorObj.executemany(sqlStatement, killTimesDataTuple)
        db_connection.commit()
        print('Data insertion successful')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')


#Inserts the "raid time" data into its corresponding table.
def raidTimesDataInsertions(db_connection, entireRaidTimesDF):

    sqlStatement =  """INSERT INTO raidtime (`Date`, `Raid clear time`)
                        VALUES (%s, %s);"""

    raidTimesDataTuple = [tuple(raidTimes) for raidTimes in entireRaidTimesDF.to_numpy()]

    try:
        cursorObj = db_connection.cursor()
        cursorObj.executemany(sqlStatement, raidTimesDataTuple)
        db_connection.commit()
        print('Data insertion successful')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')


#Inserts the "buffs" data into its corresponding table.
def buffsDataInsertions(db_connection, entireBuffsDF):

    sqlStatement =  """INSERT INTO buffs (`Date`, `Names`, `Spirit of Zandalar`,`Rallying Cry of the Dragonslayer`, `Might of Stormwind`, `Songflower Serenade`, `Fengus' Ferocity`, `Slip'kik's Savvy`, `Mol'dar's Moxie`, `Darkmoon Faire`)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

    entireBuffsDF = entireBuffsDF.replace(numpy.nan, 0)
    buffsDataTuple = [tuple(buffs) for buffs in entireBuffsDF.to_numpy()]

    try:
        cursorObj = db_connection.cursor()
        cursorObj.executemany(sqlStatement, buffsDataTuple)
        db_connection.commit()
        print('Data insertion successful')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')


#Inserts the "parses" data into its corresponding table.
def parsesDataInsertions(db_connection, entireParsesDF, zoneID):

    bwl = "(`Names`, `Date`, `Razorgore`, `Vaelastrasz`, `Broodlord`, `Firemaw`, `Flamegor`, `Chromaggus`, `Nefarian`)"
    aq = "(`Names`, `Date`, `The Prophet Skeram`, `Silithid Royalty`, `Battleguard Sartura`, `Fankriss the Unyielding`, `Viscidus`, `Princess Huhuran`, `Twin Emperors`, `Ouro`, `C\'Thun`)"

    if zoneID == 2016:
        raid = aq
        params = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    if zoneID == 2013:
        raid = bwl
        params = "(%s, %s, %s, %s, %s, %s, %s, %s, %s)"

    sqlStatement =  """INSERT INTO parses {raid}
                        VALUES {params};""".format(raid = raid, params= params)


    entireParsesDF = entireParsesDF.replace(numpy.nan, 0)
    parsesDataTuple = [tuple(parses) for parses in entireParsesDF.to_numpy()]

    try:
        cursorObj = db_connection.cursor()
        cursorObj.executemany(sqlStatement, parsesDataTuple)
        db_connection.commit()
        print('Data insertion successful')

    except mysql.connector.Error as e:
        print(rf'The following error has occurred: {e}')



#Creates the dataframes using the provided data, creates tables in the users MySQL Workbench, and inserts the data

print("Please enter the username of your MySQL Workbench database.")
user = input()
print("Please enter the password of your MySQL Workbench database.")
passwd = input()

def etlPipeline(zoneID, user, passwd):

    connection = databaseConnection(zoneID, user, passwd)

    data = creatingDataFrames(zoneID, entire_parses_data, entire_cons_data, entire_buffs_data, entire_deaths_data, entire_raid_times_data, entire_kill_times_data)

    killTimesTableCreation(connection, zoneID)
    deathsTableCreation(connection)
    raidTimesTableCreation(connection)
    buffsTableCreation(connection)
    consTableCreation(connection)
    parsesTableCreation(connection, zoneID)

    deathsDataInsertions(connection, data['entireDeathsDF'])
    killTimesDataInsertions(connection, data['entireKillTimesDF'], zoneID)
    raidTimesDataInsertions(connection, data['entireRaidTimesDF'])
    buffsDataInsertions(connection, data['entireBuffsDF'])
    consDataInsertions(connection, data['entireConsDF'])
    parsesDataInsertions(connection, data['entireParsesDF'], zoneID)

etlPipeline(zoneID, user, passwd)

end_script = time.time()
running_time = end_script - start_script
runTimeMins = round(running_time/60, 2)
print(f'{runTimeMins} minutes taken to complete the running of this script.')
