# Heist

A game where players commit heists to steal valuable items or currency, using tools to boost success and shields to reduce losses, with a risk of getting caught by police!

## [p]heistset

Manage global heist settings.<br/>

 - Usage: `[p]heistset`
 - Restricted to: `BOT_OWNER`

### [p]heistset settings

Show current settings for a heist or all heists.<br/>

 - Usage: `[p]heistset settings [heist_type=None]`

### [p]heistset cooldownreset

Reset heist cooldowns for a user.<br/>

If no heist_type is provided, resets all cooldowns for that user.<br/>

**Arguments**<br/>
- `<member>` The member whose cooldowns to reset.<br/>
- `[heist_type]` The specific heist to reset. Omit to reset all.<br/>

 - Usage: `[p]heistset cooldownreset <member> [heist_type=None]`

### [p]heistset resetprice

Reset item prices to default values.<br/>

If no item_name is provided, resets all item prices.<br/>

 - Usage: `[p]heistset resetprice [item_name=None]`

### [p]heistset reset

Reset heist settings to default values.<br/>

If no heist_type is provided, resets all heists.<br/>

 - Usage: `[p]heistset reset [heist_type=None]`

### [p]heistset event

Manage heist reward events.<br/>

 - Usage: `[p]heistset event`

#### [p]heistset event start

Show current event and start/stop one.<br/>

 - Usage: `[p]heistset event start`

### [p]heistset showprices

Show current prices for an item or all shop items.<br/>

 - Usage: `[p]heistset showprices [item_name=None]`

### [p]heistset price

Configure item shop prices.<br/>

Select the item and enter the new price.<br/>

 - Usage: `[p]heistset price`

### [p]heistset set

Configure a heist's parameters.<br/>

Select the heist, then the parameter, then enter the new value.<br/>

 - Usage: `[p]heistset set`

## [p]heist (Hybrid Command)

Heist game.<br/>

 - Usage: `[p]heist`
 - Slash Usage: `/heist`
 - Checks: `guild_only`

### [p]heist shop (Hybrid Command)

Buy items like shields or tools to aid in heists.<br/>

 - Usage: `[p]heist shop`
 - Slash Usage: `/heist shop`
 - Aliases: `shopping`

### [p]heist crew (Hybrid Command)

Organise a 4-player crew robbery for massive rewards.<br/>

Start a lobby: 3 others must join before you can begin.<br/>
Each player's tools and shields apply independently.<br/>
Rewards are split equally among all crew members.<br/>

 - Usage: `[p]heist crew`
 - Slash Usage: `/heist crew`
 - Checks: `guild_only`

### [p]heist inventory (Hybrid Command)

Check your stolen items and tools.<br/>

 - Usage: `[p]heist inventory`
 - Slash Usage: `/heist inventory`
 - Aliases: `inv`

### [p]heist sell (Hybrid Command)

Sell a stolen item or material for currency.<br/>

 - Usage: `[p]heist sell <item> [amount=1]`
 - Slash Usage: `/heist sell <item> [amount=1]`

### [p]heist craft (Hybrid Command)

Craft upgraded shields or tools using materials from heists.<br/>

 - Usage: `[p]heist craft`
 - Slash Usage: `/heist craft`

### [p]heist shield (Hybrid Command)

Check your active shield status.<br/>

 - Usage: `[p]heist shield`
 - Slash Usage: `/heist shield`

### [p]heist bailout (Hybrid Command)

Pay bail to get yourself or another user out of jail.<br/>

 - Usage: `[p]heist bailout [member=None]`
 - Slash Usage: `/heist bailout [member=None]`

### [p]heist profile (Hybrid Command)

Check your active heist profile.<br/>

 - Usage: `[p]heist profile`
 - Slash Usage: `/heist profile`

### [p]heist equip (Hybrid Command)

Equip or unequip items from your inventory.<br/>

Shows only items you currently own. Each slot (shield, tool)<br/>
has its own select menu. Use the unequip buttons to clear a slot.<br/>

 - Usage: `[p]heist equip`
 - Slash Usage: `/heist equip`

### [p]heist level (Hybrid Command)

Check heist level and XP progress.<br/>

 - Usage: `[p]heist level [member=operator.attrgetter('author')]`
 - Slash Usage: `/heist level [member=operator.attrgetter('author')]`

### [p]heist cooldowns (Hybrid Command)

Check cooldowns for all heists.<br/>

 - Usage: `[p]heist cooldowns`
 - Slash Usage: `/heist cooldowns`
 - Aliases: `cooldown`

### [p]heist start (Hybrid Command)

Attempt a heist to steal items.<br/>

 - Usage: `[p]heist start`
 - Slash Usage: `/heist start`

