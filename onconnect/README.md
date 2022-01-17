## onconnect

# NOTE
This cog sends shard events and and can be extremely spammy sometimes, depending on how your connection to discord is, if your host is slow or having a bad time with discord, it will choose to send reconnections each times it finds out the shards is having a bad time. This is not a bad thing, its just a good thing, you have control that your shard actually reconnected. so dont worry about it.

Just anyother note:
- When you set event channel to any channel you want it to send to, you have agreed that you want the spam to happen.

## Install and quick setup.
`[p]` is your prefix.

1. Add the repo
```
[p]repo add maxcogs https://github.com/ltzmax/maxcogs
```
2. Install the cog and load it
```
[p]cog install maxcogs onconnect
# type "i agree" if bot ask for it
# now wait until finished.
[p]load onconnect
```
3. See all commands
```
[p]connectset
```
## Required.
- ⚠ **Before you set event channel make sure your bot has `manage_webhooks` in the channel you select to use as event.** ⚠

This cog require you to use webhooks due to how events is made in this cog. Missing this permission will result the cog to fail sending events and your logs will be entered with errors.

4. Set event channel
```
[p]connectset channel #general
# Choose any channel you want
```
5. Set your own emojis
```
[p]connectset emoji 
# group commands, set any emojis you want on each colors.
```
