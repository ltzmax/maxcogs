# Plague

A plague game.

## [p]plagueprofile

Show's your Plague Game profile<br/>

 - Usage: `[p]plagueprofile [member]`
 - Checks: `guild_only`

## [p]infect

Infect another user. You must be infected to use this command.<br/>

 - Usage: `[p]infect <member>`
 - Aliases: `cough`
 - Cooldown: `1 per 30.0 seconds`
 - Checks: `guild_only and is_infected`

## [p]cure

Cure a user. You must be a Doctor to use this command.<br/>

 - Usage: `[p]cure <member>`
 - Cooldown: `1 per 15.0 seconds`
 - Checks: `guild_only and is_doctor`

## [p]plaguenotify

Enable/Disable Plague Game notifications.<br/>

 - Usage: `[p]plaguenotify`

## [p]plaguedoctor

Become a doctor for 10,000 currency.<br/>

You must be healthy to study at medical school.<br/>

 - Usage: `[p]plaguedoctor`
 - Aliases: `plaguedoc`
 - Checks: `is_healthy and not_doctor`

## [p]plaguebearer

Become a plaguebearer for 10,000 currency.<br/>

You must be infected to mutate into a plaguebearer.<br/>

 - Usage: `[p]plaguebearer`
 - Checks: `is_infected and not_plaguebearer`

## [p]resign

Quit being a doctor or plaguebearer for 10,000 currency.<br/>

You must be infected to mutate into a plaguebearer.<br/>

 - Usage: `[p]resign`
 - Checks: `has_role`

## [p]infectme

Get infected for 5,000 currency.<br/>

Why would you willingly infect yourself?<br/>

 - Usage: `[p]infectme`
 - Checks: `is_healthy and not_doctor`

## [p]treatme

Get cured from the plague for 5,000 currency.<br/>

This is America, so the health care is expensive.<br/>

 - Usage: `[p]treatme`
 - Checks: `is_infected and not_plaguebearer`

## [p]plagueset

Settings for the Plague game.<br/>

 - Usage: `[p]plagueset`
 - Restricted to: `BOT_OWNER`

### [p]plagueset reset

Reset the entire Plague Game.<br/>

 - Usage: `[p]plagueset reset`

### [p]plagueset doctor

Set a doctor.<br/>

 - Usage: `[p]plagueset doctor <user>`

### [p]plagueset plaguebearer

Set a plaguebearer.<br/>

 - Usage: `[p]plagueset plaguebearer <user>`

### [p]plagueset cure

Manually cure a user.<br/>

 - Usage: `[p]plagueset cure <user>`

### [p]plagueset channel

Set the log channel<br/>

 - Usage: `[p]plagueset channel [channel=None]`

### [p]plagueset infected

Sends a list of the infected users.<br/>

 - Usage: `[p]plagueset infected`

#### [p]plagueset infected guild

Sends a list of the infected users in a guild.<br/>

 - Usage: `[p]plagueset infected guild [guild]`

### [p]plagueset name

Set's the plague's name. Leave blank to show the current name.<br/>

 - Usage: `[p]plagueset name [name]`

### [p]plagueset version

Shows the version of the cog.<br/>

 - Usage: `[p]plagueset version`

### [p]plagueset healthy

Sends a list of the healthy users.<br/>

 - Usage: `[p]plagueset healthy`

### [p]plagueset resetuser

Reset a user.<br/>

 - Usage: `[p]plagueset resetuser <user>`

### [p]plagueset stats

View plague game stats.<br/>

 - Usage: `[p]plagueset stats`

### [p]plagueset rate

Set the Plague Game infection rate.<br/>

 - Usage: `[p]plagueset rate <rate>`

### [p]plagueset infect

Manually infect a user.<br/>

 - Usage: `[p]plagueset infect <user>`

### [p]plagueset settings

View the Plague Game settings.<br/>

 - Usage: `[p]plagueset settings`
 - Aliases: `showsettings`

