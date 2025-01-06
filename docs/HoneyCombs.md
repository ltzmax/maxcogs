## Game information
In Sugar Honeycombs, contestants were told to choose a honeycomb shape to carve out before being informed of the game's premise, while in this cog, you cannot choose a shape at all, the bot will automatically choose a random shape this for you. The options were a circle, a triangle, a star, and an Umbrella. After selecting a shape, they were handed small metal containers inside, they found the shapes they chose drawn on the sugar honeycombs along with a small needle. The bot will use 10 minutes to finish each of the shapes a player have, a new message will be sent once the 10 minutes are done, you will know if you passed or eliminated.

# [p]honeycombs (Hybrid Command)
Start a game of Sugar Honeycombs.<br/>

You need at least 5 players to start the game.<br/>
The maximum number of players is 456.<br/>
 - Usage: `[p]honeycombs`
 - Slash Usage: `/honeycombs`
 - Cooldown: `1 per 60.0 seconds`
 - Checks: `server_only`
# [p]honeycombset
Settings for the HoneyCombs cog.<br/>
 - Usage: `[p]honeycombset`
 - Aliases: `squidgame and sg`
 - Checks: `server_only`
## [p]honeycombset reset
Reset the game settings.<br/>

Allow administrators to reset the game settings for the server in case of any issues or to start fresh again.<br/>
 - Usage: `[p]honeycombset reset`
 - Restricted to: `ADMIN`
 - Aliases: `clear`
## [p]honeycombset losingprice
Set the losing price for the game.<br/>

Set the price to 0 to disable the losing price.<br/>

The default losing price is 100 credits.<br/>
The losing price is the amount of credits a player will lose if they fail the game.<br/>
 - Usage: `[p]honeycombset losingprice <amount>`
 - Restricted to: `BOT_OWNER`
## [p]honeycombset checklist
Check the list of players in current game.<br/>

This command will show the list of players who have joined the game along with their player numbers.<br/>
 - Usage: `[p]honeycombset checklist`
 - Cooldown: `1 per 60.0 seconds`
## [p]honeycombset modonly
Set whether only moderators can start the game.<br/>

If set to True, only moderators can start the game.<br/>
If set to False, anyone can start the game.<br/>
 - Usage: `[p]honeycombset modonly [state=None]`
 - Restricted to: `ADMIN`
## [p]honeycombset minimumplayers
Set the minimum number of players needed to start a game.<br/>

The default minimum number of players is 5.<br/>
 - Usage: `[p]honeycombset minimumplayers <minimum_players>`
 - Restricted to: `ADMIN`
## [p]honeycombset winningprice
Set the winning price for the game.<br/>

Set the price to 0 to disable the winning price.<br/>

The default winning price is 100 credits.<br/>
The winning price is the amount of credits a player will receive if they pass the game.<br/>
 - Usage: `[p]honeycombset winningprice <amount>`
 - Restricted to: `BOT_OWNER`
## [p]honeycombset defaultminutes
Change the default minutes for the game to run for.<br/>

**Please note**<br/>
- This is for the length of the game to run for, not the length of when the game starts.<br/>

The default minutes is 10.<br/>
The maximum number of minutes is 360 (6 hours).<br/>

**Examples**:<br/>
- `[p]honeycombset defaultminutes 20` - Set the default number of minutes to 20 minutes.<br/>
- `[p]honeycombset defaultminutes 60` - Set the default number of minutes to 60 minutes. (1 hour)<br/>
You can use [unitconverters](https://www.unitconverters.net/time/minutes-to-hours.htm) to convert minutes to hours.<br/>

**Arguments**:<br/>
- `<default_minutes>`: The default number of minutes for the game.<br/>
 - Usage: `[p]honeycombset defaultminutes <default_minutes>`
 - Restricted to: `ADMIN`
## [p]honeycombset setimage
Set the start image for the game.<br/>

The start image is the image that will be shown when the game starts.<br/>
You can set the image by providing a URL or by attaching an image/gif to the command.<br/>
Only JPG / JPEG / PNG / GIF / WEBP format is supported.<br/>
 - Usage: `[p]honeycombset setimage [image_url]`
 - Restricted to: `ADMIN`
 - Aliases: `setimg`
### [p]honeycombset setimage clear
Reset the start image to default.<br/>
 - Usage: `[p]honeycombset setimage clear`
 - Restricted to: `ADMIN`
 - Aliases: `reset`
## [p]honeycombset settings
View the current game settings.<br/>
 - Usage: `[p]honeycombset settings`
 - Restricted to: `MOD`
 - Cooldown: `1 per 5.0 seconds`
