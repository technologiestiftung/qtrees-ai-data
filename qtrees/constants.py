FORECAST_FEATURES = ["shading_winter", "shading_spring", "shading_summer", "shading_fall", "tree_standalter",
                     "weather_rainfall_mm_14d_sum", "weather_temp_avg_c_14d_avg", "sensor_group_median",
                     "temp_max_c", "rainfall_mm"]

NOWCAST_FEATURES = ['month', 'gattung', 'standalter', 'baumscheibe_m2', 'baumscheibe_surface',
                    'water_sga', 'water_gdk', 'shading_index', 'wind_max_ms',
                    'rainfall_mm', 'temp_avg_c', 'upm', 'ghi_sum_whm2']

HYPER_PARAMETERS = dict(max_features="sqrt", n_estimators=1000, max_depth=5, bootstrap=True)