Changelog
Version 2.7.1
Date: 2024-12-21

## Removed View:
- Removed the IgnoredNewsChannelsView from the bottom of the file.
## Added Missing Import:
- Added the missing import for the actual view used in the cog.
## Patch Notes:
This update removes an view from the bottom of the file and adds the missing import for the actual view used in the AutoPublisher cog.
________________________________________________________
Changelog
Version 2.7.0
Date: 2024-12-21

## Reverted from SQL to In-Memory Cache:
- Reverted the use of SQLite for storing published counts and reset times due to issues with proper functionality and persistence.
- Implemented an in-memory cache to store published counts and reset times, ensuring data is saved to JSON files for persistence across bot restarts.
## Improved Scheduler Setup:
- Updated the AsyncIOScheduler setup to ensure weekly, monthly, and yearly reset jobs are correctly scheduled.
- Weekly reset is now scheduled for every Sunday at midnight (UTC)
- Monthly reset is scheduled for the first day of each month at midnight (UTC)
- Yearly reset is scheduled for January 1st at midnight (UTC)
## Enhanced Reset Count Function:
- Added logging to the reset_count function to confirm when counts are reset.
- Ensured the last_count_time is updated whenever counts are reset.
- Updated get_next_reset_timestamp Function:
- Ensured the function respects the reset time and calculates the next reset timestamps correctly.
- Added parameters for hour and minute to specify the exact reset time.
## Improved Stats Command:
- Enhanced the stats command to display the next reset timestamps for weekly, monthly, and yearly resets.
- Added a check to ensure last_count_time is a valid string before converting it to a datetime object.
## Reason for Reverting from SQL:
- The use of SQLite for storing published counts and reset times did not work properly, leading to issues with data persistence and functionality.
- Switching to an in-memory cache with JSON file storage ensures better reliability and persistence across bot restarts.
## Patch Notes:
This update improves the reliability and functionality of the AutoPublisher cog by reverting from SQLite to an in-memory cache with JSON file storage. The scheduler setup has been enhanced to ensure reset jobs are correctly scheduled, and the stats command now provides accurate reset timestamps. These changes address issues with data persistence and ensure the cog operates smoothly.
