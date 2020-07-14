import discord
from redbot.core import commands

class PokeSeries(commands.Cog):
    """Cog that display about a season from pokemon and a movie."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "1.0.2"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"

        #For you that looks into the codes, yes i know it's pretty easy made.
        #i know i could have done it better than this, but as long as it works, there is nothing wrong with it, right?
        #You are free to PR it and do it better than me. :')

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke1"])
    async def indigo(self, ctx):
        """Pokemon Indigo league"""
        em = discord.Embed(title="Pokemon: Indigo league", colour=0x11FF00)
        em.description="[**Season:** 1](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Indigo_League_episodes)\n**Release Date:** April 1, 1997.\n**Episodes:** 82\n\nIt’s Ash Ketchum’s tenth birthday, and he’s ready to do what many 10-year-olds in the Kanto region set out to do—become a Pokémon Trainer! Things don’t go exactly the way he planned when he ends up with a Pikachu instead of a standard first Pokémon, and winning Gym Badges turns out to be much tougher than he thought. Luckily he’s got former Gym Leaders Brock and Misty at his side, along with a bevy of new Pokémon friends, including Bulbasaur, Squirtle, and Charmander."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke2"])
    async def islands(self, ctx):
        """Pokemon Adventures in the orange islands"""
        em = discord.Embed(title="Pokemon: Adventures in the orange islands", colour=0x11FF00)
        em.description="[**Season:** 2](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Adventures_in_the_Orange_Islands_episodes)\n**Release Date:** Jan 28, 1999.\n**Episodes:** 36\n\nAsh’s journey to the top of the Indigo League continues—but will his friendship with fellow Pokémon League competitor Richie endanger his chances? With his Kanto journey completed, Ash finds there’s still plenty to see and do when Professor Oak sends him and his friends to the Orange Islands. Brock falls head-over-heels for the attractive Professor Ivy and decides to stay with her, leaving Ash and Misty alone as a dynamic duo—at least until they meet intrepid Pokémon watcher Tracey Sketchit!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke3"])
    async def johto(self, ctx):
        """Pokemon The johto journeys"""
        em = discord.Embed(title="Pokemon: The johto journeys", colour=0x11FF00)
        em.description="[**Season:** 3](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_The_Johto_Journeys_episodes)\n**Release Date:** Oct 14 1999.\n**Episodes:** 41\n\nThe Orange League beckons and Ash answers the call, taking on the Orange Crew and their leader, Drake. Upon returning to Pallet Town, Ash and Misty reunite with Brock and set out on the next stage of their Pokémon journey—the Johto region! Though he still has an errand to run for Professor Oak, Ash jumps with both feet into the Johto League, taking on a couple of Gym Leaders and adding Pokémon like Totodile and Chikorita to his team."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke4"])
    async def champions(self, ctx):
        """pokemon Johto league champions"""
        em = discord.Embed(title="Pokemon: Johto league champions", colour=0x11FF00)
        em.description="[**Season:** 4](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Johto_League_Champions_episodes)\n**Release Date:** Aug 3, 2000.\n**Episodes:** 52\n\nFrom the sprawling metropolis of Goldenrod City to the icy peak of Snowtop Mountain, the Johto region presents Ash, Misty, and Brock with exciting new adventures—along with a few familiar faces like their old friends Todd, Duplica, and Suzie! Johto’s rich past means plenty of Pokémon mysteries for our heroes to solve, and its exciting present means some tough challenges—Ash tackles three more Gyms, while handling competitions like the Pokémon Sumo Conference along the way."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke5"])
    async def questmaster(self, ctx):
        """Pokemon Master quest"""
        em = discord.Embed(title="Pokemon: Master quest", colour=0x11FF00)
        em.description="[**Season:** 5](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Master_Quest_episodes)\n**Release Date:** Aug 9, 2001.\n**Episodes:** 65\n\nWith the Olivine City Gym temporarily out of commission, our heroes are off to the Whirl Cup Competition—and Misty wants in on the action! Resuming their journey, they find that Jessie, James, and Meowth aren’t the only members of Team Rocket they need to worry about, though that dastardly trio still has a few tricks up their collective sleeve. After a heated battle with the final Gym Leader, Ash moves on to the Silver Conference, but does he have the mettle to take on his old rival, Gary?"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke6"])
    async def advanced(self, ctx):
        """Pokemon: Advanced"""
        em = discord.Embed(title="Pokemon: Advanced", colour=0x11FF00)
        em.description="[**Season:** 6](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Advanced_episodes)\n**Release Date:** Nov 21, 2002.\n**Episodes:** 40\n\nPolishing off the Silver Conference, Ash heads toward his next challenge—the far-off Hoenn region! While he must say goodbye to old friends, he makes the acquaintance of May, a Trainer just starting out on her Pokémon journey. Along with her little brother Max and the ever-reliable Brock, this pack of Pokémon Trainers begin pursuing their dreams—with Ash racking up three Gym Badges, while May changes tack to follow the Contest path of a Pokémon Coordinator."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke7"])
    async def challenge(self, ctx):
        """Pokemon Advanced challenge"""
        em = discord.Embed(title="Pokemon: Advanced challenge", colour=0x11FF00)
        em.description="[**Season:** 7](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Advanced_Challenge_episodes)\n**Release Date:** Sep 4, 2003.\n **Episodes:** 52\n\nA shadow hovers over Ash, May, and friends as they continue their journey through the Hoenn region, and it’s not just that of Mt. Chimney—both Team Magma and Team Aqua put plans into action with our heroes caught in the middle! When not foiling evil schemes, Ash and May chase their personal goals, with Ash battling for three more Gym Badges and May winning her first three Contest Ribbons. The group also gains new Pokémon like Torkoal and Bulbasaur, but could they be too much to handle?"
        await ctx.send(embed=em)
    
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke8"])
    async def battle(self, ctx):
        """Pokemon Advanced battle"""
        em = discord.Embed(title="Pokemon: Advanced battle", colour=0x11FF00)
        em.description="[**Season:** 8](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Advanced_Battle_episodes)\n**Release Date:** Sep 9, 2004.\n**Episodes:** 53\n\nAsh earns his final two Badges and secures himself a spot in the Hoenn League Championships, while May comes dangerously close to not getting her final Ribbon—setting the stage for epic showdowns with both of her rivals in the Grand Festival. Ash meets two Trainers that become his own Hoenn rivals, facing off against both of them during the course of the tournament. Upon returning to Kanto and reuniting with old friends, Ash is recruited for a new challenge—the Battle Frontier!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke9"])
    async def frontier(self, ctx):
        """Pokemon Battle frontier"""
        em = discord.Embed(title="Pokemon: Battle frontier", colour=0x11FF00)
        em.description="[**Season:** 9](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Battle_Frontier_episodes)\n**Release Date:** Oct 5, 2005.\n**Episodes:** 57\n\nThe territory might be familiar, but even Ash and Brock can find more than a few surprises in their home region of Kanto, like a Pokémon Ranger hot on the cases of two Legendary Pokémon! May’s back on the Contest path, blazing a trail to the Kanto Grand Festival, while Ash seeks out the hidden facilities of the Battle Frontier. If finding them wasn’t hard enough, he’s still got battles with the Frontier Brains to deal with—much tougher than any Gym Leader he’s ever faced."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke10"])
    async def diamond(self, ctx):
        """Pokemon Diamond and pearel"""
        em = discord.Embed(title="Pokemon: Diamond and pearl", colour=0x11FF00)
        em.description="[**Season:** 10](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Diamond_and_Pearl:_Battle_Dimension_episodes)\n**Release Date:** Sep 28, 2006.\n**Episodes:** 52\n\nIf Gary Oak is headed for the Sinnoh region, then Ash Ketchum won’t be far behind! Ready to take on the Sinnoh League, Ash brings along Pikachu and meets up with Brock in Sinnoh, where the pair of Trainers are soon joined by a third—Dawn, a novice Pokémon Coordinator determined to follow in the footsteps of her mother. Both Ash and Dawn struggle with their respective paths, but it’s easy for them to make new friends, gaining new Pokémon like Turtwig and Piplup."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke11"])
    async def dpbattle(self, ctx):
        """Pokemon DP battle dimension"""
        em = discord.Embed(title="Pokemon: DP battle dimension", colour=0x11FF00)
        em.description="[**Season:** 11](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Diamond_and_Pearl:_Battle_Dimension_episodes)\n**Release Date:** Nov 8, 2007.\n**Episodes:** 49\n\nIt’s looking good for Ash as he works on his next three Gym Badges, but not so good for Dawn, coming off a pair of Contest defeats. Both will do what they can to become better Trainers, from entering the Wallace Cup competition to attending Professor Rowan’s Pokémon Summer Academy. Hopefully, the new tactics they pick up will give them the tools they need to succeed against the latest plot by Pokémon Hunter J—as well as the emerging threat of Team Galactic!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke12"])
    async def galactic(self, ctx):
        """Pokemon: DP galactic battle"""
        em = discord.Embed(title="Pokemon: DP galactic battle", colour=0x11FF00)
        em.description="[**Season:** 12](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Diamond_and_Pearl:_Galactic_Battles_episodes)\n**Release Date:** Dec 4, 2008.\n**Episodes:** 50\n\nAs the menace of Team Galactic continues to loom over the Sinnoh region, Ash and Dawn keep getting caught up in the schemes of this mysterious group of villains—as well as facing some other unexpected challenges! Dawn’s got her hands full dealing with the many problems of her Pokémon, while Ash’s ongoing rivalry with Paul finally comes to a head in a full 6-on-6 battle! It might be the ultimate test of training styles—will our heroes come out on top?"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke13"])
    async def sinnoh(self, ctx):
        """Pokemon DP sinnoh league victors"""
        em = discord.Embed(title="Pokemon: DP sinnoh league victors", colour=0x11FF00)
        em.description="[**Season:** 13](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Diamond_and_Pearl:_Sinnoh_League_Victors_episodes)\n**Release Date:** Jan 7, 2010.\n**Episodes:** 34\n\nWatch Ash, Dawn, and Brock travel across the Sinnoh region to face challenges, battles, and the antics of Team Rocket! With Team Galactic out of the way, Ash can now focus on qualifying for the Sinnoh League. And Dawn will train to compete for her final Contest Ribbon, which would allow her to compete in the Grand Festival!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke14"])
    async def shadow(self, ctx):
        """Pokemon Black and white"""
        em = discord.Embed(title="Pokemon: Black and white", colour=0x11FF00)
        em.description="[**Season:** 14](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Black_%26_White_episodes)\n**Release Date:** Sep 23, 2010.\n**Episodes:** 47\n\nA new land, new rivals, new challenges, and all-new Pokémon make the 14th season of the Pokémon animated series one of the most exciting ones yet! When Ash and his mother accompany Professor Oak to the distant Unova region, Ash discovers Pokémon that he’s never seen before… and that he can’t wait to catch! He may have Pikachu at his side together with new friends Iris and Cilan, but he’ll still need plenty of new Pokémon on his team if he wants to challenge Unova’s expert Gym Leaders. His quest to become a Pokémon Master just got even tougher!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke15"])
    async def rival(self, ctx):
        """Pokemon DW rival destinies"""
        em = discord.Embed(title="Pokemon: DW rival destinies", colour=0x11FF00)
        em.description="[**Season:** 15](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Black_%26_White:_Rival_Destinies_episodes)\n**Release Date:** Sep 22, 2011.\n**Episodes:** 49\n\nNew foes, new friends, and dozens of never-before-seen Pokémon await Ash and Pikachu in Pokémon: BW Rival Destinies, the new season of the Pokémon animated series. As Ash and his friends continue to explore the Unova region, he’ll find himself up against the ultimate battle challenge: Alder, the Champion Master of Unova! His friends also face their own trials, one fighting for the right to continue her travels, another confronting a returning challenge from the past—and all three of them must team up to save an island from the clashing forces of three powerful and mysterious Legendary Pokémon!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke16"])
    async def unova(self, ctx):
        """Pokemon DW adventures in unova and beyond"""
        em = discord.Embed(title="Pokemon: DW Adventures in unova and beyond", colour=0x11FF00)
        em.description="[**Season:** 16](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_Black_%26_White:_Adventures_in_Unova_and_Beyond_episodes)\n**Release Date:** Oct 11, 2012.\n**Episodes:** 45\n\nAsh and his friends Iris and Cilan have foiled Team Rocket’s latest evil plan, but a new danger lurks on the horizon! But first, with eight Gym badges in hand, Ash is ready to take on the region’s ultimate challenge: the Unova League, where he’ll face familiar rivals and new opponents in his ongoing quest to become a Pokémon Master! Meanwhile, Iris has been having some trouble connecting with her powerful and stubborn Dragonite—can a visit home to the Village of Dragons help sort things out for the aspiring Dragon Master? And what exciting new adventures await our heroes beyond the Unova League? The answers to come, as the journey continues!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke17"])
    async def xy(self, ctx):
        """Pokemon The serie XY"""
        em = discord.Embed(title="Pokemon: The serie XY", colour=0x11FF00)
        em.description="[**Season:** 17](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon:_XY_episodes)\n**Release Date:** Oct 17, 2013.\n**Episodes:** 49\n\nIt’s time for Ash and Pikachu to set off on their adventures in the Kalos region! Along the way, they’re joined by some new friends—a genius inventor named Clemont, his little sister Bonnie, and Serena, a Trainer on her first journey. Ash immediately tries to challenge the Gym in Lumiose City, but doesn’t get very far before a robot throws him out! In between Gym battles, Ash and friends will be exploring this unique region, meeting all kinds of new Pokémon, and looking into a fascinating new Pokémon mystery!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke18"])
    async def kalos(self, ctx):
        """Pokemon: The series XY Kalos Quest"""
        em = discord.Embed(title="Pokemon: The series XY Kalos Quest", colour=0x11FF00)
        em.description="[**Season:** 18](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_the_Series:_XY_Kalos_Quest_episodes)\n**Release Date:** Nov 9, 2014.\n**Episodes:** 49\n\nAsh and Pikachu continue their epic journey in the next exciting season of Pokémon the Series: XY Kalos Quest! While Ash continues his quest to win eight Gym badges so he can enter the Kalos League, he and his traveling companions will make new friends, forge new rivalries, and, of course, meet some brand-new Pokémon! Serena, with her partner Fennekin and new friend Pancham, will take on the Pokémon Showcase world; Clemont will continue to create inventions and hope some of them are a hit; and Bonnie, as ever, will try to find someone to take care of her big brother!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke19"])
    async def xyz(self, ctx):
        """Pokemon The serie XYZ"""
        em = discord.Embed(title="Pokemon: The serie XYZ", colour=0x11FF00)
        em.description="[**Season:** 19](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_the_Series:_XYZ_episodes)\n**Release Date:** Oct 29, 2015.\n**Episodes:** 47\n\nFollow Ash, Pikachu, and their friends as they explore the deepest mysteries of the Kalos region! Team Flare has plans for the Legendary Pokémon Zygarde and the secret it holds. Alain’s ongoing search for the source of Mega Evolution intersects with our heroes’ adventures. And true to Gym Leader Olympia’s prediction, Ash and his Frogadier will work together to reach surprising new heights! Journey into uncharted territory with this exciting season of Pokémon animation!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke20"])
    async def moon(self, ctx):
        """Pokemon the serie sun and moon"""
        em = discord.Embed(title="Pokemon: The serie sun and moon", colour=0x11FF00)
        em.description="[**Season:** 20](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_the_Series:_Sun_%26_Moon_episodes)\n**Release Date:** Nov 17, 2016.\n**Episodes:** 43\n\nWhat starts as a summer vacation in the tropical Alola region turns into the next exciting chapter in Ash Ketchum’s quest to become a Pokémon Master! There’s plenty for Ash and Pikachu to explore in this sunny new region, with exciting new Pokémon to discover and interesting people to learn from along the way—including the cool Professor Kukui and the fun-loving Samson Oak. More new faces will help guide Ash’s Alolan adventure, in the form of a group of skilled Trainers—Kiawe, Lana, Mallow, and Sophocles—and a mysterious research assistant called Lillie. Frequent foes Team Rocket have also made the trip to Alola, looking to swipe some high-powered new Pokémon. But they have some heavy competition on the villainy front: the ruffians of Team Skull, who delight in causing chaos and may have more sinister intentions…"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke21"])
    async def ultramoon(self, ctx):
        """Pokemon the serie ultra sun and moon"""
        em = discord.Embed(title="Pokemon: The serie ultra sun and moon adventures", colour=0x11FF00)
        em.description="[**Season:** 21](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_the_Series:_Sun_%26_Moon_%E2%80%93_Ultra_Adventures_episodes)\n**Release Date:** Oct 5, 2017.\n**Episodes:** 48\n\nWhen Ash sees the Legendary Pokémon Solgaleo and Lunala in a dream, he makes a promise to them. But when he wakes up, he can’t remember what it was! Will the strange Pokémon called Nebby help jog his memory? Along with their new friend and the rest of the students at the Pokémon School, Ash and Pikachu explore the Aether Foundation, an organization dedicated to Pokémon conservation and care. But it may not be as innocent as it seems, and Ash and his friends will have to work together to protect the people and Pokémon they care about as they face a mysterious power like nothing they have ever seen."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["poke22"])
    async def legends(self, ctx):
        """Pokemon the serie sun and moon ultra lengeds"""
        em = discord.Embed(title="Pokemon: The series sun and moon ultra legends", colour=0x11FF00)
        em.description="[**Season:** 22](https://en.wikipedia.org/wiki/List_of_Pok%C3%A9mon_the_Series:_Sun_%26_Moon_%E2%80%93_Ultra_Legends_episodes)\n**Release Date:** Oct 21, 2018.\n**Episodes:** 54\n\nAsh has completed three of his four grand trials in the Alola region, and more adventures await as he and his classmates acquire new Z-Crystals, make new Pokémon friends, and learn how to Mantine Surf! In their role as Ultra Guardians, the Pokémon School students take on an important mission to protect Wela Volcano. Ash meets a new rival, Hau, whose Dartrix offers Rowlet quite a challenge. Even Rotom Dex gets an adventure of its own when our heroes visit the set of its favorite TV show! And Professor Kukui's dream of starting a Pokémon League in Alola just might be getting closer to reality.."
        await ctx.send(embed=em)
    
    # here starts all the movies from pokemon below.

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem1"])
    async def strikes(self, ctx):
        """Pokemon the first movie: Mewtow strikes back"""
        em = discord.Embed(title="Pokemon The first movie: Mewtwo strikes back", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon:_The_First_Movie) July 18, 1998\n\nThe adventure explodes into action with the debut of Mewtwo, a bio-engineered Pokémon created from the DNA of Mew, one of the rarest Pokémon of all. After escaping from the lab where it was created, Mewtwo is determined to prove its own superiority. It lures a number of talented Trainers into a Pokémon battle like never before—and of course, Ash and his friends are happy to accept the challenge!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem2"])
    async def power(self, ctx):
        """Pokemon the movie 2000: The power of one"""
        em = discord.Embed(title="Pokemon The movie 2000: The power of one", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon:_The_Movie_2000) July 17, 1999\n\nAsh and his friends are on their journey through the Orange Islands—but even this seemingly quiet chain of islands dotted throughout the waters far south of Kanto has its own mysteries, adventures, and Legendary Pokémon! Lawrence III certainly knows it, which is why he's now traveling to the different islands and capturing the three Legendary birds—Moltres, Articuno, and Zapdos. But even with all their power, those three are merely a stepping stone to an even greater prize: Lugia, the guardian of the sea!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem3"])
    async def entei(self, ctx):
        """Pokemon 3 The movie Entei"""
        em = discord.Embed(title="Pokemon The movie entei", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_3:_The_Movie) July 8, 2000\n\nA crystal catastrophe is unleased upon Greenfield, and Ash, Pikachu, and friends must figure out how to undo the damage to the once-beautiful town. But the unthinkable happens when Ash’s mom is kidnapped by the powerful Entei, a Pokémon thought to have existed only in legend. Now Ash must go to her rescue, uncertain of what he’ll uncover when he unlocks the real secret power behind the unbelievable turn of events: a young girl whose dream world is being turned into a nightmarish reality by the mysterious and unstoppable Unown!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem4"])
    async def celebi(self, ctx):
        """Pokemon 4Ever Celebi"""
        em = discord.Embed(title="Pokemon 4Ever: Celebi", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_4Ever) July 7, 2001\n\nThere are always those who seek to contain and capture rare Pokémon—and there are those who would protect these special Pokémon from evil forces. Forty years ago that very thing occurred when Celebi found itself fleeing a vicious hunter, and a young Trainer named Sammy rushed to the rescue. They vanished—becoming yet another strange legend that the townspeople tell."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem5"])
    async def heroes(self, ctx):
        """Pokemon Heroes Latios and Latias"""
        em = discord.Embed(title="Pokemon Heroes: Latios and Latias", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_Heroes) July 13, 2002\n\nAsh gets a special peek into the secret world of Latios and Latias, but this world is soon threatened by the two women from before—Annie and Oakley—who are after the two Legendary Pokémon, as well as a mysterious jewel called the Soul Dew. These elements combined will let them control a powerful machine that normally protects against danger. When the machine malfunctions, though, it not only puts Latios and Latias at serious risk, but the entire city of Alto Mare!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem6"])
    async def jirachi(self, ctx):
        """Pokemon Jirachi Wish Maker"""
        em = discord.Embed(title="Pokemon: Jirachi Wish Maker", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon:_Jirachi%E2%80%94Wish_Maker) July 19, 2003\n\nThe Millennium Comet is about to make its long-awaited appearance in the sky again, supposedly granting the wishes of all those who see it in the skies above them. Of course, Ash and friends are equally interested in the Millennium Festival, especially when they attend a magic performance by the Great Butler. Even more interesting is the mysterious cocoon in Butler’s possession—from which Max hears a mysterious voice calling! When Jirachi emerges from its slumber, Max has a new friend—sadly, it’s only for the brief few days that the Millennium Comet appears in the sky."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem7"])
    async def deoxys(self, ctx):
        """Pokemon Destiny Deoxys"""
        em = discord.Embed(title="Pokemon: Destiny Deoxys", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon:_Destiny_Deoxys) July 14, 2004\n\nThere's a lot more to be frightened by when Deoxys shows up and takes control of the city, shutting down the machines and taking everyone captive. One Pokémon that is not amused is the Legendary Rayquaza, and it will do whatever it takes to remove this invader from its territory! Meanwhile, Ash, Tory, and all their friends may be caught in the middle, but they're certainly not out of the fight!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem8"])
    async def lucario(self, ctx):
        """Pokemon Lucario and the Mystery of Mew"""
        em = discord.Embed(title="Pokemon: Lucario and the Mystery of Mew", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon:_Lucario_and_the_Mystery_of_Mew) July 16, 2005\n\nHundreds of years ago, Camaron Palace and its people were saved by the noble sacrifice of Sir Aaron, an Aura Knight. From that day forward the people have always honored his deeds with an annual festival. Of course, Ash isn't really much of a history buff—he's more interested in the Pokémon competition being held! Only when he wins and is asked to don the ceremonial role of Aura Guardian does Aaron's importance become clear—especially when Lucario emerges from Aaron's staff! Aaron isn't a hero to this long-dormant Pokémon—all Lucario remembers is the master that betrayed it!"
        await ctx.send(embed=em)
    
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem9"])
    async def ranger(self, ctx):
        """Pokemon Ranger and the Temple of the Sea"""
        em = discord.Embed(title="Pokemon Ranger and the Temple of the Sea", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_Ranger_and_the_Temple_of_the_Sea) July 15, 2006\n\nThere's a legend out there, about a Sea Temple created by the People of the Water, where the Sea Crown is kept. No one has ever seen this Sea Crown, and very few people even know the story of the temple, except a few members of the People of the Water who wander through the Pokémon world. That all changes when a Pokémon Ranger named Jackie rescues a Manaphy Egg from a greedy pirate named Phantom! Phantom is absolutely determined to snatch the Sea Crown, and he'll need Manaphy to get to it. To stay one step ahead, Jackie will need to enlist the help of the People of the Water."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem10"])
    async def reshiram(self, ctx):
        """Pokemon the Movie: Black-Victini and Reshiram"""
        em = discord.Embed(title="Pokemon the Movie: Black-Victini and Reshiram", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Black%E2%80%94Victini_and_Reshiram_and_White%E2%80%94Victini_and_Zekrom) July 16, 2011\n\nDuring their travels through the Unova region, Ash and his friends Iris and Cilan arrive in Eindoak Town, built around a castle called the Sword of the Vale. The three Trainers have come to compete in the town’s annual battle competition, and Ash manages to win with some unexpected help from the Mythical Pokémon Victini! It turns out Victini has a special bond with this place...\n\n[Pokemon Victini and Reshiram and White](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Black%E2%80%94Victini_and_Reshiram_and_White%E2%80%94Victini_and_Zekrom=)"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem11"])
    async def justice(self, ctx):
        """Pokemon the Movie: Kyurem vs the Sword of Justice"""
        em = discord.Embed(title="Pokemon the Movie: Kyurem vs the Sword of Justice", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Kyurem_vs._the_Sword_of_Justice) July 14, 2012\n\nAsh and Pikachu, along with their friends Iris and Cilan, are on a train headed to the next stop on their journey. From the train, Ash spots an injured Pokémon—one he’s never seen before. He’s trying to figure out how he can help when the train is attacked by the Legendary Kyurem, a Dragon-type Pokémon with immense power! Ash and the others barely manage to escape the rampaging Kyurem’s attack, and as the dust settles, they turn their attention to the injured Pokémon. Their new acquaintance turns out to be the Mythical Pokémon Keldeo, and it’s on a mission to rescue its friends—Cobalion, Terrakion, and Virizion, the Legendary Pokémon known as the Swords of Justice—from Kyurem’s icy clutches!"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem12"])
    async def genesect(self, ctx):
        """Pokemon The Movie: Genesect And The Legend Awakened"""
        em = discord.Embed(title="Pokemon The Movie: Genesect And The Legend Awakened", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Genesect_and_the_Legend_Awakened) July 13, 2013\n\nA vast Pokémon habitat amid the hustle and bustle of the big city seems like the perfect new home for a group of five Genesect. The arrival of these Mythical Pokémon quickly becomes a problem, though: their nest threatens the city’s power supply, and they keep attacking anyone who approaches it. On top of that, they’ve attracted the attention of the Legendary Pokémon Mewtwo, who sympathizes with them because its own origins also involve human tampering. The group’s leader, known as Red Genesect, doesn’t trust Mewtwo, and their confrontation quickly rages out of control! Can Ash and friends stop these two powerful Pokémon before they destroy the city?"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem13"])
    async def diancie(self, ctx):
        """Pokemon the Movie: Diancie and the Cocoon of Destruction"""
        em = discord.Embed(title="Pokemon the Movie: Diancie and the Cocoon of Destruction", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Diancie_and_the_Cocoon_of_Destruction) July 19, 2014\n\nIn a country called Diamond Domain lies the powerful Heart Diamond which has served as the kingdom's source of energy and maintained it for centuries. Many Carbink live in Diamond Domain, including their princess - the Jewel Pokemon Diancie, who created the Heart Diamond. Diancie no longer has the power to control the Heart Diamond and her country is falling into chaos as a result."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem14"])
    async def hoopa(self, ctx):
        """Pokemon the Movie: Hoopa and the Clash of Ages"""
        em = discord.Embed(title="Pokemon the Movie: Hoopa and the Clash of Ages", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Hoopa_and_the_Clash_of_Ages) July 18, 2015\n\nWhen Ash, Pikachu, and their friends visit a desert city by the sea, they meet the Mythical Pokemon Hoopa, who is able to summon things - including people and Pokemon - through its magic ring. After a scary incident, they learn a story about a brave hero who stopped the rampage of a terrifying Pokemon long ago. Now, that Pokemon is in danger of breaking loose again! Can Ash help overcome the darkness within - or will a dangerous secret erupt into a clash of legends?"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem15"])
    async def volcanion(self, ctx):
        """Pokemon the Movie: Volcanion and the Mechanical Marvel"""
        em = discord.Embed(title="Pokemon the Movie: Volcanion and the Mechanical Marvel", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_Volcanion_and_the_Mechanical_Marvel) July 16, 2016\n\nAsh meets the mythical Pokémon Volcanion when it crashes down from the sky, and a mysterious force binds the two of them together. Volcanion despises humans and tries to get away, but it's forced to drag Ash along as it continues its rescue mission."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem16"])
    async def pikachu(self, ctx):
        """Pokemon the Movie: I Choose You!"""
        em = discord.Embed(title="Pokemon the Movie: I Choose You", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_I_Choose_You!) July 15, 2017\n\nAsh Ketchum from Pallet Town is 10 years old today. This means he is now old enough to become a Pokémon Trainer. Ash dreams big about the adventures he will experience after receiving his first Pokémon from Professor Oak."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem17"])
    async def pokepower(self, ctx):
        """Pokemon the Movie: The Power of Us"""
        em = discord.Embed(title="Pokemon the Movie: The Power of Us", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Pok%C3%A9mon_the_Movie:_The_Power_of_Us) July 13, 2018\n\nThe festival celebrates the Legendary Pokémon Lugia, who brings the wind that powers this seaside city. When a series of threats endangers not just the festival, but all the people and Pokémon of Fula City, it’ll take more than just Ash and Pikachu to save the day! Can everyone put aside their differences and work together—or will it all end in destruction?"
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem18"])
    async def evolution(self, ctx):
        """Mewtwo Strikes Back: Evolution"""
        em = discord.Embed(title="Mewtwo Strikes Back: Evolution", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Mewtwo_Strikes_Back:_Evolution) July 4, 2019\n\nAfter a scientific experiment leads to the creation of a clone of Mewtwo, he sets out to destroy the world. Ash and his friends then decide to thwart Mewtwo's evil plans."
        await ctx.send(embed=em)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["pokem19"])
    async def detective(self, ctx):
        """Detective Pikachu"""
        em = discord.Embed(title="Detective Pikachu", colour=0x11FF00)
        em.description="[**Release Date:**](https://en.wikipedia.org/wiki/Detective_Pikachu_(film) May 3, 2019.\n\nThe story begins when ace detective Harry Goodman goes mysteriously missing, prompting his 21-year-old son Tim to find out what happened. Aiding in the investigation is Harry's former Pokémon partner, Detective Pikachu: a hilariously wise-cracking, adorable super-sleuth who is a puzzlement even to himself. Finding that they are uniquely equipped to communicate with one another, Tim and Pikachu join forces on a thrilling adventure to unravel the tangled mystery. Chasing clues together through the neon-lit streets of Ryme City--a sprawling, modern metropolis where humans and Pokémon live side by side in a hyper-realistic live-action world--they encounter a diverse cast of Pokémon characters and uncover a shocking plot that could destroy this peaceful co-existence and threaten the whole Pokémon universe."
        await ctx.send(embed=em)