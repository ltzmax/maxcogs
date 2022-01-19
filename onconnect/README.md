## onconnect

# NOTE
This cog sends shard events and and can be extremely spammy sometimes, depending on how your connection to discord is, if your host is slow or having a bad time with discord, it will choose to send reconnections each times it finds out the shards is having a bad time. This is not a bad thing, its just a good thing, you have control that your shard actually reconnected. so dont worry about it.

Just anyother note:
- When you set event channel to any channel you want it to send to, you have agreed that you want the spam to happen.

## READ BEFORE YOU SET CHANNEL
- ⚠ **Before you set event channel make sure your bot has `manage_webhooks` in the channel you select to use as event.** ⚠

Simple guide:
1) You can adjust permissions of specific channels, both text and voice, through the channel settings menu by hovering over a channel and clicking on the cog icon.

2) Select the Permissions tab on the left-hand side.

3) You can add roles or specific people/bot(s) whom you want to manage channel permissions for by clicking the plus sign. 

4) Once you have added a Role or member/bot(s) you can begin assigning channel permissions to this group or person or bot(s).

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
6. See settings
```
[p]connectset settings
```
On every commands, leave them blank to reset settings back to default.

## Support
You can find me in the [Cog Support server](https://discord.gg/GET4DVk) (#support_othercogts) or in [Red main server](https://discord.gg/red) (#testing) for questions. Just ping MAX#1000 (345628097929936898)