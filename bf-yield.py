# BF-AFK-Yield.py
# Copyright (C) 2019 Andrew "Azure-Agst" Augustine

# Imports
import sys
import math
import os
import webbrowser
import secrets
import requests
import json
import configparser
import time
from datetime import datetime, timedelta
from optparse import OptionParser

# GLOBAL VARS
version = "2.1.0"
base_url = "https://www.bungie.net/Platform"
from bungie_api import api_key, client_id, client_secret

# Parse Options
parser = OptionParser()
parser.add_option("-o", "--offline", dest="offline", action="store_true", help="Reverts to the old offline calculator")
parser.add_option("-c", "--config", dest="infile", action="store", type="string", help="Use specified config.ini")
parser.add_option("-l", "--live-view", dest="live", action="store_true", help="If used with api, enables live view of the inventory! (Can also be triggered by setting Main.Live to True in config.ini)")
(options, args) = parser.parse_args()

# Init config
config = configparser.ConfigParser()
configLocation = os.getenv('LOCALAPPDATA')+"\\bf-yield\\config.ini"
if options.infile and not os.path.exists(options.infile):
    print("Error: Specified config file does not exist! Exiting...")
    time.sleep(1)
    sys.exit(1)
elif options.infile:
    configLocation = options.infile
config.read(configLocation)
if "Main" not in config:
    config['Main'] = {'Live': 'False'}
if "API" not in config:
    config['API'] = {}


##########################
# SUPPLEMENTAL FUNCTIONS #
##########################

# Log
def log(string):
    with open(os.getenv('LOCALAPPDATA')+"\\bf-yield\\log.txt", 'w') as log:
        log.truncate(0)
        log.write(str(string))
        log.close()

# Print Title
def printTitle():
    os.system('cls')
    print("Destiny 2 BF-AFK Yield Calculator v{}".format(version))
    print("Copyright (C) 2019 Azure-Agst")

# Save Config
def saveConfig():
    if options.infile:
        with open(options.infile, 'w') as configfile:
            config.write(configfile)
    else:
        if not os.path.exists(os.getenv('LOCALAPPDATA')+"\\bf-yield"):
            os.mkdir(os.getenv('LOCALAPPDATA')+"\\bf-yield", 0o755)
        with open(os.getenv('LOCALAPPDATA')+"\\bf-yield\\config.ini", 'w') as configfile:
            config.write(configfile)
    print("Saved config!")

# Kill App Function
def quitApp():
    saveConfig()
    input("Press any key to exit...")
    sys.exit(0)


#########################
# API-RELATED FUNCTIONS #
#########################

# Get Access Token
def getAccessToken():
    print("\nNo cached token found! Need to (re)authenticate!")
    print("\nIn 3 seconds, your browser will open to the Bungie OAuth URL. Authorize the app, then paste the code you recieve below.")
    state = secrets.token_hex(8)
    url = "https://www.bungie.net/en/oauth/authorize?client_id={}&response_type=code&state={}".format(client_id, state)
    time.sleep(3)
    webbrowser.open_new(url)
    oauth = input("Code: ").split('|')
    print("") # Literallly for spacing
    if oauth[0] != state:
        print("ERROR: State does not match! Quitting app...")
        quitApp()
    else:
        postData = {'grant_type': 'authorization_code', 'code': oauth[1], 'client_id':client_id, 'client_secret': client_secret}
        tokenRes = json.loads(requests.post("https://www.bungie.net/Platform/App/OAuth/token/", data=postData).text)
        if "error" in tokenRes:
            print("ERROR: Error while getting token! ")
            print(tokenRes)
            print("Quitting app...")
            quitApp()
        else:
            config['API'] = tokenRes
            config['API']['time_granted'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            return 

# Refresh Token
def refreshToken():
    print("Refreshing Cached Token...")
    postData = {'grant_type': 'refresh_token', 'refresh_token': config['API']['refresh_token'], 'client_id':client_id, 'client_secret': client_secret }
    tokenRes = json.loads(requests.post("https://www.bungie.net/Platform/App/OAuth/token/", data=postData).text)
    if "error" in tokenRes:
        print("ERROR: Error while refreshing token!")
        print(tokenRes)
        print("Quitting app...")
        quitApp()
    else:
        config['API'] = tokenRes
        config['API']['time_granted'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        return 
    
# Get User Memberships
def getUserMembership(headers):
    try:
        membResTemp = requests.get("{}/User/GetMembershipsForCurrentUser/".format(base_url), headers=headers)
    except requests.exceptions.ConnectionError:
        print("Get User Memberships Failed? Probably isolated, however this error's fatal. Launch app again!")
        return quitApp()
    membRes = json.loads(membResTemp.text)
    if 'ErrorCode' in membRes:
        if membRes['ErrorCode'] == 99:
            print("Encountering error 99 'WebAuthRequired'...")
            quitApp()
    user = membRes["Response"]["destinyMemberships"][0]
    print("Logged in as user: {}\n".format(user["displayName"]))
    return [user["membershipType"], user["membershipId"]]

# Get Latest Character
def getLatestChar(headers, membership):
    latestCharId = ""
    try:
        charRes = json.loads(requests.get("{}/Destiny2/{}/Profile/{}/?components=Characters".format(base_url, membership[0], membership[1]), headers=headers).text)
    except requests.exceptions.ConnectionError:
        print('Get Latest Character Request Failed? Probably isolated. Try again!')
        return latestCharId
    characters = charRes["Response"]["characters"]["data"]
    latestTime = datetime.now() - timedelta(days=1)
    for key in characters:
        char = characters[key]
        charTime = datetime.strptime(char["dateLastPlayed"], '%Y-%m-%dT%H:%M:%SZ')
        if charTime > latestTime:
            latestTime = charTime
            latestCharId = char["characterId"]
    if latestCharId == "":
        print("No character has logged in within the past 24 hours! Exiting...")
        quitApp()
    else:
        return latestCharId

# Get Character Inventories
def getItemCount(headers, membership, latestCharId):
    materials = {"dusk": 0, "data": 0}
    while True:
        try:
            res = requests.get("{}/Destiny2/{}/Profile/{}/?components=ProfileInventories,CharacterInventories".format(base_url, membership[0], membership[1]), headers=headers).text
            log(res)
            invenRes = json.loads(res)
        except requests.exceptions.ConnectionError:
            print('Character Inventories Request Failed? Probably isolated. Try again!')
            return materials
        except json.decoder.JSONDecodeError:
            print('Token expired. Refreshing!')
            refreshToken()
        if invenRes['ErrorCode'] == 99:
            refreshToken()
        else:
            break
    inventories = { 'Inventory': invenRes["Response"]["profileInventory"]["data"]["items"], 'Postmaster': invenRes["Response"]["characterInventories"]["data"][latestCharId]["items"] }
    for invenName in inventories:
        for item in inventories[invenName]:
            if item["itemHash"] == 950899352:
                materials['dusk'] += item['quantity']
                if not options.live and not config['Main']['Live'] == 'True':
                    print("Found {} Dusklight in {}!".format(item['quantity'], invenName))
            elif item["itemHash"] == 3487922223:
                materials['data'] += item['quantity']
                if not options.live and not config['Main']['Live'] == 'True':
                    print("Found {} Datalattice in {}!".format(item['quantity'], invenName))
    return materials


########################
# Calculator Functions #
########################

# Online Calculator
def calcNewAPI():
    print("\nLaunched in API mode.")
    if "access_token" not in config["API"]:
        getAccessToken()
    else:
        print("\nCached access token found!")
        if datetime.strptime(config['API']['time_granted'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=int(config['API']['expires_in'])) < datetime.now():
            refreshToken()
    
    req_headers = {'Authorization': ("Bearer "+config['API']['access_token']), 'X-API-Key': api_key}

    # Start fuckin with the API
    membership = getUserMembership(req_headers)
    latestChar = getLatestChar(req_headers, membership)

    # Save config, in case of runtime error
    saveConfig()

    # Switch
    if options.live or config['Main']['Live'] == 'True':
        try:
            while 1:
                materials = getItemCount(req_headers, membership, latestChar)
                printTitle()
                calculator(materials)
                for x in range(30):
                    print("[ {} seconds to refresh. Press Ctrl-C to exit. ]".format(str(29-x).zfill(2)), end="\r")
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n") # For spacing.
            quitApp()
    else:
        materials = getItemCount(req_headers, membership, latestChar)
        calculator(materials)
        quitApp()


# Offline Calculator
def offlineCalc():
    print("\nLaunched in offline mode.\n")
    numDusk = int(input("How much Dusklight? (Enter 0 for no Dusklight calculations) \n -> "))
    numData = int(input("How much Datalattice? (Enter 0 for no Datalattice calculations) \n -> "))
    calculator({"dusk": numDusk, "data": numData})


# Calculator Engine
def calculator(materials):
    #printTitle()
    for key in materials:
        itemname = {"dusk": "Dusklight", "data": "Datalattice"}
        if materials[key] < 55:
            print("\nSkipping {}, not enough to claim a full engram...".format(itemname[key]))
            continue

        # Item Name
        print("\nItem:", itemname[key])

        # Amount
        print(" - Amount:", materials[key])

        # Engrams
        engrams = math.floor(materials[key]/55)
        print(" - Engrams:", engrams)

        # Shards
        minshards = engrams*6
        maxshards = engrams*10
        print(" - LShards: [ Min: {}, Max: {}, Est: {} ]".format(minshards, maxshards, engrams*8))

        # Curated Drops
        curated = round(engrams/10) # 10% is an estimated value based of my IRL stats
        print(" - Curated rolls:", curated)
    print("") # Spacing.
    if materials["dusk"] == 0 and materials["data"] == 0:
        print("Looks like we've encountered a error. Data will be restored on next refresh.\n")

# Main Switch
printTitle()
if options.offline:
    offlineCalc()
else:
    calcNewAPI()

# Just in case it doesn't exit already
quitApp()