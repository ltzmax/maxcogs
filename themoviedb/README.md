Search for informations of movies and TV shows from themoviedb.org.

# [p]tmdbset
Configure TheMovieDB cog settings.<br/>
 - Usage: `[p]tmdbset`
 - Restricted to: `ADMIN`
## [p]tmdbset role
Set or unset a role to ping for new video notifications.<br/>
 - Usage: `[p]tmdbset role [role=None]`
## [p]tmdbset toggle
Toggle notifications for one or more studios, or all studios.<br/>

Use `[p]tmdbset list` to see available studios. Pass 'all' to toggle all studios,<br/>
or specify multiple studio names to toggle them at once.<br/>

**NOTE**:<br/>
Videos may include more than just trailers from movies or TV shows, they can also feature behind-the-scenes content or interviews. This is intended to keep you updated on new content from your favorite studios and channels.<br/>

**Examples**:<br/>
- `[p]tmdbset toggle marvel`<br/>
- `[p]tmdbset toggle netflix sony amazon`<br/>
- `[p]tmdbset toggle all`<br/>

**Arguments**:<br/>
- `<channel_names>`: One or more studio names to toggle, or 'all' to toggle all studios.<br/>
 - Usage: `[p]tmdbset toggle <channel_names>`
## [p]tmdbset creds
Guide to setting up the TMDB API key.<br/>

This command will give you information on how to set up the API key.<br/>
 - Usage: `[p]tmdbset creds`
 - Restricted to: `BOT_OWNER`
## [p]tmdbset channel
Set or unset the channel for video notifications.<br/>
 - Usage: `[p]tmdbset channel [channel=None]`
## [p]tmdbset list
List all available studios and their notification status.<br/>
 - Usage: `[p]tmdbset list`
# [p]movie (Hybrid Command)
Search for a movie.<br/>

You can write the full name of the movie to get more accurate results.<br/>

**Examples:**<br/>
- `[p]movie the dark knight`<br/>
- `[p]movie the lord of the rings`<br/>

**Arguments:**<br/>
- `<query>` - The movie you want to search for.<br/>
 - Usage: `[p]movie <query>`
 - Slash Usage: `/movie <query>`
 - Aliases: `movies`
# [p]tvshow (Hybrid Command)
Search for a TV show.<br/>

You can write the full name of the TV show to get more accurate results.<br/>

**Examples:**<br/>
- `[p]tv the office`<br/>
- `[p]tv game of thrones`<br/>

**Arguments:**<br/>
- `<query>` - The TV show you want to search for.<br/>
 - Usage: `[p]tvshow <query>`
 - Slash Usage: `/tvshow <query>`
 - Aliases: `tv`
# [p]person (Hybrid Command)
Search for a person.<br/>

You can write the full name of the person to get more accurate results.<br/>

**Examples:**<br/>
- `[p]person arthur`<br/>
- `[p]person johnny depp`<br/>

**Arguments:**<br/>
- `<query>` - The person you want to search for.<br/>
 - Usage: `[p]person <query>`
 - Slash Usage: `/person <query>`
