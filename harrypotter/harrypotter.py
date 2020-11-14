import discord
from redbot.core import commands

class HarryPotter(commands.Cog):
    """Cog that display about Harry potter."""

    __version__ = "0.1.0"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"
    
    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return    
    
    def __init__(self, bot):
        self.bot = bot

    # yes this could've been better. :P

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def stone(self, ctx):
        """Harry Potter and the Philosopher's Stone"""
        em = discord.Embed(title="Harry Potter and the Philosopher's Stone", colour=0x11FF00)
        em.description="**Release Date:** November 4, 2001.\n\nThis is the tale of Harry Potter (Daniel Radcliffe), an ordinary eleven-year-old boy serving as a sort of slave for his aunt and uncle who learns that he is actually a wizard and has been invited to attend the Hogwarts School for Witchcraft and Wizardry. Harry is snatched away from his mundane existence by Rubeus Hagrid (Robbie Coltrane), the groundskeeper for Hogwarts, and quickly thrown into a world completely foreign to both him and the viewer. Famous for an incident that happened at his birth, Harry makes friends easily at his new school. He soon finds, however, that the wizarding world is far more dangerous for him than he would have imagined, and he quickly learns that not all wizards are ones to be trusted."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def chamber(self, ctx):
        """Harry Potter and the Chamber of Secrets"""
        em = discord.Embed(title="Harry Potter and the Chamber of Secrets", colour=0x11FF00)
        em.description="**Release Date:** November 3, 2002.\n\nForced to spend his summer holidays with his muggle relations, Harry Potter (Daniel Radcliffe) gets a real shock when he gets a surprise visitor: Dobby (Toby Jones) the house-elf, who warns Harry against returning to Hogwarts, for terrible things are going to happen. Harry decides to ignore Dobby's warning and continues with his pre-arranged schedule. But at Hogwarts, strange and terrible things are indeed happening. Harry is suddenly hearing mysterious voices from inside the walls, muggle-born students are being attacked, and a message scrawled on the wall in blood puts everyone on his or her guard, `The Chamber Of Secrets Has Been Opened. Enemies Of The Heir, Beware.`"
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def prisoner(self, ctx):
        """Harry Potter and the Prisoner of Azkaban"""
        em = discord.Embed(title="Harry Potter and the Prisoner of Azkaban", colour=0x11FF00)
        em.description="**Release Date:** May 23, 2004.\n\nHarry Potter (Daniel Radcliffe) is having a tough time with his relatives (yet again). He runs away after using magic to inflate Uncle Vernon's (Richard Griffiths') sister Marge (Pam Ferris), who was being offensive towards Harry's parents. Initially scared for using magic outside the school, he is pleasantly surprised that he won't be penalized after all. However, he soon learns that a dangerous criminal and Voldemort's trusted aide Sirius Black (Gary Oldman) has escaped from Azkaban Prison and wants to kill Harry to avenge the Dark Lord. To worsen the conditions for Harry, vile creatures called Dementors are appointed to guard the school gates and inexplicably happen to have the most horrible effect on him. Little does Harry know that by the end of this year, many holes in his past (whatever he knows of it) will be filled up and he will have a clearer vision of what the future has in store."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def goblet(self, ctx):
        """Harry Potter and the Goblet of Fire"""
        em = discord.Embed(title="Harry Potter and the Goblet of Fire", colour=0x11FF00)
        em.description="**Release Date:** November 6, 2005.\n\nHarry's (Daniel Radcliffe's) fourth year at Hogwarts is about to start and he is enjoying the summer vacation with his friends. They get the tickets to The Quidditch World Cup Final, but after the match is over, people dressed like Lord Voldemort's (Ralph Fiennes') `Death Eaters` set a fire to all of the visitors' tents, coupled with the appearance of Voldemort's symbol, the `Dark Mark` in the sky, which causes a frenzy across the magical community. That same year, Hogwarts is hosting `The Triwizard Tournament`, a magical tournament between three well-known schools of magic : Hogwarts, Beauxbatons, and Durmstrang. The contestants have to be above the age of seventeen, and are chosen by a magical object called `The Goblet of Fire`. On the night of selection, however, the Goblet spews out four names instead of the usual three, with Harry unwittingly being selected as the Fourth Champion. Since the magic cannot be reversed, Harry is forced to go with it and brave three exceedingly..."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def phoenix(self, ctx):
        """Harry Potter and the Order of the Phoenix"""
        em = discord.Embed(title="Harry Potter and the Order of the Phoenix", colour=0x11FF00)
        em.description="**Release Date:** June 28, 2007.\n\nAfter a lonely summer on Privet Drive, Harry (Daniel Radcliffe) returns to a Hogwarts full of ill-fortune. Few of students and parents believe him or Dumbledore (Sir Michael Gambon) that Voldemort (Ralph Fiennes) is really back. The ministry had decided to step in by appointing a new Defense Against the Dark Arts teacher, Professor Dolores Umbridge (Imelda Staunton), who proves to be the nastiest person Harry has ever encountered. Harry also can't help stealing glances with the beautiful Cho Chang (Katie Leung). To top it off are dreams that Harry can't explain, and a mystery behind something for which Voldemort is searching. With these many things, Harry begins one of his toughest years at Hogwarts School of Witchcraft and Wizardry."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def prince(self, ctx):
        """Harry Potter and the Half-Blood Prince"""
        em = discord.Embed(title="Harry Potter and the Half-Blood Prince", colour=0x11FF00)
        em.description="**Release Date:** July 6, 2009.\n\nIn Harry Potter's (Daniel Radcliffe's) sixth year at Hogwarts School of Witchcraft, he finds a book marked mysteriously, `This book is the property of the Half Blood Prince`, which helps him excel at Potions class and teaches him a few dark and dangerous ones along the way. Meanwhile, Harry is taking private lessons with Dumbledore (Sir Michael Gambon) in order to find out about Voldemort's (Ralph Fiennes') past so they can find out what might be his only weakness."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def deathlyp1(self, ctx):
        """Harry Potter And The Deathly Hallows part 1"""
        em = discord.Embed(title="Harry Potter And The Deathly Hallows part 1", colour=0x11FF00)
        em.description="**Release Date:** November 11, 2010.\n\nVoldemort's (Ralph Fiennes') power is growing stronger. He now has control over the Ministry of Magic and Hogwarts. Harry (Daniel Radcliffe), Ron (Rupert Grint), and Hermione (Emma Watson) decide to finish Dumbledore's (Sir Michael Gambon's) work and find the rest of the Horcruxes to defeat the Dark Lord. But little hope remains for the trio, and the rest of the Wizarding World, so everything they do must go as planned."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def deathlyp2(self, ctx):
        """Harry Potter and the Deathly Hallows Part 2"""
        em = discord.Embed(title="Harry Potter and the Deathly Hallows Part 2", colour=0x11FF00)
        em.description="**Release Date:** July 7, 2011.\n\nHarry (Daniel Radcliffe), Ron (Rupert Grint), and Hermione (Emma Watson) continue their quest of finding and destroying Voldemort's (Ralph Fiennes') three remaining Horcruxes, the magical items responsible for his immortality. But as the mystical Deathly Hallows are uncovered, and Voldemort finds out about their mission, the biggest battle begins, and life as they know it will never be the same again."
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")