import pandas as pd
import numpy as np
from functools import reduce
import datetime as dt
from typing import Optional
from sklearn.preprocessing import OrdinalEncoder
from qtrees.constants import PREPROCESSING_HYPERPARAMS, NOWCAST_FEATURES, FORECAST_FEATURES
from qtrees.helper import get_logger

DATA_START_DATE = "2021-06-01"
WEATHER_COLUMNS = ["wind_max_ms", "wind_avg_ms", "rainfall_mm", "temp_max_c", "temp_avg_c"]

class DataLoader:
    """
    Loads data from DB for training or forecasting

    Class which has functions for downloading either training or inference data for forecast or nowcast. Training data stays the same
    but forecast and nowcast may have different features. For inference, download_nowcast_inference_data is complete while download_forecast_inference_data
    is a minimalistic download without weather features. Due to the iterative nature of forecasting, it made more sense to keep these in the
    forecasting script

    Attributes
    ----------
    forecast : bool
        Decides wether the downloader is used for providing forecast or nowcast data
    date : datetime.date
        Day for the nowcast or initial day for forecasting if provided
    public_run : bool
        Only use publicly available data?
    batch_size:
        Download one chunk of data
    batch_num:
        Which chunk of data to download
    logger : Logger
       Gives error messages if the data download breaks


    Methods
    -------
    download_nowcast_inference_data(date: dt.date = dt.date.today() - dt.timedelta(days=1), public_run: bool = False, batch_size: Optional[int] = None, batch_num: Optional[int] = None):
        Downloads tree data without sensors and merges it with weather of the given day if there is any data for that day.
    download_forecast_inference_data(date: dt.date = dt.date.today(), public_run: bool = False, batch_size: Optional[int] = None, batch_num: Optional[int] = None):
        Downloads tree data without sensors for a given day but no weather data.
    download_training_data(self, forecast, public_run: bool = False):
        Downloads all available training data. Necessarily has sensors and no specific date. If filtering should occur, it has to happen at a later point. Note that initial
        filtering of the data is already done when writing it to the DB
    """
    
    def __init__(self, engine, logger=None):
        """
        Constructs all the necessary attributes for DataLoader.

        Parameters
        ----------
            engine : sqlalchemy.engine.Engine
                Engine for connecting to the SQL DB. Created via the sqlalchemy.create_engine function
            logger : Logger, optional
                A logger for writing error messages. If none is provided, the function creates one
        """
        self.engine = engine
        if logger is None:
            self.logger = get_logger(__name__)
        else:
            self.logger = logger

    def download_nowcast_inference_data(self, date: dt.date = dt.date.today() - dt.timedelta(days=1), public_run: bool = False, batch_size: Optional[int] = None, batch_num: Optional[int] = None):
        """
        Downloads nowcast data for inference

        For a given date this function downloads inference data, i.e. tree data for all available street trees without sensors. If provided it only downloads one batch of size
        batch_size. Use batch_num to iterate through the batches.
        Parameters
        ----------
        date : Datetime.date
            Gives the day for which inference data is downloaded if there is any
        public_run : bool
            If True, uses only publicly available data
        batch_size: int, optional
            Only download this number of trees. Use in combination with batch_num to get trees with ids from batch_size*batch_num to batch_size*(batch_num+1)
        batch_num: int, optional
            Use with batch_size to iterate through the data

        Returns
        -------
        pandas.Dataframe
            Dataframe with columns for metadata for each tree and weather data
        """
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
        """
        Downloads forecast data for inference

        For a given date this function downloads inference data, i.e. tree data for all available street trees without sensors. If provided it only downloads one batch of size
        batch_size. Use batch_num to iterate through the batches.
        Parameters
        ----------
        date : Datetime.date
            Gives the day for which inference data is downloaded if there is any
        public_run : bool
            If True, uses only publicly available data
        batch_size: int, optional
            Only download this number of trees. Use in combination with batch_num to get trees with ids from batch_size*batch_num to batch_size*(batch_num+1)
        batch_num: int, optional
            Use with batch_size to iterate through the data

        Returns
        -------
        pandas.Dataframe
            Dataframe with columns for metadata for each tree
        """
        self.forecast = True
        self.date = date
        self.public_run = public_run
        self.batch_size = batch_size
        self.batch_num = batch_num
        data = self._download_data(with_sensors=False)
        return data

    def download_training_data(self, forecast, public_run: bool = False):
        """
        Downloads all available training data

        Downloads all training data with sensors for the entire timewindow from June 2021 to today
        Parameters
        ----------
        forecast: bool
            If True, downloads training data for a forecasting model
        public_run : bool
            If True, uses only publicly available data
        
        Returns
        -------
        pandas.Dataframe
            Dataframe with columns for sensordata and metadata for each tree where there are sensors and weather data for the whole timewindow
        """
        self.forecast = forecast
        self.public_run = public_run
        self.batch_size = None
        data = self._download_data(with_sensors=True)
        data = data.merge(self._get_weather_measurements(), how="left", left_on="timestamp", right_index=True)
        return data

    def _download_data(self, with_sensors: bool = True) -> pd.DataFrame:
        """
        Downloads data and gets called by inference or training data downloader

        Download data for training or inference. If sensordata is downloaded, we ignore date.
        Otherwise we can download data for all trees for one day for inference

        Parameters
        ----------
        with_sensors: bool, optional
            If True, downloads sensordata for trees. Only used for training

        Returns
        -------
        pandas.Dataframe
        """
        self.with_sensors = with_sensors
        if self.with_sensors:
            self.date = None
        # Select all trees
        try:
            if self.batch_size is None:
                trees = pd.read_sql("SELECT id,gattung,standalter FROM public.trees WHERE street_tree = true", self.engine.connect())
            else:
                trees = pd.read_sql("SELECT id,gattung,standalter FROM public.trees WHERE street_tree = true ORDER BY id LIMIT %s OFFSET %s",
                                    self.engine.connect(), params=(self.batch_size, self.batch_size*self.batch_num))
                if trees.shape[0] == 0:
                    return None
            trees.rename(columns={"id": "tree_id"}, inplace=True)
            trees["standalter"] = pd.cut(trees["standalter"], bins=[0, 3, 10, 100], labels=["jung", "mittel", "alt"])
        except Exception as e:
            self.logger.error("Failed to read trees from DB: %s", e)
            exit(121)
        data = self._add_tree_data(trees)
        return data


    def _add_tree_data(self, subset):
        '''Adds sensor data, waterings and shading index to the metadata of each tree. Subsets the data such that only trees remain where there are sensors. Watering is split into Gieß-den-Kiez (gdk) and Grünflächenämter (sga)'''
        def get_sensors(trees):
            data = pd.read_sql(f"SELECT tree_id, type_id, timestamp, value FROM private.sensor_measurements WHERE tree_id IN {tuple(subset.tree_id.unique())}",
                               self.engine.connect())
            tree_devices = pd.read_sql(f"SELECT tree_id, site_id FROM private.tree_devices WHERE tree_id IN {tuple(subset.tree_id.unique())}",
                                       self.engine.connect())
            if not data.empty:
                data = data.assign(month=data.timestamp.dt.month)
                data = reduce(lambda left, right: pd.merge(left, right, on="tree_id",
                                                           how='left'), [data, trees, tree_devices])
            return data
        
        def get_watering(relevant_trees):
            water_sga = pd.read_sql(f"SELECT * FROM private.watering_sga WHERE tree_id IN {relevant_trees}", self.engine.connect())
            water_gdk = pd.read_sql(f"SELECT * FROM private.watering_gdk WHERE tree_id IN {relevant_trees}", self.engine.connect())
            watered_trees = pd.Series(list(set(water_sga.tree_id).union(set(water_gdk.tree_id))), name="tree_id")
            # Only get last 8 days if we don't take the sensors
            if self.date is None:
                dates = pd.date_range(DATA_START_DATE, pd.Timestamp("today"), tz="UTC")
                dates = dates[dates.month.isin(range(4, 11))]
                water = pd.DataFrame({"timestamp": dates})
            else:
                water = pd.DataFrame({"timestamp": pd.date_range(self.date - dt.timedelta(days=PREPROCESSING_HYPERPARAMS['rolling_window'] + 1), self.date, tz="UTC")})
            water = water.merge(watered_trees, "cross").assign(temp=0)
            for source, name in zip([water_sga, water_gdk], ["water_sga", "water_gdk"]):
                source["date"] = source["date"].astype('datetime64[ns, UTC]')
                source.rename(columns={"amount_liters": name, "date": "timestamp"}, inplace=True)
            water = reduce(lambda left, right: pd.merge(left, right, on=["tree_id", "timestamp"],
                                                        how='left'), [water, water_sga, water_gdk])
            water = water.drop(columns="temp")
            water = water.fillna(0)
            grpd = water.groupby(["tree_id"])
            water[["water_sga", "water_gdk"]] = grpd[["water_sga", "water_gdk"]].transform(lambda x: x.rolling(PREPROCESSING_HYPERPARAMS['rolling_window'], min_periods=1).sum())
            return water

        def get_shading_index(relevant_trees):
            monthly_shading = pd.read_sql(f"SELECT * FROM public.shading_monthly WHERE tree_id IN {relevant_trees}", self.engine.connect())
            shading_long = pd.melt(monthly_shading, id_vars="tree_id")
            month_mapping = dict((v, k) for v, k in zip(shading_long.variable.unique(), range(1, 13)))
            shading_long = shading_long.assign(month=[month_mapping[el] for el in shading_long.variable])
            shading_long.drop(columns="variable", inplace=True)
            shading_long.rename(columns={"value": "shading_index"}, inplace=True)
            return shading_long
        try:
            if self.with_sensors:
                trees = get_sensors(subset)
                if trees.empty:
                    return trees
            else:
                trees = subset
                if self.date is None:
                    dates = pd.date_range(DATA_START_DATE, pd.Timestamp("today") + pd.Timedelta(days=PREPROCESSING_HYPERPARAMS['fc_horizon'] if self.forecast else 0), tz="UTC")
                    dates = dates[dates.month.isin(range(4, 11))].to_series(name="timestamp")
                    trees = trees.merge(dates, how="cross")
                else:
                    trees = trees.assign(timestamp=self.date)
                    trees = trees.astype({"timestamp": 'datetime64[ns, UTC]'})
                trees = trees.assign(month=trees.timestamp.dt.month)
            relevant_trees = tuple(trees.tree_id.unique())
            if not self.public_run:
                trees_private = pd.read_sql("SELECT tree_id, baumscheibe_m2, baumscheibe_surface FROM private.trees_private", self.engine.connect())
                trees_private["baumscheibe_m2"] = pd.cut(trees_private["baumscheibe_m2"], bins=[0, 5, 100], labels=["klein", "groß"])
                trees = trees.merge(trees_private, how="left", on="tree_id")
                if not self.forecast:
                    water = get_watering(relevant_trees)
                    trees = trees.merge(water, how="left", on=["tree_id", "timestamp"])
            shading = get_shading_index(relevant_trees)
            trees = trees.merge(shading, how="left", on=["tree_id", "month"])
            return trees
        except Exception as e:
            self.logger.error("Failed to get shading_index, waterings or sensordata from DB: %s", e)
            exit(121)

    def _get_weather_measurements(self):
        '''Used internally to add weather data to the dataframe. Interpolates gaps in the weather data and calculates rolling averages. Uses different data sources for public and private runs.'''
        try:
            if self.public_run:  # If public run, we only take the public.weather file
                weather_station = pd.read_sql_table("weather", schema="public", index_col="date",
                                                    con=self.engine.connect(), columns=WEATHER_COLUMNS)
            else:  # For private runs we take the solar irradiance in addition to other weather data
                if self.forecast: # For forecast we use solar anywhere data as this is the only one with available weather predictions
                    weather_station = pd.read_sql_table("weather_tile_measurement", schema="private", con=self.engine.connect(),
                                                        index_col="date", columns=['tile_id']+WEATHER_COLUMNS+["ghi_sum_whm2"])
                    weather_station = weather_station.groupby(level=0).mean().drop(columns="tile_id")
                else:  # For nowcast we use 
                    weather_station = pd.read_sql_table("weather", schema="public", con=self.engine.connect(),
                                                        index_col="date", columns=WEATHER_COLUMNS)
                    weather_solar = pd.read_sql_table("weather_tile_measurement", con=self.engine.connect(), schema="private",
                                                      columns=["tile_id", "ghi_sum_whm2"], index_col="date")
                    weather_solar = weather_solar.groupby(level=0).mean().drop(columns="tile_id")
                    weather_station = weather_station.merge(weather_solar, how="left", left_index=True, right_index=True)

            weather_station.index = weather_station.index.tz_localize("UTC")
            weather_station.interpolate(limit=PREPROCESSING_HYPERPARAMS['rolling_window'])
            weather_station["rainfall_mm"] = weather_station["rainfall_mm"].rolling(window=PREPROCESSING_HYPERPARAMS['rolling_window'], min_periods=1).sum()
            for col in [x for x in weather_station.columns if x != "rainfall_mm"]:
                weather_station[col] = weather_station[col].rolling(window=PREPROCESSING_HYPERPARAMS['rolling_window'], min_periods=1).mean()
            col_names = [x for x in WEATHER_COLUMNS+["ghi_sum_whm2"] if x in weather_station.columns]
            weather_station.columns = col_names
            return weather_station

        except Exception as e:
            self.logger.error("Failed to get weather data from DB: %s", e)
            exit(121)

class PreprocessorNowcast:
    """
    Preprocesses data for nowcast training and inference.

    Class which prepares training or inference data for being used in an sklearn.model. This class handles renaming columns, ordinal encoding of categorical features and filling gaps in less important features

    Attributes
    ----------
    weather_features : list of strings
        All weather features which we want to keep from the data. Not every feature mentioned here needs to be present in the dataframe
    cat_features : list of strings
        All categorical features. For these the preprocessor will do ordinal encoding. Not every feature mentioned here needs to be present in the dataframe
    num_features : list of strings
        All numerical features that we want to keep from the data.
    ordinal_encoder:
        Sklearn.preprocessing.OrdinalEncoder object for ordinal encoding of the categorical features

    Methods
    -------
    fit(X, y=None):
        Fits the Preprocessor to some training data. This depends on columns and sets the numerical values for each category.
    transform_train(X, y=None):
        Fills NAs of less important columns so we dont lose this data. Then transforms categorical features and drops columns where we have no sensor data.
    transform_inference(X, y=None):
        Fills NAs of less important columns so we dont lose this data. Then transforms categorical features. Does not drop NAs
    """
    def __init__(self,
                 weather_features=["wind_max_ms", "wind_avg_ms", "rainfall_mm", "temp_max_c", "temp_avg_c", "ghi_sum_whm2", "upm"]):
        self.weather_features = weather_features
        self.cat_features = ['month', 'gattung', 'standalter', 'baumscheibe_m2', 'baumscheibe_surface']
        self.num_features = ['value', 'water_gdk', 'water_sga', 'shading_index', 'mean_yesterday', 'site_id']
        self.ordinal_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)

    def fit(self, X, y=None):
        '''Creates the mean_yesterday column, which is a grouped mean by day and sensor_depth, used for inference. Fits the ordinal encoder so it can encode
        categorical features during transformation.'''
        self.cat_columns = list(X.columns[X.columns.isin(self.cat_features)])
        self.num_columns = list(X.columns[X.columns.isin(self.num_features+self.weather_features)])
        self.mean_yesterday = X.groupby(["timestamp", "type_id"])["value"].mean().shift(1).rename("mean_yesterday")
        self.index_cols = ["type_id", "tree_id", "timestamp"]
        self.ordinal_encoder = self.ordinal_encoder.fit(X[self.cat_columns])

    def transform_train(self, X, y=None):
        '''Transforms some columns from numeric to categorical features by binning. Then transforms categorical features ordinally.
        Drops columns without sensors, renames columns and matches the index for further use.'''
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
        '''Transforms some columns from numeric to categorical features by binning. Then transforms categorical features ordinally.
        Matches the index for further use.'''
        all_cols = self.index_cols + self.cat_columns + self.num_columns
        all_cols = [x for x in all_cols if x not in ["site_id", "value", "type_id"]]
        X = X[all_cols]
        X = self._transform_features(X)
        X.loc[:, self.cat_columns] = self.ordinal_encoder.transform(X[self.cat_columns])
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


class PreprocessorForecast:
    """
    Preprocesses data for forecast training and inference.

    Class which prepares training or inference data for being used in an sklearn.model. This class handles renaming columns, ordinal encoding of categorical features and filling gaps in less important features

    Attributes
    ----------
    weather_features : list of strings
        All weather features which we want to keep from the data. Not every feature mentioned here needs to be present in the dataframe
    cat_features : list of strings
        All categorical features. For these the preprocessor will do ordinal encoding. Not every feature mentioned here needs to be present in the dataframe
    num_features : list of strings
        All numerical features that we want to keep from the data.
    ordinal_encoder:
        Sklearn.preprocessing.OrdinalEncoder object for ordinal encoding of the categorical features

    Methods
    -------
    fit(X, y=None):
        Fits the Preprocessor to some training data. This depends on columns and sets the numerical values for each category.
    transform_train(X, y=None):
        Adds autoregressive features to the data. Then transforms categorical features and drops columns where we have no sensor data. Fills NAs of less important columns so we dont lose this data. 
    transform_inference(X, y=None):
        Fills NAs of less important columns so we dont lose this data. Then transforms categorical features. Does not drop NAs. Autoregressive features are generated iteratively during inference.
    """
    def __init__(self,
                 weather_features=["wind_max_ms", "wind_avg_ms", "rainfall_mm", "temp_max_c", "temp_avg_c", "ghi_sum_whm2", "upm"]):
        self.weather_features = weather_features
        self.cat_features = ['month', 'gattung', 'standalter', 'baumscheibe_m2', 'baumscheibe_surface']
        self.num_features = ['value', 'shading_index', 'mean_yesterday', 'site_id']
        self.ordinal_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)

    def fit(self, X, y=None):
        '''Creates the mean_yesterday column, which is a grouped mean by day and sensor_depth, used for inference. Fits the ordinal encoder so it can encode
        categorical features during transformation.'''
        self.cat_columns = list(X.columns[X.columns.isin(self.cat_features)])
        self.num_columns = list(X.columns[X.columns.isin(self.num_features+self.weather_features)])
        self.mean_yesterday = X.groupby(["timestamp", "type_id"])["value"].mean().shift(1).rename("mean_yesterday")
        self.index_cols = ["type_id", "tree_id", "timestamp"]
        self.ordinal_encoder = self.ordinal_encoder.fit(X[self.cat_columns])

    def transform_train(self, X, y=None):
        '''Transforms some columns from numeric to categorical features by binning. Adds autoregressive features to the data.
        Then transforms categorical features ordinally. Drops columns without sensors, renames columns and matches the index for further use.'''
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
        '''Transforms some columns from numeric to categorical features by binning. Then transforms categorical features ordinally.
        Matches the index for further use.'''
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
        for i in range(1, PREPROCESSING_HYPERPARAMS['autoreg_lag']+1):
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
                    temp = temp[temp.index.month.isin(range(4, 11))]
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
