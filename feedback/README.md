# Feedback Help

Send feedback.

# feedbackset
 - Usage: `[p]feedbackset `
 - Restricted to: `ADMIN`

Manage feedback settings.

## feedbackset toggle
 - Usage: `[p]feedbackset toggle [toggle] `

Toggle feedbacks on/off.

Extended Arg Info
> ### toggle: bool = None
> ```
> Can be 1, 0, true, false, t, f
> ```
## feedbackset showsettings
 - Usage: `[p]feedbackset showsettings `
 - Aliases: `settings`

Show feedback settings.

## feedbackset reset
 - Usage: `[p]feedbackset reset `
 - Aliases: `clear`

Reset feedback settings.

## feedbackset version
 - Usage: `[p]feedbackset version `

Shows the cog version.

## feedbackset channel
 - Usage: `[p]feedbackset channel [channel] `

Set the feedback channel.

Extended Arg Info
> ### channel: discord.channel.TextChannel = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
# feedback (Hybrid Command)
 - Usage: `[p]feedback <feedback> `
 - Slash Usage: `/feedback <feedback> `
 - Cooldown: `1 per 60.0 seconds`

Send a feedback to the server's feedback channel.
