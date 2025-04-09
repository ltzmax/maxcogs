Easter hunt cog that provides a fun Easter-themed game where users can hunt for eggs, work for egg shards, give eggs to others or steal, and earn achievements. <br/>It includes various commands for interacting with the game, managing progress, and viewing leaderboards.

# [p]easterhunt
Easter Hunt commands<br/>
 - Usage: `[p]easterhunt`
 - Checks: `server_only`
## [p]easterhunt tradeshards
Trade your easter shards for credits.<br/>

1 easter shards is worth 20 credits, these credits will be added to your `[p]bank balance`.<br/>
 - Usage: `[p]easterhunt tradeshards <amount>`
## [p]easterhunt owner
Owner commands for Easter Hunt.<br/>
 - Usage: `[p]easterhunt owner`
 - Restricted to: `BOT_OWNER`
### [p]easterhunt owner resetall
Reset all Easter hunt data for all users and global config.<br/>
 - Usage: `[p]easterhunt owner resetall`
### [p]easterhunt owner setimage
Set a custom image URL for an egg type.<br/>

**Egg Types**: nothing (This is when it doesn't find anything in the fields), common, silver, gold, shiny, legendary, mythical.<br/>
**URL**: The direct URL to the image (or "reset" to clear the custom URL)<br/>

Example: [p]easterhunt setimage silver https://i.maxapp.tv/b6182522w.png<br/>
To reset: [p]easterhunt setimage silver reset<br/>
 - Usage: `[p]easterhunt owner setimage <egg_type> <url>`
### [p]easterhunt owner setshards
Set a user's shard amount.<br/>
 - Usage: `[p]easterhunt owner setshards <user> <amount>`
### [p]easterhunt owner resetuser
Reset a specific user's Easter hunt data.<br/>
 - Usage: `[p]easterhunt owner resetuser <user>`
## [p]easterhunt progress
Check your Easter Hunt progress!<br/>
 - Usage: `[p]easterhunt progress`
## [p]easterhunt work
Work for the Easter Bunny with a fun job!<br/>

You earn shards from working, you can trade it in for currency!<br/>
 - Usage: `[p]easterhunt work`
## [p]easterhunt view
Check your Easter haul!<br/>
 - Usage: `[p]easterhunt view`
## [p]easterhunt give
Give some of your eggs to another user!<br/>

**Arguments**:<br/>
- `user`: The user to give the eggs to.<br/>
- `egg_type`: The type of egg to give (common, silver, gold, shiny).<br/>
- `amount`: The number of eggs to give (default is 1).<br/>

**Notes**:<br/>
- You can only give Common, Silver, Gold, or Shiny Eggs. Legendary and Mythical Eggs cannot be traded.<br/>
- You must have at least the number of eggs you're trying to give.<br/>
- There’s a 5 secoud cooldown between giving eggs.<br/>
 - Usage: `[p]easterhunt give <user> <egg_type> [amount=1]`
## [p]easterhunt resetme
Reset your own Easter hunt data (eggs, shards, pity counters, etc.).<br/>
 - Usage: `[p]easterhunt resetme`
 - Cooldown: `1 per 800.0 seconds`
## [p]easterhunt achievements
Check if you've completed any Easter Hunt!<br/>

You can check your own or someone else's achievements.<br/>
You will need shiny, legendary, and mythical eggs to complete these achievements and get the rewards.<br/>

Why are not all the eggs listed?<br/>
- The rarest of the eggs are the ones that are the achievements in the game, and they are the ones that you can get rewards for completing the achievements while the rest are just for fun and aren't giving any rewards since their rarity is not high enough.<br/>
 - Usage: `[p]easterhunt achievements [user=None]`
 - Aliases: `achievement`
## [p]easterhunt hunt
Go on an Easter egg hunt and wait for the results!<br/>

Every hunt lasts a minute, it's all random for what it brings back!<br/>
You do not get egg shards for hunting, only eggs to top leaderboard, use `[p]easterhunt work` and `[p]easterhunt daily` for egg shards.<br/>

**Various egg types**:<br/>
- common egg, silver egg, gold egg, shiny egg, legendary egg, and mythical egg.<br/>
 - Usage: `[p]easterhunt hunt`
## [p]easterhunt leaderboard
Display the top egg collectors in this server!<br/>

Only Common, Silver, and Gold Eggs are counted in the total for the leaderboard.<br/>
Shiny, Legendary, and Mythical Eggs are special achievement eggs and are not included.<br/>
 - Usage: `[p]easterhunt leaderboard`
 - Aliases: `lb`
## [p]easterhunt daily
Claim your daily Easter gift!<br/>

You can claim every 12 hours.<br/>
The amount of shards you get is from 5 to 20, it's all random of what you get.<br/>
 - Usage: `[p]easterhunt daily`
