import requests
import pandas as pd
import geopandas as gpd
from thefuzz import process
from sqlalchemy import create_engine, text, inspect
#import pydeck as pdk
import json
import warnings

import plotly.graph_objects as go
import matplotlib.pyplot as plt
from zipfile import ZipFile
import io
import datetime

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
from qtrees.fisbroker import get_trees
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors

engine = create_engine(
    f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
)

with engine.connect() as con:
    train_data = pd.read_sql('select * from api.training_data', con)
    test_data = pd.read_sql('select * from api.test_data', con)

#train_data = train_data.dropna()

data = []
for sensor_type in [1, 2, 3]:
    for tree in train_trees.index.unique():
        tmp =  train_data.loc[(train_data.tree_id == tree) & (train_data.sensor_type == sensor_type)]
        tmp = tmp.sort_values("timestamp")
        tmp["value_lag"] = tmp["value"].shift()
        data.append(tmp)
train_data = pd.concat(data)

test_trees = test_data[["id", "winter", "spring", "summer", "fall", "gattung_deutsch", "standalter"]].set_index("id")
test_trees.standalter = (test_trees.standalter-test_trees.standalter.min())/(test_trees.standalter.max()-test_trees.standalter.min())
enc = OneHotEncoder(sparse=False)
tree_dummies = pd.DataFrame(enc.fit_transform(test_trees[["gattung_deutsch"]]), index=test_trees.index)
test_trees = pd.concat([test_trees[["winter", "spring", "summer", "fall", "standalter"]], tree_dummies], axis=1)

train_trees = train_data[["tree_id", "winter", "spring", "summer", "fall", "gattung_deutsch", "standalter"]].drop_duplicates().set_index("tree_id")
train_trees.standalter = (train_trees.standalter-train_trees.standalter.min())/(train_trees.standalter.max()-train_trees.standalter.min())
tree_dummies = pd.DataFrame(enc.transform(train_trees[["gattung_deutsch"]]), index=train_trees.index)
train_trees = pd.concat([train_trees[["winter", "spring", "summer", "fall", "standalter"]], tree_dummies], axis=1)

train_trees.shape, test_trees.shape

neigh = NearestNeighbors(n_neighbors=1)
neigh.fit(train_trees.values)

test_trees = test_trees.dropna()
neighbors = pd.DataFrame(neigh.kneighbors(test_trees.values,return_distance=False), index=test_trees.index, columns=["neighbor"])

IDX_MAP = dict(zip(range(len(train_trees.index)), train_trees.index))
neighbors.neighbor.map(IDX_MAP)


test = []
for idx, row in test_data.iterrows():
    for sensor_type in [1,2,3]:
        print(row.append(pd.Series((1, 2), index=["sensor_type", "value_lag"])))
    break


train_data[train_data.timestamp.dt.date==datetime.date(2022, 11, 20)]