# Plague Help

A plague game.

# infect
 - Usage: `[p]infect <member>`
 - Aliases: `cough`
 - Cooldown: `1 per 30.0 seconds`
 - Checks: `server_only and is_infected`

Infect another user. You must be infected to use this command.

# cure
 - Usage: `[p]cure <member>`
 - Cooldown: `1 per 15.0 seconds`
 - Checks: `server_only and is_doctor`

Cure a user. You must be a Doctor to use this command.

# plagueprofile
 - Usage: `[p]plagueprofile [member]`
 - Aliases: `pprofile`
 - Checks: `server_only`

Show's your Plague Game profile

# plaguenotify
 - Usage: `[p]plaguenotify`

Enable/Disable Plague Game notifications.

# plaguedoctor
 - Usage: `[p]plaguedoctor`
 - Aliases: `plaguedoc`
 - Checks: `is_healthy and not_doctor`

Become a doctor for 10,000 currency.<br/><br/>You must be healthy to study at medical school.

# plaguebearer
 - Usage: `[p]plaguebearer`
 - Checks: `is_infected and not_plaguebearer`

Become a plaguebearer for 10,000 currency.<br/><br/>You must be infected to mutate into a plaguebearer.

# resign
 - Usage: `[p]resign`
 - Checks: `has_role`

Quit being a doctor or plaguebearer for 10,000 currency.<br/><br/>You must be infected to mutate into a plaguebearer.

# infectme
 - Usage: `[p]infectme`
 - Checks: `is_healthy and not_doctor`

Get infected for 5,000 currency.<br/><br/>Why would you willingly infect yourself?

# treatme
 - Usage: `[p]treatme`
 - Checks: `is_infected and not_plaguebearer`

Get cured from the plague for 5,000 currency.<br/><br/>This is America, so the health care is expensive.

# plagueset
 - Usage: `[p]plagueset`
 - Restricted to: `BOT_OWNER`

Settings for the Plague game.

## plagueset name
 - Usage: `[p]plagueset name [name]`

Set's the plague's name. Leave blank to show the current name.

## plagueset doctor
 - Usage: `[p]plagueset doctor <user>`

Set a doctor.

## plagueset version
 - Usage: `[p]plagueset version`

Shows the version of the cog.

## plagueset healthy
 - Usage: `[p]plagueset healthy`

Sends a list of the healthy users.

## plagueset infected
 - Usage: `[p]plagueset infected`

Sends a list of the infected users.

### plagueset infected server
 - Usage: `[p]plagueset infected server [server]`

Sends a list of the infected users in a server.

## plagueset cure
 - Usage: `[p]plagueset cure <user>`

Manually cure a user.

## plagueset stats
 - Usage: `[p]plagueset stats`

View plague game stats.

## plagueset infect
 - Usage: `[p]plagueset infect <user>`

Manually infect a user.

## plagueset reset
 - Usage: `[p]plagueset reset`

Reset the entire Plague Game.

## plagueset rate
 - Usage: `[p]plagueset rate <rate>`

Set the Plague Game infection rate.

## plagueset settings
 - Usage: `[p]plagueset settings`
 - Aliases: `showsettings`

View the Plague Game settings.

## plagueset channel
 - Usage: `[p]plagueset channel [channel=None]`

Set the log channel

## plagueset plaguebearer
 - Usage: `[p]plagueset plaguebearer <user>`

Set a plaguebearer.

## plagueset resetuser
 - Usage: `[p]plagueset resetuser <user>`

Reset a user.

