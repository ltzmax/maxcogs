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

### [p]earthquakeset safety

Set or clear a custom safety message for alerts.<br/>

 - Usage: `[p]earthquakeset safety [message]`

### [p]earthquakeset role

Set or clear the role to ping for earthquake alerts.<br/>

 - Usage: `[p]earthquakeset role <role>`

Extended Arg Info

> ### role: Optional[discord.role.Role]
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     

### [p]earthquakeset webhook

Enable or disable the use of webhooks for earthquake alerts.<br/>

**Example:**<br/>
- `[p]earthquakeset webhook true` to enable webhooks.<br/>
- `[p]earthquakeset webhook false` to disable webhooks (default).<br/>

**Arguments:**<br/>
- `[use_webhook]`: `true` to enable webhooks, `false` to disable.<br/>

 - Usage: `[p]earthquakeset webhook <use_webhook>`

Extended Arg Info

> ### use_webhook: bool
> ```
> Can be 1, 0, true, false, t, f
> ```

### [p]earthquakeset country

Filter earthquake alerts to a specific country or region.<br/>

The filter is matched against the USGS location string, which typically<br/>
looks like `10km NNE of City, Country`. The match is case-insensitive<br/>
and partial, so `Norway` will also match `Norwegian Sea`.<br/>

Leave blank to clear the filter and receive global alerts.<br/>

**Examples:**<br/>
- `[p]earthquakeset country Japan`<br/>
- `[p]earthquakeset country Norway`<br/>
- `[p]earthquakeset country` to clear and receive global alerts.<br/>

**Arguments:**<br/>
- `[country]`: The country or region name to filter by.<br/>

 - Usage: `[p]earthquakeset country [country]`

Extended Arg Info

> ### country: Optional[str] = None
> ```
> Must be valid country name otherwise it'd ignore.
> ```

### [p]earthquakeset settings

Show current earthquake alert settings.<br/>

 - Usage: `[p]earthquakeset settings`

### [p]earthquakeset magnitude

Set the minimum magnitude for earthquake alerts.<br/>

**Note:** Setting a lower magnitude will increase the frequency of notifications, as it includes smaller earthquakes that may not be significant in your area or other. It is recommended to set a higher threshold (e.g., 4.5 or higher) to receive alerts only for significant events.<br/>

**Example:**<br/>
- `[p]earthquakeset magnitude 5.0` to set the minimum magnitude to 5.0.<br/>
- `[p]earthquakeset magnitude` to reset to the default value of 4.5.<br/>

**Arguments:**<br/>
- `[magnitude]`: The minimum magnitude for alerts (default is 4.5, range 1.0 to 10.0).<br/>

 - Usage: `[p]earthquakeset magnitude [magnitude=4.5]`

### [p]earthquakeset channel

Set or clear the channel for earthquake alerts.<br/>

 - Usage: `[p]earthquakeset channel <channel>`

Extended Arg Info

> ### channel: Optional[discord.channel.TextChannel]
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by channel URL.
>     4. Lookup by name
> 
>     

