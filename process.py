"""Process raw match data in preparation for training."""
import json

import config


def write_json_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)


def match_id_condition(match_id, start, end):
    if start is None and end is None:
        return True
    elif start is not None and end is not None:
        return start <= match_id <= end
    elif start is not None and end is None:
        return match_id >= start
    else:
        return match_id <= end


def process_data(input_file, output_file, start_match_id, end_match_id):
    """Convert raw data into format suitable for training and write this data to file.

    Overwrite existing training data file.
    """
    try:
        with open(input_file) as data_file:
            in_data = json.load(data_file)
    except FileNotFoundError:
        print('{} not found.'.format(input_file))
        return
    radiant = []
    dire = []
    labels = []
    match_ids = []
    for m in in_data['matches']:
        match_id = m['match_id']
        if match_id_condition(match_id, start_match_id, end_match_id):
            picks_radiant = m['picks_radiant']
            picks_dire = m['picks_dire']
            radiant_win = m['radiant_win']
            radiant.append(picks_radiant)
            dire.append(picks_dire)
            labels.append(radiant_win)
            match_ids.append(match_id)
    processed = {'picks_radiant': radiant, 'picks_dire': dire,  'radiant_win': labels, 'match_ids': match_ids}
    write_json_data(output_file, processed)


if __name__ == '__main__':
    in_file = config.MATCH_DATA_FILE
    out_file = config.TRAINING_DATA_FILE
    start_id = config.training_start_match_id
    end_id = config.training_end_match_id
    process_data(in_file, out_file, start_id, end_id)
