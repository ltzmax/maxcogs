# Pokemon

This is pokemon related stuff cog.<br/><br/>- Can you guess Who's That Pokémon?<br/>- Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).<br/>- Get information about a Pokémon.

## [p]pokeinfo (Hybrid Command)

Get information about a Pokémon.<br/>

**Example:**<br/>
- `[p]pokeinfo pikachu` - returns information about Pikachu.<br/>

**Arguments:**<br/>
- `<pokemon>` - The Pokémon to search for.<br/>

 - Usage: `[p]pokeinfo <pokemon>`
 - Slash Usage: `/pokeinfo <pokemon>`
 - Cooldown: `1 per 5.0 seconds`

## [p]tcgcard (Hybrid Command)

Fetch Pokémon cards based on Pokémon Trading Card Game (a.k.a Pokémon TCG).<br/>

**Example:**<br/>
- `[p]tcgcard pikachu` - returns information about pikachu's cards.<br/>

**Arguments:**<br/>
- `<query>` - The pokemon you want to search for.<br/>

 - Usage: `[p]tcgcard <query>`
 - Slash Usage: `/tcgcard <query>`
 - Cooldown: `1 per 5.0 seconds`

## [p]whosthatpokemon (Hybrid Command)

Guess Who's that Pokémon in 30 seconds!<br/>

You can optionally specify generation from `gen1` to `gen9` only.<br/>

**Example:**<br/>
- `[p]whosthatpokemon` - This will start a new Generation.<br/>
- `[p]whosthatpokemon gen1` - This will pick any pokemon from generation 1 for you to guess.<br/>

**Arguments:**<br/>
- `[generation]` - Where you choose any generation from gen 1 to gen 9.<br/>

 - Usage: `[p]whosthatpokemon [generation=None]`
 - Slash Usage: `/whosthatpokemon [generation=None]`
 - Aliases: `wtp`
 - Cooldown: `1 per 30.0 seconds`

