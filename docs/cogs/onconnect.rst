.. _onconnect:
=====
onconnect
=====

``[p] is your prefix.``

- ``[]`` means optional. 
- ``<>`` means required.

.. note ::

    Important note, this cog support slash command, once you sync the tree it will show up under ``/`` on discord.

.. note ::

    Please be aware that you cannot set events in thread, forum or voice text channels, this will not be available to work.

----
Usage
----
This cog sends shard events and can be extremely spammy sometimes, depending on how your connection to discord is or how your bot is having its time with the gateway. this is not anything you need to worry about, you just will see reconnections and disconnections, it'd take about a sec for it to connect back and it will repeat like that.

----
Commands
----
.. code-block:: none

    [p]connectset

**Description**:

Manage settings for onconnect.

.. note ::

    Leave blank to reset the events if you do not want it to post.

.. code-block:: none

    [p]connectset channel [#channel]

**Description**:

Set the channel to log shard events to.

.. code-block:: none

    [p]connectset emoji

**Description**:

Settting to change emojis.

.. code-block:: none

    [p]connectset emoji green [emoji_you_want]

**Description**:

Change the emoji green emoji.

.. code-block:: none

    [p]connectset emoji red [emoji_you_want]

**Description**:

Change the emoji red emoji.

.. code-block:: none

    [p]connectset emoji orange [emoji_you_want]

**Description**:

Change the emoji orange emoji.

.. code-block:: none

    [p]connectset showsettings

**Description**:

Shows the current settings for OnConnect.

----
Missing the cog?
----
1. Add the repo

.. code-block:: none

    [p]repo add maxcogs https://github.com/ltzmax/maxcogs

2. install the cog

.. code-block:: none

    [p]cog install maxcogs onconnect

3. load the cog

.. code-block:: none

    [p]load onconnect
