import json
from operator import itemgetter

import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.constraints import max_norm
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

import config


def hero_count():
    with open(config.HERO_DATA_FILE) as hero_file:
        count = json.load(hero_file)['count']
    return count


def hero_dicts():
    with open(config.HERO_DATA_FILE) as hero_file:
        heroes = json.load(hero_file)['heroes']
    return heroes


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


def picks_vector(radiant, dire, num_heroes, hero_matrix=None):
    if hero_matrix is None:
        hero_matrix = one_hot_matrix(num_heroes)
    vector = np.zeros(num_heroes, dtype=int)
    for p in radiant:
        vector += hero_matrix[p]
    for p in dire:
        vector -= hero_matrix[p]
    return vector


def load_data(filename, num_heroes):
    with open(filename) as data_file:
        database = json.load(data_file)
    picks_radiant = database['picks_radiant']
    picks_dire = database['picks_dire']
    labels = np.array(database['radiant_win']).astype(int)
    num_matches = len(labels)
    data = np.empty((num_matches, num_heroes), dtype=int)
    hero_matrix = one_hot_matrix(num_heroes)
    for m in range(num_matches):
        radiant = picks_radiant[m]
        dire = picks_dire[m]
        data[m] = picks_vector(radiant, dire, num_heroes, hero_matrix=hero_matrix)
    return data, labels


def split_data(data, labels, training_fraction=0.9):
    """Split data into training and testing parts."""
    training_index = round(training_fraction * (labels.shape[0]))
    train_data = data[:training_index]
    train_labels = labels[:training_index]
    test_data = data[training_index:]
    test_labels = labels[training_index:]
    return train_data, train_labels, test_data, test_labels


def build_model(num_heroes):
    model = Sequential()
    model.add(Dropout(0.2, input_shape=(num_heroes,)))
    # model.add(Dense(128, activation='relu', input_dim=num_heroes))
    model.add(Dense(128, activation='relu', kernel_constraint=max_norm(3)))
    model.add(Dropout(0.2))
    model.add(Dense(64, activation='relu', kernel_constraint=max_norm(3)))
    model.add(Dropout(0.2))
    model.add(Dense(1, activation='sigmoid'))

    adam = Adam(lr=0.01)
    model.compile(optimizer=adam, loss='binary_crossentropy', metrics=['accuracy'])
    return model


if __name__ == '__main__':
    heroes_count = hero_count()
    drafts, radiant_win = load_data(config.TRAINING_DATA_FILE, heroes_count)
    train_drafts, train_radiant_win, test_drafts, test_radiant_win = split_data(drafts, radiant_win)

    model = build_model(heroes_count)
    model.summary()
    history = model.fit(train_drafts, train_radiant_win, batch_size=65536, epochs=12, validation_split=0.1)

    # Graph training and validation loss and accuracy.
    acc = history.history['acc']
    val_acc = history.history['val_acc']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs = range(1, len(acc) + 1)
    # "bo" is for "blue dot"
    plt.plot(epochs, loss, 'rx', markersize=4, label='Training loss')
    # b is for "solid blue line"
    plt.plot(epochs, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
    plt.clf()  # clear figure
    plt.plot(epochs, acc, 'rx', markersize=4, label='Training acc')
    plt.plot(epochs, val_acc, 'b', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.show()

    # Evaluate model on test data.
    results = model.evaluate(test_drafts, test_radiant_win)
    print(results)

    heroes = hero_dicts()
    hero_map = one_hot_matrix(heroes_count)
    for h in heroes:
        test_input = np.array([picks_vector([h['id'], 22, 71, 20, 70], [37, 5, 99, 67, 82], heroes_count, hero_map)])
        h['radiant_win'] = model.predict(test_input)[0, 0]
    sorted_heroes = sorted(heroes, key=itemgetter('radiant_win'), reverse=True)
    counter = 0
    for h in sorted_heroes:
        print('{:3} {:20} {:6.6}'.format(h['id'], h['localized_name'], str(h['radiant_win'])))
        counter += 1
        if counter > 60:
            break
