import requests
import requests_cache
from bs4 import BeautifulSoup
from datetime import datetime

requests_cache.install_cache('my_cache.db')

GAME_DATA_LINK = "https://www.naturalstattrick.com/games.php?fromseason=20232024&thruseason=20232024&stype=2&sit=pp&loc=B&team=All&rate=n"

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
# PK_SHOOT_AGAINST, what percentage of shots against team are on goal during power play (want opponent to have a low value)
# PK_SAVE_PERCENT, what percentage of shots are saved during a power play (want opponent to have a high value)
# PP_PERCENT, what percentage of power plays is a goal scored (want team to have a low value)
# PK_PERCENT, what percentage of power plays are killed (want opponent to have a high value)

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

response = requests.get(GAME_DATA_LINK, headers=headers)
html = response.text
soup = BeautifulSoup(html, features="html.parser")

thead = soup.find('thead')
column_names = [column.text for column in thead.find_all('th')]
column_idx_to_name_mapping = {idx: name for idx, name in enumerate(column_names)}
column_name_to_idx_mapping = {name: idx for idx, name in enumerate(column_names)}

tbody = soup.find('tbody')
if tbody:
    rows = tbody.find_all('tr')

    for i in range(0, len(rows), 2):
        # Select rows in pairs
        row1 = rows[i]
        row2 = rows[i + 1] if i + 1 < len(rows) else None

        col1_vals = [c.text for c in row1.find_all('td')]
        col2_vals = [c.text for c in row2.find_all('td')]
        col_vals = [col1_vals, col2_vals]
        
        # Extract game date
        game1_ft_val = col1_vals[column_name_to_idx_mapping["Game"]].split(" - ")[0].strip()
        game1_ft_val = datetime.strptime(game1_ft_val, "%Y-%m-%d")
        game2_ft_val = col2_vals[column_name_to_idx_mapping["Game"]].split(" - ")[0].strip()
        game2_ft_val = datetime.strptime(game2_ft_val, "%Y-%m-%d")
        assert game1_ft_val == game2_ft_val

        team_data_map = [{"Game": game1_ft_val}, {"Game": game2_ft_val}]

        for x in range(2):
            # Extract the team name
            team_data_map[x]["Team"] = col_vals[x][column_name_to_idx_mapping["Team"]]

            # Extract PK_TOI
            team_data_map[x]["PK_TOI"] = col_vals[1 - x][column_name_to_idx_mapping["TOI"]]

            # Extract PP_CF
            team_data_map[x]["PP_CF"] = col_vals[x][column_name_to_idx_mapping["CF"]]

            # Extract PK_CA
            team_data_map[x]["PK_CA"] = col_vals[1 - x][column_name_to_idx_mapping["CA"]]

            # Extract PP_SF
            team_data_map[x]["PP_SF"] = col_vals[x][column_name_to_idx_mapping["SF"]]

            # Extract PK_SA
            team_data_map[x]["PK_SA"] = col_vals[1 - x][column_name_to_idx_mapping["SA"]]

            # Extract PP_GF
            team_data_map[x]["PP_GF"] = col_vals[x][column_name_to_idx_mapping["GF"]]

            # Extract PK_GA
            # team_data_map[x]["PK_CA"] = col_vals[1 - x][column_name_to_idx_mapping["GA"]]

        break

print(team_data_map)





