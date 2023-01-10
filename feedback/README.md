# Feedback Help

Send feedback.

# feedbackset
 - Usage: `[p]feedbackset `
 - Restricted to: `ADMIN`

Manage feedback settings.

## feedbackset channel
 - Usage: `[p]feedbackset channel [channel=None] `

Set feedback channel.

Extended Arg Info
> ### channel: discord.channel.TextChannel = None
> 
> 
>     1. Lookup by ID.
>     2. Lookup by mention.
>     3. Lookup by name
> 
>     
## feedbackset reset
 - Usage: `[p]feedbackset reset `

Reset feedback settings.

## feedbackset showsettings
 - Usage: `[p]feedbackset showsettings `
 - Aliases: `settings`

Show feedback settings.

## feedbackset toggle
 - Usage: `[p]feedbackset toggle [toggle] `

Toggle feedbacks on/off.

Extended Arg Info
> ### toggle: bool = None
> ```
> Can be 1, 0, true, false, t, f
> ```
# feedback (Hybrid Command)
 - Usage: `[p]feedback <feedback> `
 - Slash Usage: `/feedback <feedback> `

Send a feedback to the server's feedback channel.

Extended Arg Info
> ### feedback: str
> ```
> A single word, if not using slash and multiple words are necessary use a quote e.g "Hello world".
> ```
