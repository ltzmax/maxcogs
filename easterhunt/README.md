Easter hunt cog that provides a fun Easter-themed game where users can hunt for eggs, work for egg shards, give eggs to others or steal, and earn achievements.<br/>It includes various commands for interacting with the game, managing progress, and viewing leaderboards.

# [p]easterhunt (Hybrid Command)
Easter Hunt commands<br/>

Documentations for the rarity of the eggs and how it works can be found here: https://easterhunt.maxapp.tv<br/>
 - Usage: `[p]easterhunt`
 - Slash Usage: `/easterhunt`
 - Aliases: `ehunt and easterh`
 - Checks: `server_only`
## [p]easterhunt sellgems (Hybrid Command)
Sell your hidden gems for egg shards.<br/>

Each hidden gem can be sold for 500 egg shards.<br/>
 - Usage: `[p]easterhunt sellgems <amount>`
 - Slash Usage: `/easterhunt sellgems <amount>`
## [p]easterhunt daily (Hybrid Command)
Claim your daily Easter gift!<br/>

You can claim every 12 hours.<br/>
The amount of shards you get is from 5 to 140, it's all random of what you get.<br/>
 - Usage: `[p]easterhunt daily`
 - Slash Usage: `/easterhunt daily`
## [p]easterhunt tradeshards (Hybrid Command)
Trade your easter shards for credits.<br/>

1 easter shards is worth 20 credits, these credits will be added to your `[p]bank balance`.<br/>
 - Usage: `[p]easterhunt tradeshards <amount>`
 - Slash Usage: `/easterhunt tradeshards <amount>`
## [p]easterhunt inventory (Hybrid Command)
Check your Easter haul!<br/>
 - Usage: `[p]easterhunt inventory [member=None]`
 - Slash Usage: `/easterhunt inventory [member=None]`
 - Aliases: `inv, view, and views`
## [p]easterhunt give (Hybrid Command)
Give some of your eggs to another user!<br/>

**Arguments**:<br/>
- `member`: The user to give the eggs to.<br/>
- `egg_type`: The type of egg to give (common, silver, gold, shiny).<br/>
- `amount`: The number of eggs to give (default is 1).<br/>

**Notes**:<br/>
- You can only give Common, Silver, Gold, or Shiny Eggs. Legendary and Mythical Eggs cannot be traded.<br/>
- You must have at least the number of eggs you're trying to give.<br/>
- There’s a 5 second cooldown between giving eggs.<br/>
 - Usage: `[p]easterhunt give <member> <egg_type> [amount=1]`
 - Slash Usage: `/easterhunt give <member> <egg_type> [amount=1]`
## [p]easterhunt resetme (Hybrid Command)
Reset your own Easter hunt data (eggs, shards, pity counters, etc.).<br/>
 - Usage: `[p]easterhunt resetme`
 - Slash Usage: `/easterhunt resetme`
 - Cooldown: `1 per 800.0 seconds`
## [p]easterhunt achievements (Hybrid Command)
Check if you've completed any Easter Hunt!<br/>

You can check your own or someone else's achievements.<br/>
You will need shiny, legendary, and mythical eggs to complete these achievements and get the rewards.<br/>

Why are not all the eggs listed?<br/>
- The rarest of the eggs are the ones that are the achievements in the game, and they are the ones that you can get rewards for completing the achievements while the rest are just for fun and aren't giving any rewards since their rarity is not high enough.<br/>
 - Usage: `[p]easterhunt achievements [member=None]`
 - Slash Usage: `/easterhunt achievements [member=None]`
 - Aliases: `achievement`
## [p]easterhunt progress (Hybrid Command)
Check your Easter Hunt progress!<br/>
 - Usage: `[p]easterhunt progress`
 - Slash Usage: `/easterhunt progress`
## [p]easterhunt hunt (Hybrid Command)
Go on an Easter egg hunt and wait for the results!<br/>

Every hunt lasts a minute, it's all random for what it brings back!<br/>
You do not get egg shards for hunting, only eggs to top leaderboard, use `[p]easterhunt work` and `[p]easterhunt daily` for egg shards.<br/>

**Various egg types**:<br/>
- common egg, silver egg, gold egg, shiny egg, legendary egg, and mythical egg.<br/>
 - Usage: `[p]easterhunt hunt`
 - Slash Usage: `/easterhunt hunt`
## [p]easterhunt leaderboard (Hybrid Command)
Display the top egg collectors in this server!<br/>

Only Common, Silver, and Gold Eggs are counted in the total for the leaderboard.<br/>
Shiny, Legendary, and Mythical Eggs are special achievement eggs and are not included.<br/>
 - Usage: `[p]easterhunt leaderboard`
 - Slash Usage: `/easterhunt leaderboard`
 - Aliases: `lb`
## [p]easterhunt work (Hybrid Command)
Work for the Easter Bunny with a fun job!<br/>

You earn shards from working, you can trade it in for currency!<br/>
 - Usage: `[p]easterhunt work`
 - Slash Usage: `/easterhunt work`

# [p]ownerset
Owner commands for Easter Hunt.<br/>
 - Usage: `[p]ownerset`
 - Restricted to: `BOT_OWNER`
## [p]ownerset resetuser
Reset a specific user's Easter hunt data.<br/>
 - Usage: `[p]ownerset resetuser <user>`
## [p]ownerset resetshift
Reset a specific user's shift time and active states.<br/>
 - Usage: `[p]ownerset resetshift <user>`
## [p]ownerset setimage
Set a custom image URL for an egg type.<br/>

**Egg Types**: nothing (This is when it doesn't find anything in the fields), common, silver, gold, shiny, legendary, mythical.<br/>
**URL**: The direct URL to the image (or "reset" to clear the custom URL)<br/>

Example: [p]easterhunt setimage silver https://i.maxapp.tv/b6182522w.png<br/>
To reset: [p]easterhunt setimage silver reset<br/>
 - Usage: `[p]ownerset setimage <egg_type> <url>`
## [p]ownerset setgems
Set a user's hidden gems amount.<br/>
 - Usage: `[p]ownerset setgems <user> <amount>`
## [p]ownerset setshards
Set a user's shard amount.<br/>
 - Usage: `[p]ownerset setshards <user> <amount>`
## [p]ownerset setachievement
Set a specific achievement for a user (true/false).<br/>

Use the achievement key from [p]easterhunt achievements.<br/>
 - Usage: `[p]ownerset setachievement <user> <key> <value>`
## [p]ownerset resetall
Reset all Easter hunt data for all users and global config.<br/>
 - Usage: `[p]ownerset resetall`
