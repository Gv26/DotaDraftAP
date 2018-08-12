import json

import numpy as np

import config


def hero_count():
    with open(config.HERO_DATA_FILE) as hero_file:
        count = json.load(hero_file)['count']
    return count


def one_hot_matrix(num_heroes):
    with open(config.HERO_DATA_FILE) as hero_file:
        hero_list = [h['id'] for h in json.load(hero_file)['heroes']]
    max_id = max(hero_list)
    hero_matrix = np.zeros((max_id + 1, num_heroes), dtype=int)
    hot_index = 0
    for h in range(max_id + 1):
        if h in hero_list:
            hero_matrix[h, hot_index] = 1
            hot_index += 1
    return hero_matrix


def picks_vector(radiant, dire, hero_matrix=None):
    num_heroes = hero_count()
    if hero_matrix is None:
        hero_matrix = one_hot_matrix(num_heroes)
    vector = np.zeros(num_heroes, dtype=int)
    for p in radiant:
        vector += hero_matrix[p]
    for p in dire:
        vector -= hero_matrix[p]
    return vector


def load_data(filename):
    with open(filename) as data_file:
        database = json.load(data_file)
    picks_radiant = database['picks_radiant']
    picks_dire = database['picks_dire']
    labels = np.array(database['radiant_win']).astype(int)
    num_matches = len(labels)
    num_heroes = hero_count()
    drafts = np.empty((num_matches, num_heroes), dtype=int)
    hero_matrix = one_hot_matrix(num_heroes)
    for m in range(num_matches):
        radiant = picks_radiant[m]
        dire = picks_dire[m]
        drafts[m] = picks_vector(radiant, dire, hero_matrix=hero_matrix)
    return drafts, labels
