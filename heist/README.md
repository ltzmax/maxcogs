A game where players commit heists to steal valuable items or currency, using tools to boost success and shields to reduce losses, with a risk of getting caught by police!

# [p]heist (Hybrid Command)
Heist game.<br/>
 - Usage: `[p]heist`
 - Slash Usage: `/heist`
 - Checks: `server_only`
## [p]heist shop (Hybrid Command)
Buy items like shields or tools to aid in heists.<br/>
 - Usage: `[p]heist shop`
 - Slash Usage: `/heist shop`
 - Aliases: `shopping`
## [p]heist equip (Hybrid Command)
Equip items for heists.<br/>
 - Usage: `[p]heist equip`
 - Slash Usage: `/heist equip`
### [p]heist equip shield (Hybrid Command)
Equip a shield from your inventory.<br/>
 - Usage: `[p]heist equip shield <shield_type>`
 - Slash Usage: `/heist equip shield <shield_type>`
### [p]heist equip consumable (Hybrid Command)
Equip a consumable from your inventory.<br/>
 - Usage: `[p]heist equip consumable <consumable_type>`
 - Slash Usage: `/heist equip consumable <consumable_type>`
### [p]heist equip unequip (Hybrid Command)
Unequip a specific item type.<br/>
 - Usage: `[p]heist equip unequip <item_type>`
 - Slash Usage: `/heist equip unequip <item_type>`
### [p]heist equip tool (Hybrid Command)
Equip a tool from your inventory.<br/>
 - Usage: `[p]heist equip tool <tool_type>`
 - Slash Usage: `/heist equip tool <tool_type>`
## [p]heist status (Hybrid Command)
Check your active heist status.<br/>
 - Usage: `[p]heist status`
 - Slash Usage: `/heist status`
## [p]heist craft (Hybrid Command)
Craft upgraded shields or tools using materials from heists.<br/>

Craftable items are stronger than shop-bought items but require specific materials.<br/>

**Vaild craftable items**:<br/>
- `reinforced_wooden_shield`, `enhanced_pickpocket_gloves`, `reinforced_iron_shield`, `reinforced_steel_shield`, `reinforced_titanium_shield`, `reinforced_diamond_shield`, `enhanced_crowbar`, `enhanced_glass_cutter`, `enhanced_brass_knuckles`, `enhanced_laser_jammer`, `enhanced_hacking_device`, `enhanced_store_key`, `enhanced_lockpick_kit`, `enhanced_grappling_hook`, `enhanced_bike_tool`, `enhanced_car_tool` and `enhanced_motorcycle_tool`.<br/>
 - Usage: `[p]heist craft <recipe_name>`
 - Slash Usage: `/heist craft <recipe_name>`
## [p]heist start (Hybrid Command)
Attempt a heist to steal items.<br/>
 - Usage: `[p]heist start`
 - Slash Usage: `/heist start`
## [p]heist sell (Hybrid Command)
Sell a stolen item or material for currency.<br/>
 - Usage: `[p]heist sell <item> [amount=1]`
 - Slash Usage: `/heist sell <item> [amount=1]`
## [p]heist shield (Hybrid Command)
Check your active shield status.<br/>
 - Usage: `[p]heist shield`
 - Slash Usage: `/heist shield`
## [p]heist inventory (Hybrid Command)
Check your stolen items and tools.<br/>
 - Usage: `[p]heist inventory`
 - Slash Usage: `/heist inventory`
 - Aliases: `inv`
## [p]heist bailout (Hybrid Command)
Pay bail to get yourself or another user out of jail.<br/>
 - Usage: `[p]heist bailout [member=None]`
 - Slash Usage: `/heist bailout [member=None]`
## [p]heist cooldowns (Hybrid Command)
Check cooldowns for all heists.<br/>
 - Usage: `[p]heist cooldowns`
 - Slash Usage: `/heist cooldowns`
 - Aliases: `cooldown`
 
# [p]heistset
Manage global heist settings.<br/>
 - Usage: `[p]heistset`
 - Restricted to: `BOT_OWNER`
## [p]heistset resetprice
Reset item prices to default values.<br/>

If no item_name is provided, resets all item prices.<br/>
 - Usage: `[p]heistset resetprice [item_name=None]`
## [p]heistset reset
Reset heist settings to default values.<br/>

If no heist_type is provided, resets all heists.<br/>
 - Usage: `[p]heistset reset [heist_type=None]`
## [p]heistset set
Modify a parameter for a specific heist type using a modal.<br/>

You can edit multiple prices until the interaction times out.<br/>

**Arguments**<br/>
- heist_type: Valid options:<br/>
    - `pocket_steal`, `atm_smash`, `store_robbery`, `jewelry_store`, `fight_club`, `art_gallery`, `casino_vault`, `museum_relic`, `luxury_yacht`, `street_bike`, `street_motorcycle`, `street_car`, `corporate`, `bank`, `elite`.<br/>
- param: The parameter to change. Valid options:<br/>
    - `risk`: Failure probability (0–100, percentage).<br/>
   - `min_reward`: Minimum reward amount (credits, non-negative).<br/>
   - `max_reward`: Maximum reward amount (credits, non-negative, must be above min_reward).<br/>
   - `cooldown`: Time before the heist can be attempted again (seconds, minimum 60).<br/>
   - `min_success`: Minimum success chance (0–100, percentage).<br/>
   - `max_success`: Maximum success chance (0–100, percentage, must be above min_success).<br/>
   - `duration`: Time to complete the heist (seconds, minimum 30).<br/>
   - `police_chance`: Chance of getting caught (0–100, percentage).<br/>
   - `jail_time`: Jail duration if caught (seconds, minimum 60).<br/>
- value: The new value for the parameter (percentage for risk/success, credits for rewards, seconds for cooldown/duration).<br/>
 - Usage: `[p]heistset set`
## [p]heistset price
Modify the price of an item in the shop using a modal.<br/>

You can edit multiple prices until the interaction times out.<br/>
 - Usage: `[p]heistset price`
## [p]heistset show
Show current settings for a heist or all heists.<br/>

Parameters:<br/>
- heist_type: The heist to show (e.g., pocket_steal). Omit for all heists.<br/>
 - Usage: `[p]heistset show [heist_type=None]`
## [p]heistset showprices
Show current prices for an item or all shop items.<br/>

Parameters:<br/>
- item_name: The item to show (e.g., wooden_shield). Omit for all items.<br/>
 - Usage: `[p]heistset showprices [item_name=None]`
