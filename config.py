# Your Steam Web API key. These may be acquired from:
# https://steamcommunity.com/dev/apikey
STEAM_API_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

# Name of file in which to store raw data.
MATCH_DATA_FILE = 'matches.json'

# Filtering parameters for fetching match data. Values as stated at:
# https://wiki.teamfortress.com/wiki/WebAPI/GetMatchDetails#Result_data
game_mode = 1, 22  # All pick (22 has replaced 1 in games since ranked matchmaking was introduced).
# Can specify multiple lobby types by comma separating values.
lobby_type = 0, 7  # 0 Public matchmaking, 7 ranked.
human_players = 10

# Match IDs from which to fetch data.
# Set "start_match_id = None" to find and use the first match of the current patch.
# Set to "start_match_id = 'latest'" to use the most recent match stored in the local database.
start_match_id = None  # Patch 7.25 begins on match 5298181556.
# Set "end_match_id = 'latest'" to use the most recent match played.
end_match_id = 'latest'

# Name of file in which to store training data.
TRAINING_DATA_FILE = 'training_data.json'
# Match IDs from which to create training data.
# Set "training_start_match_id = None" for no restriction on start.
training_start_match_id = None
# Set "training_end_match_id = None" for no restriction on end.
training_end_match_id = None

# Language for hero names.
LANGUAGE = 'english'
# Name of file in which to store hero data.
HERO_DATA_FILE = 'heroes.json'
