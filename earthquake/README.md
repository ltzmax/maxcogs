# Earthquake

Real-time worldwide earthquake alerts from USGS.

## [p]earthquakeset

Configure earthquake alerts for this server.<br/>

⚠️**WARNING**⚠️<br/>
This cog provides informational alerts only and may have 15–30 minute delays. Always prioritize local authorities for real-time safety information.<br/>

 - Usage: `[p]earthquakeset`
 - Restricted to: `ADMIN`
 - Aliases: `eqset and earthquake`
 - Checks: `guild_only`

### [p]earthquakeset settings

Show current earthquake alert settings.<br/>

 - Usage: `[p]earthquakeset settings`

### [p]earthquakeset safety

Set or clear a custom safety message for alerts.<br/>

 - Usage: `[p]earthquakeset safety [message]`

### [p]earthquakeset magnitude

Set the minimum magnitude for earthquake alerts.<br/>

**Note:** Setting a lower magnitude will increase the frequency of notifications, as it includes smaller earthquakes that may not be significant in your area or other. It is recommended to set a higher threshold (e.g., 4.5 or higher) to receive alerts only for significant events.<br/>

**Example:**<br/>
- `[p]earthquakeset magnitude 5.0` to set the minimum magnitude to 5.0.<br/>
- `[p]earthquakeset magnitude` to reset to the default value of 4.5.<br/>

**Arguments:**<br/>
- `[magnitude]`: The minimum magnitude for alerts (default is 4.5, range 1.0 to 10.0).<br/>

 - Usage: `[p]earthquakeset magnitude [magnitude=4.5]`

### [p]earthquakeset webhook

Enable or disable the use of webhooks for earthquake alerts.<br/>

**Example:**<br/>
- `[p]earthquakeset webhook true` to enable webhooks.<br/>
- `[p]earthquakeset webhook false` to disable webhooks (default).<br/>

**Arguments:**<br/>
- `[use_webhook]`: `true` to enable webhooks, `false` to disable.<br/>

 - Usage: `[p]earthquakeset webhook <use_webhook>`

### [p]earthquakeset role

Set or clear the role to ping for earthquake alerts.<br/>

 - Usage: `[p]earthquakeset role <role>`

### [p]earthquakeset channel

Set or clear the channel for earthquake alerts.<br/>

 - Usage: `[p]earthquakeset channel <channel>`
