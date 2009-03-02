DROP TABLE IF EXISTS zvv_apikey;
CREATE TABLE `zvv_apikey` (
    apikey_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    apikey_key VARCHAR(32) NOT NULL DEFAULT '',
    apikey_domain VARCHAR(255) NOT NULL DEFAULT '',

    PRIMARY KEY (apikey_id)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

DROP TABLE IF EXISTS zvv_station;
CREATE TABLE zvv_station (
    station_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    station_sbbid INT UNSIGNED NOT NULL DEFAULT 0,
    station_lat DECIMAL(9,6) NOT NULL DEFAULT 0.000000,
    station_lon DECIMAL(9,6) NOT NULL DEFAULT 0.000000,
    station_name VARCHAR(255) NOT NULL DEFAULT '',
    station_type VARCHAR(128) NOT NULL DEFAULT '',
    
    PRIMARY KEY (station_id),
    UNIQUE(station_sbbid),
    INDEX(station_lat),
    INDEX(station_lon)
) CHARACTER SET utf8 COLLATE utf8_general_ci;

