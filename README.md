# DotaDraftAP
Machine learning application for drafting All Pick matches in Dota 2.

## Getting started

You can configure DotaDraft by editing the parameters in `config.py`.

### Getting training data
In order to fetch new match data for training, `STEAM_API_KEY` must be set to your [Steam Web API key](https://steamcommunity.com/dev/apikey) in `config.py`.

To make sure the hero information is up-to-date, run `python heroes.py`.

Run `python matches.py` and new matches will begin to be fetched (this is very slow) and output to file as JSON.

The data is formatted as
```json
{
    "data_size": 1,
    "matches": [
        {
            "match_id": 0,
            "match_seq_num": 0,
            "radiant_win": true,
            "game_mode": 0,
            "lobby_type": 0,
            "picks_radiant": [1, 2, 3, 4, 5],
            "picks_dire": [6, 7, 8, 9, 10]
        }
    ]
}
```

Run `python process.py` to generate a JSON file containing data converted for use as training data.
