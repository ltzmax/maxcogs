# Note
The chest will spawn in all servers it has a channel configured when reloading the cog. I am not responsible for any demages done if you sit and reload to get it to spawn. It will also spawn every 4 hours after first spawn or whatever it says in the `Next Spawn`.

# Chest Help

First to click the button gets random credits to their `[p]bank balance`.

# chestset
 - Usage: `[p]chestset`
 - Checks: `server_only`

Configure the chest game

## chestset channel
 - Usage: `[p]chestset channel [channel=None]`

Set the channel for the chest game.<br/><br/>Use the command again to disable chest from spawning.

## chestset settings
 - Usage: `[p]chestset settings`

Show current settings

## chestset version
 - Usage: `[p]chestset version`

Shows the version of the cog.

## chestset owner
 - Usage: `[p]chestset owner`
 - Restricted to: `BOT_OWNER`

Group owner commands.

### chestset owner toggle
 - Usage: `[p]chestset owner toggle`

Toggle whether you want to use image(s) in spawn/claim embed or not.<br/><br/>Default is Disabled.

### chestset owner setimage
 - Usage: `[p]chestset owner setimage <image_type> [image=None]`

Set a new default image.<br/><br/>Args:<br/>    ctx (discord.Context): The command context.<br/>    image_type (str): The type of image to update (spawn, claim or fail).<br/>    image (str, optional): The URL of the image or None if an attachment is provided. Defaults to None.

### chestset owner credit
 - Usage: `[p]chestset owner credit <coins>`
 - Aliases: `credits`

Change how much credits users can get from claiming.<br/><br/>Default is 5,000. (it random select between 1 and 5,000)

### chestset owner setemoji
 - Usage: `[p]chestset owner setemoji <emoji>`

Change the default emoji on the button.<br/><br/>Leave blank to reset back to default.<br/>Note that your bot must share same server as the emoji for the emoji to work.

### chestset owner rate
 - Usage: `[p]chestset owner rate <fail_rate>`

Change the fail rate to a different.<br/><br/>Default is 30% fail rate.<br/><br/>**Example**:<br/>- `[p]chestset rate 40` This will make you fail 40% of time to get coins.<br/><br/>**Arguments**:<br/>- `<fail_rate>` The number of whichever % you want users to fail.<br/>    - Cannot be longer than 100 and less than 1.

### chestset owner reset
 - Usage: `[p]chestset owner reset`

Reset back to default setting
