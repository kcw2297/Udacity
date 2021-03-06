import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

LOG_DATA = config.get("S3", "LOG_DATA")
LOG_JSONPATH = config.get("S3", "LOG_JSONPATH")
SONG_DATA = config.get("S3","SONG_DATA")
ARN = config['IAM_ROLE']['ARN']
REGION = config['PLACE']['REGION']

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""
    CREATE TABLE IF NOT EXISTS staging_events(
    artist VARCHAR,
    auth VARCHAR,
    firstName VARCHAR,
    gender CHAR(1),
    itemINSession INTEGER,
    lastName VARCHAR,
    length FLOAT,
    level VARCHAR,
    location VARCHAR,
    method VARCHAR,
    page VARCHAR,
    registration FLOAT,
    sessionId INTEGER,
    song VARCHAR,
    status INTEGER,
    ts BIGINT,
    userAgent VARCHAR,
    userId INTEGER
    );
""")


staging_songs_table_create = ("""
    CREATE TABLE IF NOT EXISTS staging_songs(
    num_songs INTEGER,
    artist_id VARCHAR,
    artist_latitude FLOAT,
    artist_longitude FLOAT,
    artist_location VARCHAR,
    artist_name VARCHAR,
    song_id VARCHAR,
    title VARCHAR,
    duration FLOAT,
    year INTEGER
    );
""")



user_table_create = ("""
    CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER sortkey distkey,
    first_name VARCHAR,
    last_name VARCHAR,
    gender CHAR(1),
    level VARCHAR,
    PRIMARY KEY (user_id)
    );
""")

song_table_create = ("""
    CREATE TABLE IF NOT EXISTS songs(
    song_id VARCHAR sortkey,
    title VARCHAR NOT NULL,
    artist_id VARCHAR NOT NULL,
    year INTEGER,
    duration FLOAT,
    PRIMARY KEY(song_id)
    );
""")

artist_table_create = ("""
    CREATE TABLE IF NOT EXISTS artists(
    artist_id VARCHAR sortkey,
    name VARCHAR NOT NULL,
    location VARCHAR,
    latitude VARCHAR,
    longitude VARCHAR,
    PRIMARY KEY(artist_id)
    );
""")

time_table_create = ("""
    CREATE TABLE IF NOT EXISTS time(
        start_time TIMESTAMP NOT NULL sortkey,
        hour INTEGER NOT NULL,
        day INTEGER NOT NULL,
        week INTEGER NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        weekday INTEGER NOT NULL,
        PRIMARY KEY (start_time)
    );
""")

songplay_table_create = ("""
CREATE TABLE IF NOT EXISTS songplays(
    songplay_id INTEGER IDENTITY(0, 1) sortkey,
    start_time TIMESTAMP REFERENCES time(start_time),
    user_id INTEGER REFERENCES users(user_id) distkey,
    level VARCHAR,
    song_id VARCHAR REFERENCES songs(song_id),
    artist_id VARCHAR REFERENCES artists(artist_id),
    session_id INTEGER NOT NULL,
    location VARCHAR,
    user_agent VARCHAR,
    PRIMARY KEY (songplay_id)
    );
""")


# STAGING TABLES

staging_events_copy = ("""
    COPY staging_events 
    FROM {}
    iam_role {}
    region {}
    format as json {}
    timeformat as 'epochmillisecs'
    COMPUPDATE OFF;
""").format(LOG_DATA,ARN,REGION,LOG_JSONPATH)

staging_songs_copy = ("""
    COPY staging_songs
    FROM {}
    iam_role {}
    region {}
    format as json 'auto'
    COMPUPDATE OFF;
""").format(SONG_DATA,ARN,REGION)

# FINAL TABLES

songplay_table_insert = ("""
    INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
    SELECT DISTINCT TIMESTAMP 'epoch' + se.ts * interval '0.001 seconds',
        se.userId, 
        se.level, 
        ss.song_id, 
        ss.artist_id,  
        se.sessionId, 
        se.location,
        se.userAgent
    FROM staging_events se
    INNER JOIN staging_songs ss
    ON se.song = ss.title AND se.artist=ss.artist_name
    WHERE se.page = 'NextSong';
""")

user_table_insert = ("""
    INSERT INTO users (user_id, first_name, last_name, gender, level)
    SELECT DISTINCT se.userId,
        se.firstName,
        se.lastName,
        se.gender,
        se.level
    FROM staging_events se
    WHERE userId IS NOT NULL;
""")

song_table_insert = ("""
    INSERT INTO songs (song_id, title, artist_id, year, duration)
    SELECT DISTINCT ss.song_id,
        ss.title,
        ss.artist_id,
        ss.year,
        ss.duration
    FROM staging_songs ss
    WHERE ss.song_id IS NOT NULL;
""")

artist_table_insert = ("""
    INSERT INTO artists (artist_id, name, location, latitude, longitude)
    SELECT DISTINCT ss.artist_id,
    ss.artist_name,
    ss.artist_location,
    ss.artist_latitude,
    ss.artist_longitude
    FROM staging_songs ss
    WHERE ss.artist_id IS NOT NULL;
""")

time_table_insert = ("""
    INSERT INTO time (start_time, hour, day, week, month, year, weekday)
    SELECT  TIMESTAMP 'epoch' + ts/1000 * INTERVAL '1 second' AS start_time,
    EXTRACT(hour from start_time),
    EXTRACT(day from start_time),
    EXTRACT(week from start_time),
    EXTRACT(month from start_time),
    EXTRACT(year from start_time),
    EXTRACT(weekday from start_time)
    FROM staging_events se
    WHERE se.page = 'NextSong';
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, user_table_create, song_table_create, artist_table_create, time_table_create, songplay_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
