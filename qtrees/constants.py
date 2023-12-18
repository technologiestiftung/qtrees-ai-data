FORECAST_FEATURES = ['month', 'gattung', 'standalter', 'shading_index',
                     "wind_max_ms", "temp_avg_c", "rainfall_mm", "ghi_sum_whm2"]

NOWCAST_FEATURES = ['month', 'gattung', 'standalter', 'water_sga', 'water_gdk', 'shading_index', 'wind_max_ms',
                    'rainfall_mm', 'temp_avg_c', 'upm', 'ghi_sum_whm2']

HYPER_PARAMETERS_NC = dict(max_features="sqrt", n_estimators=1000, max_depth=5, bootstrap=True)

HYPER_PARAMETERS_FC = dict(max_features="sqrt", n_estimators=1000, max_depth=10, bootstrap=True)

PREPROCESSING_HYPERPARAMS = dict(rolling_window=7, fc_horizon=14, autoreg_lag=3, tile_id=2)
