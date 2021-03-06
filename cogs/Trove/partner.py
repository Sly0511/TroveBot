# Priority: 1

from discord.ext import commands
from utils.CustomObjects import CEmbed


class Partner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(slash_command=True, name="calendar", aliases=["events"], help="Check out Trovesaurus calendar.")
    async def _show_events(self, ctx):
        request = await self.bot.AIOSession.get("https://trovesaurus.com/calendar/feed")
        calendar = await request.json()
        e = CEmbed(color=0x2a5757)
        e.description = f"You can check current and upcoming events at [Trovesaurus](https://trovesaurus.com/calendar/new)"
        e.set_author(name="Trovesaurus Calendar", icon_url="https://trovesaurus.com/images/logos/Sage_64.png?1")
        if calendar:
            calendar.sort(key= lambda x: x["enddate"])
            e.set_thumbnail(url=calendar[0]["icon"])
            for event in calendar:
                url = f"https://trovesaurus.com/event={event['id']}"
                name = event["name"]
                category = event["category"]
                start, end = event["startdate"], event["enddate"]
                e.add_field(name=f"{category}: {name}", value=f"[About this event]({url})\nStarted on <t:{start}:F>\nEnds <t:{end}:R>", inline=False)
        else:
            e.description += "\n\nNo Events are happening at the time."
        await ctx.reply(embed=e)

def setup(bot):
    bot.add_cog(Partner(bot))
