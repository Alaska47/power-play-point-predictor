import os
import sys
import requests
import requests_cache
from bs4 import BeautifulSoup
from datetime import datetime

import lxml
import cchardet
import unicodedata
import re
import json

WEBSITE_PREFIX = "https://naturalstattrick.com/"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def get_html_for_natural_stat_trick_for_path(path):
    return requests.get(WEBSITE_PREFIX + path, headers=headers).text

os.makedirs("data", exist_ok=True)

FROM_SEASON = 2023
TO_SEASON = 2024
GAME_DATA_LINK_TEMPLATE = "games.php?fromseason={}&thruseason={}&stype=2&sit={}&loc=B&team=All&rate=n"
EXISTING_DATA_FILES = set(os.listdir("data"))
MISSING_DATA_VAL = -999

nhl_teams = {
    'Anaheim Ducks': 'Ducks',
    'Arizona Coyotes': 'Coyotes',
    'Boston Bruins': 'Bruins',
    'Buffalo Sabres': 'Sabres',
    'Calgary Flames': 'Flames',
    'Carolina Hurricanes': 'Hurricanes',
    'Chicago Blackhawks': 'Blackhawks',
    'Colorado Avalanche': 'Avalanche',
    'Columbus Blue Jackets': 'Blue Jackets',
    'Dallas Stars': 'Stars',
    'Detroit Red Wings': 'Red Wings',
    'Edmonton Oilers': 'Oilers',
    'Florida Panthers': 'Panthers',
    'Los Angeles Kings': 'Kings',
    'Minnesota Wild': 'Wild',
    'Montreal Canadiens': 'Canadiens',
    'Nashville Predators': 'Predators',
    'New Jersey Devils': 'Devils',
    'New York Islanders': 'Islanders',
    'New York Rangers': 'Rangers',
    'Ottawa Senators': 'Senators',
    'Philadelphia Flyers': 'Flyers',
    'Pittsburgh Penguins': 'Penguins',
    'San Jose Sharks': 'Sharks',
    'Seattle Kraken': 'Kraken',
    'St Louis Blues': 'Blues',
    'Tampa Bay Lightning': 'Lightning',
    'Toronto Maple Leafs': 'Maple Leafs',
    'Vancouver Canucks': 'Canucks',
    'Vegas Golden Knights': 'Golden Knights',
    'Washington Capitals': 'Capitals',
    'Winnipeg Jets': 'Jets'
}

def minutes_seconds_to_decimal(time_str):
    if(time_str.strip() == "0"):
        return 0
    
    # Split the string into minutes and seconds
    minutes, seconds = map(int, time_str.split(':'))

    # Calculate the decimal representation in minutes
    decimal_minutes = minutes + seconds / 60.0

    return decimal_minutes

# Stats I care about
# PK_TOI, how often you give up penalties (want the opponent to have a low value)
# PP_CF, how many shot opportunities you get during a power play (want team to have a low value)
# PK_CA, how many shot opportunities you conceded during a power play (want opponent to have a low value)
# PP_SF, how many SOG you get during a power play (want team to have a low value)
# PK_SA, how many SOG you conceded during a power play (want opponent to have a low value)
# PP_GF, how many goals you score during a power play (want team to have a low value)
# PK_GA, how many goals you conceded during a power play (want opponent to have a low value)
# PP_OPP, how many power play opportunities you get during the game (want team to have a low value)
# PP_SHOOT_PERCENT, what percentage of shots are on goal during power play (want team to have a low value)
# PK_SAVE_PERCENT, what percentage of shots are saved during a power play (want opponent to have a high value)
# PP_PERCENT, what percentage of power plays is a goal scored (want team to have a low value)
# PK_PERCENT, what percentage of power plays are killed (want opponent to have a high value)


pp_soup = BeautifulSoup(get_html_for_natural_stat_trick_for_path(GAME_DATA_LINK_TEMPLATE.format("{}{}".format(FROM_SEASON, FROM_SEASON + 1), "{}{}".format(TO_SEASON - 1, TO_SEASON), "pp")), features="html5lib")
pp_soup = BeautifulSoup(get_html_for_natural_stat_trick_for_path(GAME_DATA_LINK_TEMPLATE.format("{}{}".format(FROM_SEASON, FROM_SEASON + 1), "{}{}".format(TO_SEASON - 1, TO_SEASON), "pk")), features="html5lib")

thead = pp_soup.find('table', id="teams").find('thead')
column_names = [column.text for column in thead.find_all('th')]
column_idx_to_name_mapping = {idx: name for idx, name in enumerate(column_names)}
column_name_to_idx_mapping = {name: idx for idx, name in enumerate(column_names)}

pp_tbody = pp_soup.find('table', id="teams").find('tbody')
pk_tbody = pk_soup.find('table', id="teams").find('tbody')
if pp_tbody and pk_tbody:
    pp_rows = pp_tbody.find_all('tr')
    pk_rows = pk_tbody.find_all('tr')
    print("Got {} rows for PP, and {} rows for PK".format(len(pp_rows), len(pk_rows)))

    for i in range(0, min(len(pp_rows), len(pk_rows))):
        pp_row = pp_rows[i]
        pk_row = pk_rows[i]

        pp_col_vals = [(str(MISSING_DATA_VAL) if item == "-" else item) for c in pp_row.find_all('td') for item in [c.text]]
        pk_col_vals = [(str(MISSING_DATA_VAL) if item == "-" else item) for c in pk_row.find_all('td') for item in [c.text]]
        
        # Verify game date
        pp_game_ft_val = pp_col_vals[column_name_to_idx_mapping["Game"]].split(" - ")[0].strip()
        pp_game_ft_val = datetime.strptime(pp_game_ft_val, "%Y-%m-%d")
        pk_game_ft_val = pk_col_vals[column_name_to_idx_mapping["Game"]].split(" - ")[0].strip()
        pk_game_ft_val = datetime.strptime(pk_game_ft_val, "%Y-%m-%d")
        assert pp_game_ft_val == pk_game_ft_val

        # Verify team name
        try:
            assert pp_col_vals[column_name_to_idx_mapping["Team"]] == pk_col_vals[column_name_to_idx_mapping["Team"]]
        except AssertionError:
            print("Comparing {} and {}".format(pp_col_vals[column_name_to_idx_mapping["Team"]], pk_col_vals[column_name_to_idx_mapping["Team"]]))
            print(pp_col_vals)
            print(pk_col_vals)
            print("Before")
            print([(str(MISSING_DATA_VAL) if item == "-" else item) for c in pp_rows[i - 1].find_all('td') for item in [c.text]])
            raise
        

        team_data_map = {}
        team_data_map["Game"] = pp_game_ft_val.isoformat()
        team_data_map["Team"] = pp_col_vals[column_name_to_idx_mapping["Team"]]
        full_report_link_path = pp_row.find_all('td')[column_name_to_idx_mapping[""]].find('a', string=lambda text: text and "Full" in text)['href']
        game_id = re.search(r'game=(\d+)', full_report_link).group(1)
        file_name = "{}_{}.json".format(nhl_teams[team_data_map["Team"]].lower(), game_id)
        if(file_name in EXISTING_DATA_FILES):
            print("Skipping, already found: {}".format(file_name))
            continue
        print("Analyzing {} - {}".format(team_data_map["Game"], team_data_map["Team"]))

        team_data_map["PK_TOI"] = float(minutes_seconds_to_decimal(pk_col_vals[column_name_to_idx_mapping["TOI"]]))
        team_data_map["PP_CF"] = float(pp_col_vals[column_name_to_idx_mapping["CF"]])
        team_data_map["PK_CA"] = float(pk_col_vals[column_name_to_idx_mapping["CA"]])
        team_data_map["PP_SF"] = float(pp_col_vals[column_name_to_idx_mapping["SF"]])
        team_data_map["PK_SA"] = float(pk_col_vals[column_name_to_idx_mapping["SA"]])
        team_data_map["PP_GF"] = float(pp_col_vals[column_name_to_idx_mapping["GF"]])
        team_data_map["PK_GA"] = float(pk_col_vals[column_name_to_idx_mapping["GA"]])
        team_data_map["PP_SHOOT_%"] = float(pp_col_vals[column_name_to_idx_mapping["SH%"]])
        team_data_map["PK_SAVE_%"] = float(pk_col_vals[column_name_to_idx_mapping["SV%"]])

        # Extract full report
        full_report_soup = BeautifulSoup(get_html_for_natural_stat_trick_for_path(full_report_link_path), features="lxml")
        label = full_report_soup.find('label', string="{} - Power Plays".format(nhl_teams[team_data_map["Team"]]))
        if label:
            div = label.find_next('div')
            if div:
                header_tags = div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                header_count = len(header_tags)
                team_data_map["PP_OPP"] = header_count
            else:
                print("Eror, couldn't find div containing power plays")
        else:
            print("Error, couldn't find label with the name: {}".format("{} - Power Plays".format(nhl_teams[team_data_map["Team"]])))
        team_data_map["PP%"] = ((team_data_map["PP_GF"] + 1) / (team_data_map["PP_OPP"] + 1)) * 100
        team_data_map["PK%"] = (((team_data_map["PP_OPP"] - team_data_map["PK_GA"]) + 1) / (team_data_map["PP_OPP"] + 1)) * 100

        # Get player stats
        team_data_map["players"] = []
        label_div = full_report_soup.find('label', string="{} - Individual".format(nhl_teams[team_data_map["Team"]])).find_parent('div')
        div_tpp_datadiv = label_div.find('div', class_='tpp datadiv')
        skaters_h3 = div_tpp_datadiv.find('h3', string='Skaters')
        table = skaters_h3.find_next('table')

        # Extract the column names from the table header
        player_column_names = [th.text for th in table.find("thead").find_all(['th', 'td'])]
        player_column_name_to_idx_mapping = {name: idx for idx, name in enumerate(player_column_names)}
        for player_row in table.find("tbody").find_all('tr'):
            player_stats = {}
            player_col_vals = [c.text for c in player_row.find_all('td')]
            player_stats["name"] = unicodedata.normalize("NFKD", player_col_vals[player_column_name_to_idx_mapping["Player"]])
            player_stats["TOI"] = float(player_col_vals[player_column_name_to_idx_mapping["TOI"]])
            player_stats["points"] = float(player_col_vals[player_column_name_to_idx_mapping["Total Points"]])
            player_stats["iCF"] = float(player_col_vals[player_column_name_to_idx_mapping["iCF"]])
            player_stats["iSCF"] = float(player_col_vals[player_column_name_to_idx_mapping["iSCF"]])
            player_stats["iHDCF"] = float(player_col_vals[player_column_name_to_idx_mapping["iHDCF"]])
            team_data_map["players"].append(player_stats)
        
        game_id = re.search(r'game=(\d+)', full_report_link).group(1)
        file_path = os.path.join("data", file_name)
        # Write the JSON data to the file
        with open(file_path, "w") as json_file:
            json.dump(team_data_map, json_file, indent=4)





