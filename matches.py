"""Retrieves Dota match data and outputs it to file as JSON."""
import json
import time

import requests

import config
from process import write_json_data

REQUEST_PERIOD_OPENDOTA = 1  # seconds
REQUEST_PERIOD_STEAM = 1  # seconds

last_call_opendota = None
last_call_steam = None


def rate_limited(request_period, last_call_time, request_function, *args, **kwargs):
    """Delay function call if too little time has passed."""
    if last_call_time is None:
        last_call_time = -request_period
    while True:
        current_time = time.perf_counter()
        time_since_last_call = current_time - last_call_time
        if time_since_last_call < request_period:
            time.sleep(request_period - time_since_last_call)
        try:
            response = request_function(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print('ConnectionError. Waiting before retrying.')
            time.sleep(30)
            continue
        last_call_time = time.perf_counter()
        status = response.status_code
        if status == 429 or status == 503:  # 429 Too Many Requests, 503 Service Unavailable.
            print('HTTP status code: {}. Waiting before retrying.'.format(status))
            time.sleep(30)
            continue
        break
    return response, last_call_time


def get_match_details(match_id):
    """Return response object for the Steam Web API GetMatchDetails method.

    https://wiki.teamfortress.com/wiki/WebAPI/GetMatchDetails
    """
    base = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1'
    payload = {'key': config.STEAM_API_KEY, 'match_id': match_id}
    global last_call_steam
    response, last_call_steam = rate_limited(REQUEST_PERIOD_STEAM, last_call_steam, requests.get, base, params=payload)
    return response


def get_match_history(**kwargs):
    """Return response object for the Steam Web API GetMatchHistory method.

    https://wiki.teamfortress.com/wiki/WebAPI/GetMatchHistory
    """
    base = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1'
    if 'key' not in kwargs:
        kwargs['key'] = config.STEAM_API_KEY
    global last_call_steam
    response, last_call_steam = rate_limited(REQUEST_PERIOD_STEAM, last_call_steam, requests.get, base, params=kwargs)
    return response


def get_match_history_by_seq_num(start_at_match_seq_num, matches_requested=100):
    """Return response object for the Steam Web API GetMatchHistoryBySequenceNum method.

    https://wiki.teamfortress.com/wiki/WebAPI/GetMatchHistoryBySequenceNum
    """
    base = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v1'
    payload = {'key': config.STEAM_API_KEY, 'start_at_match_seq_num': start_at_match_seq_num,
               'matches_requested': matches_requested}
    global last_call_steam
    response, last_call_steam = rate_limited(REQUEST_PERIOD_STEAM, last_call_steam, requests.get, base, params=payload)
    return response


def get_opendota_match(match_id):
    """Return response object for OpenDota API GET /matches/{match_id}.

    https://docs.opendota.com/#tag/matches%2Fpaths%2F~1matches~1%7Bmatch_id%7D%2Fget
    """
    base = 'https://api.opendota.com/api/matches/'
    request_url = base + str(match_id)
    global last_call_opendota
    response, last_call_opendota = rate_limited(REQUEST_PERIOD_OPENDOTA, last_call_opendota, requests.get, request_url)
    return response


def latest_match_id():
    """Return the match ID of the most recently played match."""
    for attempt in range(5):
        latest_match = get_match_history(matches_requested=1)
        request_status = latest_match.status_code
        if request_status == 200:
            result = latest_match.json()['result']
            if result['status'] == 1:
                latest_id = result['matches'][0]['match_id']
                return latest_id
            else:
                print('latest_match_id statusDetail: ' + result['statusDetail'])
                break
        else:
            print('HTTP status code: {}. Waiting to retry...'.format(request_status))
            time.sleep(30)
    else:
        raise requests.exceptions.RetryError('latest_match_id exceeded maximum number of attempts.')


def greatest_database_seq_num(filename):
    """Return the greatest match sequence number stored in the local database."""
    with open(filename) as data:
        database = json.load(data)
    matches = database['matches']
    match_seq_nums = [m['match_seq_num'] for m in matches]
    return max(match_seq_nums)


def smallest_database_match_id(filename):
    """Return the smallest match ID stored in the local database."""
    with open(filename) as data:
        database = json.load(data)
    matches = database['matches']
    match_ids = [m['match_id'] for m in matches]
    return min(match_ids)


def current_patch_match_id():
    """Return the match ID for the first match of the current patch.

    Uses a binary search algorithm.
    """
    match_id_lower = 0
    match_id_upper = latest_match_id()
    current_patch = get_opendota_match(match_id_upper).json()['patch']
    api_calls = 1
    while match_id_upper - match_id_lower > 1:
        match_id_mid = (match_id_lower + match_id_upper) // 2
        opendota_match = get_opendota_match(match_id_mid)
        status_code = opendota_match.status_code
        api_calls += 1
        if status_code == 404:  # Match ID not found.
            # Expand match ID ball around midpoint until endpoints are valid match IDs.
            match_id_ball_lower = match_id_mid - 1
            match_id_ball_upper = match_id_mid + 1
            while True:
                opendota_match_lower = get_opendota_match(match_id_ball_lower)
                api_calls += 1
                if opendota_match_lower.status_code == 200:
                    break
                match_id_ball_lower -= 1
            while True:
                opendota_match_upper = get_opendota_match(match_id_ball_upper)
                api_calls += 1
                if opendota_match_upper.status_code == 200:
                    break
                match_id_ball_upper += 1
            # Update bounds on match IDs accordingly.
            patch_lower = opendota_match_lower.json()['patch']
            patch_upper = opendota_match_upper.json()['patch']
            if patch_upper < current_patch:
                match_id_lower = match_id_ball_upper
            elif patch_lower == current_patch:
                match_id_upper = match_id_ball_lower
            else:
                match_id_upper = match_id_ball_upper
                break
        elif status_code == 200:
            patch = opendota_match.json()['patch']  # Patch of midpoint.
            # Update bounds on match IDs accordingly.
            if patch < current_patch:
                match_id_lower = match_id_mid
            else:
                match_id_upper = match_id_mid
        else:
            print('Failed to find first match ID of current patch.')
            return
    print('Fetched patch match ID ({}). {} OpenDota API calls made.'.format(match_id_upper, api_calls))
    return match_id_upper


def fetch_matches(filename, game_mode, lobby_type, human_players=10, start_match_id=None, end_match_id=None):
    """Fetch matches and write data to file if specified conditions are met."""
    max_match_length = 18000  # seconds
    # Setup start sequence number.
    if start_match_id == 'latest':
        try:
            search_start_seq_num = greatest_database_seq_num(filename)
        except FileNotFoundError:
            print("{} not found. Cannot use start_match_id = 'latest' in config.".format(filename))
            return
        start_match_id = smallest_database_match_id(filename)
    else:
        if start_match_id is None:
            start_match_id = current_patch_match_id()
        start_match = get_match_details(start_match_id)
        start_match_result = start_match.json()['result']
        if 'error' in start_match_result:
            print('start_match_id: ' + start_match_result['error'])
            return
        start_seq_num = start_match_result['match_seq_num']
        search_start_seq_num = start_seq_num - max_match_length

    # Setup end sequence number.
    if end_match_id == 'latest':
        end_match_id = latest_match_id()
    end_match = get_match_details(end_match_id)
    end_match_result = end_match.json()['result']
    if 'error' in end_match_result:
        print('end_match_id: ' + end_match_result['error'])
        return
    end_seq_num = end_match_result['match_seq_num']
    end_search_seq_num = end_seq_num + max_match_length

    # Read existing data.
    try:
        with open(filename) as data:
            database = json.load(data)
        data_size = database['data_size']
        matches = database['matches']
    except FileNotFoundError:
        data_size = 0
        matches = []
    match_id_set = {m['match_id'] for m in matches}

    matches_requested = 100
    no_abandon_leaver_status = {0, 1}
    new_matches_fetched = 0
    num_matches_fetched = 0
    new_matches = []
    seq_num = search_start_seq_num
    # Loop through GetMatchHistoryBySequenceNum responses from smallest to largest sequence number.
    while seq_num < end_search_seq_num:
        for attempt in range(20):
            try:
                response = get_match_history_by_seq_num(seq_num, matches_requested)
                decoded_response = response.json()
            except json.JSONDecodeError:
                print('JSONDecodeError. Waiting before retrying...')
                time.sleep(30)
                continue
            break
        else:
            raise json.JSONDecodeError
        result = decoded_response['result']
        # Check that response contains good data.
        if result['status'] == 1:
            # Add matches to database if specified conditions are met.
            api_matches = result['matches']
            for m in api_matches:
                match_id = m['match_id']
                match_seq_num = m['match_seq_num']

                # Conditions:
                match_lobby_type = m['lobby_type']
                try:
                    lobby_condition = match_lobby_type in lobby_type
                except TypeError:
                    lobby_condition = match_lobby_type == lobby_type
                match_game_mode = m['game_mode']
                try:
                    mode_condition = match_game_mode in game_mode
                except TypeError:
                    mode_condition = match_game_mode == game_mode
                conditions = (lobby_condition and mode_condition and start_match_id <= match_id <= end_match_id and
                              m['human_players'] == human_players and match_id not in match_id_set)

                if conditions:
                    # Check for leavers and create lists of hero picks for each team.
                    picks_radiant = []
                    picks_dire = []
                    for p in m['players']:
                        try:
                            if p['leaver_status'] not in no_abandon_leaver_status:
                                leavers = True
                                break
                        except KeyError:  # Bots do not have key 'leaver_status'.
                            continue
                        player_slot = bin(p['player_slot'])[2:].zfill(8)  # int to 8-bit binary string.
                        player_dire = int(player_slot[0])  # 0 is Radiant and 1 is Dire.
                        hero_id = p['hero_id']
                        if player_dire:
                            picks_dire.append(hero_id)
                        else:
                            picks_radiant.append(hero_id)
                    else:
                        leavers = False
                    picks_radiant.sort()
                    picks_dire.sort()

                    if not leavers:
                        match = {'match_id': match_id, 'match_seq_num': match_seq_num, 'radiant_win': m['radiant_win'],
                                 'game_mode': match_game_mode, 'lobby_type': match_lobby_type,
                                 'picks_radiant': picks_radiant, 'picks_dire': picks_dire}
                        new_matches.append(match)
                        new_matches_fetched += 1

            # Check if we are in the final loop.
            seq_num = 1 + api_matches[-1]['match_seq_num']
            final_loop = len(api_matches) < matches_requested or seq_num >= end_search_seq_num

            # Write database to file when enough matches have been fetched.
            if new_matches_fetched >= 1000 or final_loop:
                try:
                    with open(filename) as data:
                        construct = json.load(data)
                except FileNotFoundError:
                    construct = {'data_size': 0, 'matches': []}
                construct['data_size'] += new_matches_fetched
                num_matches_fetched += new_matches_fetched
                new_matches_fetched = 0
                construct['matches'].extend(new_matches)
                new_matches = []
                write_json_data(filename, construct)

            # Stop gathering data if we are in the final loop.
            if final_loop:
                break

            # Print completion details about data fetched so far.
            completion = 100 * (seq_num - search_start_seq_num) / (end_search_seq_num - search_start_seq_num)
            print('Progress: {:6.6}% (sequence number {:>11})'.format(str(completion), seq_num))
        else:
            print('Sequence number {} statusDetail: {}'.format(seq_num, result['statusDetail']))
            seq_num += 1

    print('Fetched {} new matches.'.format(num_matches_fetched))
    print('Total size is {} matches.'.format(data_size + num_matches_fetched))


if __name__ == '__main__':
    fn = config.MATCH_DATA_FILE
    mode = config.game_mode
    lobby = config.lobby_type
    players = config.human_players
    start_id = config.start_match_id
    end_id = config.end_match_id
    fetch_matches(fn, mode, lobby, players, start_id, end_id)
