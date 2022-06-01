``
[p] is your prefix.
``
## This cog require send_messages and view_channel permission to be used.

## NOTE
Please be aware that you cannot set events in threads and will not be available in those channels. It will simple reset your events back to default if you try to set channel to threads. (This only matter for discord.py 2.0.)

## Usage
This cog sends shard events and can be extremely spammy sometimes, depending on how your connection to discord is or how your bot is having its time with the gateway. this is not anything you need to worry about, you just will see reconnections and disconnections, it'd take about a sec for it to connect back and it will repeat like that.

## Commands
```yaml
[p]connectset
```
## Description
Manage settings for onconnect.

## NOTE
Before you set event channel make sure your bot has send_messages and view_channel in the channel you select to use as event. If you want it to send embed, you have to enable embed_links else it will send without embed. It is recommneded to NOT set to threads channel. This will not work.
```yaml
[p]connectset channel #general
```
## Desctiption
Set the channel to log shard events to.
```yaml
[p]connectset emoji
```
## Desctiption
Settings to change default emoji.
```yaml
[p]connectset emoji green <emoji_you_want>
```
## Desctiption
Change the green emoji to your own.
```yaml
[p]connectset emoji orange <emoji_you_want>
```
## Desctiption
Change the orange emoji to your own.
```yaml
[p]connectset emoji red <emoji_you_want>
```
## Desctiption
Change the red emoji to your own.
```yaml
[p]connectset settings
```
## Description
Shows the current settings for OnConnect.

## Missing the cog?
1. Add the repo
```yaml
[p]repo add maxcogs https://github.com/ltzmax/maxcogs
```
2. install the cog
```yaml
[p]cog install maxcogs onconnect
```
3. load the cog
```yaml
[p]load onconnect
```