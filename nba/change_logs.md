**Changelog**
**Version 3.1.0**
**Date: 2024-12-21**
## Improvements:
- Final Game Data Reset: 
    - Reworked the final part of the code to ensure that all game data is properly reset to zero at the end of each game session. This change ensures a clean slate for each new game, preventing carry-over issues from previous sessions.
- Cache Removal: 
    - Removed the `final_game_cache`. This removal allows for continuous updates to the game data without interference from cached information, enhancing performance and ensuring that each game starts with the latest game state.
________________________________________________________________

**Changelog**
**Version 3.0.0**
**Date: 2024-12-21**
## Reverted from SQL to In-Memory Cache with orjson:
- Reverted the use of SQLite for storing game data due to issues with proper data removal after games and unnecessary spamming.
- Implemented an in-memory cache using orjson to store game data, ensuring data is saved to JSON files for persistence across bot restarts.
## Improved Game Data Handling:
- Added logic to mark games as final and prevent further updates once a game is completed.
- Ensured that game data is correctly updated and saved to JSON files.
## Enhanced Periodic Check Function:
- Updated the periodic_check function to use the in-memory cache and orjson for game data storage.
- Added checks to prevent processing of already completed games.
## Updated Cache Loading and Saving:
- Implemented load_cache and save_cache methods to handle loading and saving of game data using orjson.
- Ensured that the cache is correctly initialized and updated.
## Reason for Reverting from SQL:
- The use of SQLite for storing game data did not work properly, leading to issues with data removal after games and unnecessary spamming.
- Switching to an in-memory cache with orjson ensures better reliability and persistence across bot restarts.
## Patch Notes:
This update improves the reliability and functionality of the NBA cog by reverting from SQLite to an in-memory cache with orjson for game data storage. The periodic_check function has been enhanced to prevent processing of already completed games, and the cache loading and saving mechanisms have been updated to ensure data persistence. These changes address issues with data removal and spamming, ensuring the cog operates smoothly.
