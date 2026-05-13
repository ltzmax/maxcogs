# HoneyCombs

Play Honeycombs.

## [p]honeycombs (Hybrid Command)

Start a game of Honeycombs.<br/>

You need at least 2 players to start the game.<br/>
The maximum number of players is 456.<br/>

 - Usage: `[p]honeycombs`
 - Slash Usage: `/honeycombs`
 - Cooldown: `1 per 60.0 seconds`
 - Checks: `guild_only`

## [p]honeycombset

Settings for the HoneyCombs cog.<br/>

 - Usage: `[p]honeycombset`
 - Checks: `guild_only`

### [p]honeycombset reset

Reset the game settings.<br/>

Allow administrators to reset the game settings for the server in case of any issues or to start fresh again.<br/>

 - Usage: `[p]honeycombset reset`
 - Restricted to: `ADMIN`
 - Aliases: `clear`

### [p]honeycombset minimumplayers

Set the minimum number of players needed to start a game.<br/>

The default minimum is 2 players.<br/>

 - Usage: `[p]honeycombset minimumplayers <minimum_players>`
 - Restricted to: `ADMIN`

### [p]honeycombset checklist

Check the list of players in the current game.<br/>

Shows all players who have joined along with their player numbers.<br/>

 - Usage: `[p]honeycombset checklist`
 - Cooldown: `1 per 60.0 seconds`

### [p]honeycombset shapeodds

Set the pass-chance percentage for a specific shape.<br/>

Shape must be one of: circle, triangle, star, umbrella.<br/>
Percentage is 1–99 (e.g. 20 means a 20% chance of passing).<br/>

Default values:<br/>
- circle: 20%<br/>
- triangle: 20%<br/>
- star: 20%<br/>
- umbrella: 8%<br/>

 - Usage: `[p]honeycombset shapeodds <shape> <percentage>`
 - Restricted to: `ADMIN`

### [p]honeycombset setimage

Set the start image for the game.<br/>

The start image is the image that will be shown when the game starts.<br/>
You can set the image by providing a URL or by attaching an image/gif to the command.<br/>
Only JPG / JPEG / PNG / GIF / WEBP format is supported.<br/>

 - Usage: `[p]honeycombset setimage [image_url]`
 - Restricted to: `ADMIN`
 - Aliases: `setimg`

#### [p]honeycombset setimage clear

Clear the start image (disables it).<br/>

 - Usage: `[p]honeycombset setimage clear`
 - Restricted to: `ADMIN`
 - Aliases: `reset`

### [p]honeycombset losingprice

Set the losing price for the game.<br/>

Set the price to 0 to disable the losing price.<br/>
The default losing price is 100 credits.<br/>

 - Usage: `[p]honeycombset losingprice <amount>`
 - Restricted to: `BOT_OWNER`

### [p]honeycombset endtime

Change the default minutes for when the game should end.<br/>

The default is 10 minutes.<br/>
The maximum is 720 minutes (12 hours).<br/>

 - Usage: `[p]honeycombset endtime <default_minutes>`
 - Restricted to: `ADMIN`

### [p]honeycombset settings

View the current game settings.<br/>

 - Usage: `[p]honeycombset settings`
 - Restricted to: `MOD`
 - Cooldown: `1 per 5.0 seconds`

### [p]honeycombset modonly

Set whether only moderators can start the game.<br/>

If set to True, only moderators can start the game.<br/>
If set to False, anyone can start the game.<br/>

 - Usage: `[p]honeycombset modonly [state=None]`
 - Restricted to: `ADMIN`

### [p]honeycombset winningprice

Set the winning price for the game.<br/>

Set the price to 0 to disable the winning price.<br/>
The default winning price is 100 credits.<br/>

 - Usage: `[p]honeycombset winningprice <amount>`
 - Restricted to: `BOT_OWNER`

