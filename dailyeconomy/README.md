# DailyEconomy Help

Receive a daily amount of economy credits

# daily
 - Usage: `[p]daily `

Claim your daily credits<br/><br/>You can claim your daily credits once every 24 hours.<br/>The amount of credits you receive is random.

# dailyset
 - Usage: `[p]dailyset `
 - Restricted to: `GUILD_OWNER`

Daily Economy Settings

## dailyset view
 - Usage: `[p]dailyset view `
 - Checks: `server_only and is_owner_if_bank_global`

View the current daily limit.

## dailyset amount
 - Usage: `[p]dailyset amount <amount> `
 - Checks: `server_only and is_owner_if_bank_global`

Set the maximum amount of credits you can receive from daily<br/><br/>The default amount is 3000.<br/>The amount must be between 0 and 30000.

Extended Arg Info
> ### amount: int
> ```
> A number without decimal places.
> ```
## dailyset dailyversion
 - Usage: `[p]dailyset dailyversion `

Shows the version of the cog.
