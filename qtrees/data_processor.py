import pandas as pd
import numpy as np
from functools import reduce
import datetime as dt
from typing import Union, Optional
from sklearn.preprocessing import OrdinalEncoder

ROLLING_WINDOW = 7
FORECAST_HORIZON = 14
AUTOREGRESSIVE_LAG = 3

class Data_loader:
    def __init__(self, engine):
        self.engine = engine

    def download_nowcast_inference_data(self, date: dt.date = dt.date.today() - dt.timedelta(days=1), public_run: bool = False, batch_size: Optional[int] = None, batch_num: Optional[int] = None):
        # TODO: Figure out a way to download data in batches s.t. we do not have to hold that much info in memory
        self.forecast = False
        self.date = date
        self.public_run = public_run
        self.batch_size = batch_size
        self.batch_num = batch_num
        data = self._download_data(with_sensors=False)
        if data is not None:
            data = data.merge(self._get_weather_measurements(), how="left", left_on="timestamp", right_index=True)
        return data
    
    def download_forecast_inference_data(self, date: dt.date = dt.date.today(), public_run: bool = False, batch_size: Optional[int] = None, batch_num: Optional[int] = None):
        self.forecast = True
        self.date = date
        self.public_run = public_run
        self.batch_size = batch_size
        self.batch_num = batch_num
        data = self._download_data(with_sensors=False)
        return data
    
    def download_nowcast_training_data(self, public_run: bool = False):
        self.forecast = False
        self.public_run = public_run
        self.batch_size = None
        data = self._download_data(with_sensors=True)
        data = data.merge(self._get_weather_measurements(), how="left", left_on="timestamp", right_index=True)
        return data
    
    def download_forecast_training_data(self, public_run: bool = False):
        self.forecast = True
        self.public_run = public_run
        self.batch_size = None
        data = self._download_data(with_sensors=True)
        data = data.merge(self._get_weather_measurements(), how="left", left_on="timestamp", right_index=True)
        return data

    def _download_data(self, with_sensors: bool = True) -> pd.DataFrame:
        '''Download data for training or inference. If sensordata is downloaded, we ignore tree_subset and date.
        Otherwise we can download data for all trees for one day for inference. For evaluation we need to split training data into train and eval, e.g. via Crossvalidation'''
        self.with_sensors = with_sensors
        if self.with_sensors:
            self.date = None
        # Select all trees
        if self.batch_size is None:
            trees = pd.read_sql("SELECT id,gattung,standalter FROM public.trees WHERE street_tree = true", self.engine.connect())
        else:
            trees = pd.read_sql(f"SELECT id,gattung,standalter FROM public.trees WHERE street_tree = true ORDER BY id LIMIT {self.batch_size} OFFSET {self.batch_size*self.batch_num}", self.engine.connect())
            if trees.shape[0] == 0:
                return None
        trees.rename(columns={"id": "tree_id"}, inplace=True)
        trees["standalter"] = pd.cut(trees["standalter"], bins=[0, 3, 10, 100], labels=["jung", "mittel", "alt"])
        data = self._add_tree_data(trees)
        return data

    def _add_tree_data(self, subset):
        def get_sensors(trees):
            data = pd.read_sql(f"SELECT tree_id, type_id, timestamp, value FROM private.sensor_measurements WHERE tree_id in {tuple(subset.tree_id.unique())}", self.engine.connect())
            tree_devices = pd.read_sql(f"SELECT tree_id, site_id FROM private.tree_devices WHERE tree_id in {tuple(subset.tree_id.unique())}", self.engine.connect())
            if not data.empty:
                data = data.assign(month=data.timestamp.dt.month)
                data = reduce(lambda left, right: pd.merge(left, right, on="tree_id",
                                                           how='left'), [data, trees, tree_devices])
            return data
        
        def get_watering(relevant_trees):
            water_sga = pd.read_sql(f"SELECT * from private.watering_sga WHERE tree_id in {relevant_trees}", self.engine.connect())
            water_gdk = pd.read_sql(f"SELECT * FROM private.watering_gdk WHERE tree_id in {relevant_trees}", self.engine.connect())
            watered_trees = pd.Series(list(set(water_sga.tree_id).union(set(water_gdk.tree_id))), name="tree_id")
            # Only get last 8 days if we don't take the sensors
            if self.date is None:
                dates = pd.date_range("2021-06-01", pd.Timestamp("today"), tz="UTC")
                dates = dates[dates.month.isin(range(4,11))]
                water = pd.DataFrame({"timestamp": dates})
            else:
                water = pd.DataFrame({"timestamp": pd.date_range(self.date - dt.timedelta(days=ROLLING_WINDOW + 1), self.date, tz="UTC")})
            water = water.merge(watered_trees, "cross").assign(temp=0)
            for source, name in zip([water_sga, water_gdk], ["water_sga", "water_gdk"]):
                source["date"] = source["date"].astype('datetime64[ns, UTC]')
                source.rename(columns={"amount_liters": name, "date": "timestamp"}, inplace=True)
            water = reduce(lambda left, right: pd.merge(left, right, on=["tree_id", "timestamp"],
                                                        how='left'), [water, water_sga, water_gdk])
            water = water.drop(columns="temp")
            water = water.fillna(0)
            water = water.groupby(["tree_id", "timestamp"]).rolling(window=ROLLING_WINDOW, min_periods=1).sum()
            return water

        def get_shading_index(relevant_trees):
            monthly_shading = pd.read_sql(f"SELECT * FROM public.shading_monthly WHERE tree_id in {relevant_trees}", self.engine.connect())
            shading_long = pd.melt(monthly_shading, id_vars="tree_id")
            month_mapping = dict((v, k) for v, k in zip(shading_long.variable.unique(), range(1, 13)))
            shading_long = shading_long.assign(month=[month_mapping[el] for el in shading_long.variable])
            shading_long.drop(columns="variable", inplace=True)
            shading_long.rename(columns={"value": "shading_index"}, inplace=True)
            return shading_long

        if self.with_sensors:
            trees = get_sensors(subset)
            if trees.empty:
                return trees
        else:
            trees = subset
            if self.date is None:
                dates = pd.date_range("2021-06-01", pd.Timestamp("today") + pd.Timedelta(days=FORECAST_HORIZON if self.forecast else 0), tz="UTC")
                dates = dates[dates.month.isin(range(4, 11))].to_series(name="timestamp")
                trees = trees.merge(dates, how="cross")
            else:
                trees = trees.assign(timestamp=self.date)
                trees = trees.astype({"timestamp": 'datetime64[ns, UTC]'})
            trees = trees.assign(month=trees.timestamp.dt.month)
        relevant_trees = tuple(trees.tree_id.unique())
        if not self.public_run:
            trees_private = pd.read_sql("SELECT tree_id,baumscheibe_m2,baumscheibe_surface FROM private.trees_private", self.engine.connect())
            trees_private["baumscheibe_m2"] = pd.cut(trees_private["baumscheibe_m2"], bins=[0, 5, 100], labels=["klein", "groß"])
            trees = trees.merge(trees_private, how="left", on="tree_id")
            if not self.forecast:
                water = get_watering(relevant_trees)
                trees = trees.merge(water, how="left", on=["tree_id", "timestamp"])
        shading = get_shading_index(relevant_trees)
        trees = trees.merge(shading, how="left", on=["tree_id", "month"])
        return trees

    def _get_weather_measurements(self):
        '''Get station data and solar if not public run and merge them. Generate weekly avg or sum depending on column.'''
        if self.forecast and not self.public_run:
            weather_station = pd.read_sql("SELECT tile_id, date, wind_max_ms, wind_avg_ms, temp_max_c, temp_avg_c, rainfall_mm FROM private.weather_tile_measurement", con=self.engine.connect())
            weather_station = weather_station.groupby("date").mean().drop(columns="tile_id").reset_index()
        else:
            weather_station = pd.read_sql("SELECT date, wind_max_ms, wind_avg_ms, rainfall_mm, temp_max_c, temp_avg_c, upm FROM public.weather", con=self.engine.connect())
        weather_list = [weather_station]
        if not self.public_run:
            weather_solar = pd.read_sql("SELECT tile_id, date, ghi_sum_whm2 FROM private.weather_tile_measurement", con=self.engine.connect())
            weather_list.append(weather_solar)
        for source in weather_list:
            source["date"] = source["date"].astype('datetime64[ns, UTC]')
            source.set_index("date", inplace=True)
            source.interpolate(limit=7)
        if not self.public_run:
            weather_station = weather_station.merge(weather_solar.groupby(level=0).mean()["ghi_sum_whm2"], how="left", left_index=True, right_index=True)
        weather_station["rainfall_mm"] = weather_station["rainfall_mm"].rolling(window=ROLLING_WINDOW, min_periods=1).sum()
        for col in [x for x in weather_station.columns if x not in ["date", "rainfall_mm"]]:
            weather_station[col] = weather_station[col].rolling(window=ROLLING_WINDOW, min_periods=1).mean()
        return weather_station

    def _get_weather_forecast(self):
        '''For forecast training and inference we take the weather forecast from solar anywhere instead of the station weather. However we do not have upm for the forecast'''
        weather_solar = pd.read_sql(f"SELECT tile_id, date, ghi_sum_whm2, wind_max_ms, wind_avg_ms, temp_max_c, temp_avg_c, rainfall_mm FROM private.weather_tile_forecast WHERE DATE(created_at) = '{self.date.strftime('%Y-%m-%d')}';", con=self.engine.connect())
        weather_solar["date"] = weather_solar["date"].astype('datetime64[ns, UTC]')
        weather_solar = weather_solar.groupby(["date"]).mean()
        weather_solar["rainfall_mm"] = weather_solar["rainfall_mm"].rolling(window=ROLLING_WINDOW, min_periods=1).sum()
        for col in [x for x in weather_solar.columns if x not in ["date", "rainfall_mm"]]:
            weather_solar[col] = weather_solar[col].rolling(window=ROLLING_WINDOW, min_periods=1).mean()
        return weather_solar.drop(columns="tile_id")


class Preprocessor_Nowcast:
    def __init__(self,
                 weather_features=["wind_max_ms", "wind_avg_ms", "rainfall_mm", "temp_max_c", "temp_avg_c", "ghi_sum_whm2", "upm"]):
        self.weather_features = weather_features
        self.cat_features = ['month', 'gattung', 'standalter', 'baumscheibe_m2', 'baumscheibe_surface']
        self.num_features = ['value', 'water_gdk', 'water_sga', 'shading_index', 'mean_yesterday', 'site_id']
        self.ordinal_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)

    def fit(self, X, y=None):
        self.cat_columns = list(X.columns[X.columns.isin(self.cat_features)])
        self.num_columns = list(X.columns[X.columns.isin(self.num_features+self.weather_features)])
        self.mean_yesterday = X.groupby(["timestamp", "type_id"])["value"].mean().shift(1).rename("mean_yesterday")
        self.index_cols = ["type_id", "tree_id", "timestamp"]
        self.ordinal_encoder = self.ordinal_encoder.fit(X[self.cat_columns])

    def transform_train(self, X, y=None):
        all_cols = self.index_cols + self.cat_columns + self.num_columns
        X = X[all_cols]
        X = self._transform_features(X)
        X = self._fill_gaps(X)
        X[self.cat_columns] = self.ordinal_encoder.transform(X[self.cat_columns])
        X = X[X["value"].notna()]
        X.set_index(["tree_id", "timestamp"], inplace=True)
        X = X.rename(columns={"value": "target"})
        return X

    def transform_inference(self, X):
        all_cols = self.index_cols + self.cat_columns + self.num_columns
        all_cols = [x for x in all_cols if x not in ["site_id", "value", "type_id"]]
        X = X[all_cols]
        X = self._transform_features(X)
        X.loc[:,self.cat_columns] = self.ordinal_encoder.transform(X[self.cat_columns])
        # X = X.merge(self.mean_yesterday, left_on=["timestamp", "type_id"], right_index=True)
        return X.set_index(["tree_id", "timestamp"])
    
    def _fill_gaps(self, X):
        resampled_data = None
        X.set_index(["type_id", "tree_id", "timestamp"], inplace=True)
        for depth in [1, 2, 3]:
            for idx in X.index.get_level_values(1).unique():
                try:
                    temp = X.loc[depth, idx, :].resample("D").ffill(limit=7)
                    temp = temp[temp.index.month.isin(range(4, 10))]
                    temp["type_id"] = depth
                    temp["tree_id"] = idx
                except AttributeError:
                    temp = None
                if resampled_data is None:
                    resampled_data = temp
                else:
                    resampled_data = pd.concat([resampled_data, temp])
        X_filled = resampled_data.reset_index()
        return X_filled

    def _transform_features(self, X):
        for col in ["baumscheibe_m2", "baumscheibe_surface", "water_sga", "water_gdk"]:
            if col in X:
                X.loc[:, col] = X[col].fillna(X[col].mode()[0])
        if "value" in X.columns:
            temp = X.groupby(["timestamp", "type_id"])["value"].mean().groupby("type_id").shift(1).rename("mean_yesterday")
            X = X.merge(temp, left_on=["timestamp", "type_id"], right_index=True)
        return X


class Preprocessor_Forecast:
    def __init__(self,
                 weather_features=["wind_max_ms", "wind_avg_ms", "rainfall_mm", "temp_max_c", "temp_avg_c", "ghi_sum_whm2", "upm"]):
        self.weather_features = weather_features
        self.cat_features = ['month', 'gattung', 'standalter', 'baumscheibe_m2', 'baumscheibe_surface']
        self.num_features = ['value', 'shading_index', 'mean_yesterday', 'site_id']
        self.ordinal_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)

    def fit(self, X, y=None):
        self.cat_columns = list(X.columns[X.columns.isin(self.cat_features)])
        self.num_columns = list(X.columns[X.columns.isin(self.num_features+self.weather_features)])
        self.mean_yesterday = X.groupby(["timestamp", "type_id"])["value"].mean().shift(1).rename("mean_yesterday")
        self.index_cols = ["type_id", "tree_id", "timestamp"]
        self.ordinal_encoder = self.ordinal_encoder.fit(X[self.cat_columns])

    def transform_train(self, X, y=None):
        all_cols = self.index_cols + self.cat_columns + self.num_columns
        X = X[all_cols]
        X = self._transform_features(X)
        X = self._fill_gaps(X)
        X = self._add_autoregressive_features(X)
        X[self.cat_columns] = self.ordinal_encoder.transform(X[self.cat_columns])
        X = X[X["value"].notna()]
        X.set_index(["tree_id", "timestamp"], inplace=True)
        X = X.rename(columns={"value": "target"})
        return X

    def transform_inference(self, X):
        all_cols = self.index_cols + self.cat_columns + self.num_columns
        all_cols = [x for x in all_cols if x not in self.weather_features + ["site_id", "value", "type_id"]]
        X = X[all_cols]
        X = self._transform_features(X)
        X[self.cat_columns] = self.ordinal_encoder.transform(X[self.cat_columns])
        #X = X.merge(self.mean_yesterday, left_on=["timestamp", "type_id"], right_index=True)
        return X.set_index(["tree_id", "timestamp"])

    def _add_autoregressive_features(self, X):
        X.set_index(["tree_id", "type_id", "timestamp"], inplace=True)
        X.sort_index(inplace=True)
        for i in range(1, AUTOREGRESSIVE_LAG+1):
            X.insert(0, f"shift_{i}", 0)
            for tree_id in X.index.get_level_values(0).unique():
                for type_id in [1, 2, 3]:
                    try:
                        X.loc[(tree_id, type_id, slice(None)), f"shift_{i}"] = X.loc[(tree_id, type_id, slice(None)), "value"].shift(i)
                    except:
                        continue
        X.reset_index(inplace=True)
        return X

    def _fill_gaps(self, X):
        resampled_data = None
        X.set_index(["type_id", "tree_id", "timestamp"], inplace=True)
        for depth in [1, 2, 3]:
            for idx in X.index.get_level_values(1).unique():
                try:
                    temp = X.loc[depth, idx, :].resample("D").ffill(limit=7)
                    temp = temp[temp.index.month.isin(range(4, 10))]
                    temp["type_id"] = depth
                    temp["tree_id"] = idx
                except AttributeError:
                    temp = None
                if resampled_data is None:
                    resampled_data = temp
                else:
                    resampled_data = pd.concat([resampled_data, temp])
        X_filled = resampled_data.reset_index()
        return X_filled

    def _transform_features(self, X):
        for col in ["baumscheibe_m2", "baumscheibe_surface", "water_sga", "water_gdk"]:
            if col in X:
                X.loc[:, col] = X[col].fillna(X[col].mode()[0])
        if "value" in X.columns:
            temp = X.groupby(["timestamp", "type_id"])["value"].mean().groupby("type_id").shift(1).rename("mean_yesterday")
            X = X.merge(temp, left_on=["timestamp", "type_id"], right_index=True)
        return X
