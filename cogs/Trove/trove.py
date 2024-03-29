# Priority: 2
import asyncio
import re
from datetime import datetime, timedelta
from typing import Literal

import discord
import utils.checks as perms
from bs4 import BeautifulSoup
from discord.ext import commands
from utils.CustomObjects import CEmbed
from io import BytesIO


class Trove(commands.Cog):
#--------------- Module Management --------------#
    def __init__(self, bot):
        self.bot = bot
        self.bot.Trove.luxion_inventory = {}

#--------------- Events----------------#

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        ctx = await self.bot.get_context(message)
        # Notifications channel message clearing
        if ctx.channel.id == 812762716908552272 and not ctx.valid and not ctx.author.id == self.bot.user.id:
            return await message.delete()
        # Feedback channel message clearing
        if ctx.channel.id == 859433409016496128 and not ctx.author.bot:
            await ctx.send("Use command retard...", delete_after=10)
            return await message.delete()

#--------------- Commands --------------#
 # Other Commands

    @commands.command(slash_command=True, name="betterdiscord", aliases=["bbd"], help="Show code for better discord game tags.")
    async def _better_discord(self, ctx):
        e = CEmbed(description="Go to Custom CSS tab in your settings and then paste the following line onto it.```css\n@import url('https://trove.slynx.xyz/gametags');```**Hit update and save.**", color=discord.Color.random())
        e.set_author(name="Better Discord Trove Tags", icon_url=self.bot.user.avatar)
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Display server time and next reset", aliases=["time", "stime"])
    async def server_time(self, ctx):
        today = self.bot.Trove.time.now
        time = today.isoformat().split('T')[1][:5]
        dreset = int((today + timedelta(days=1, hours=-today.hour+11, minutes=-today.minute, seconds=-today.second, microseconds=today.microsecond)).timestamp())
        wreset = int((today + timedelta(days=7-today.weekday(), hours=-today.hour+11, minutes=-today.minute, seconds=-today.second, microseconds=today.microsecond)).timestamp())
        text = f"🕐 Server Time {time}\nNext daily reset <t:{dreset}:R> <t:{dreset}:F>\nNext weekly reset <t:{wreset}:R> <t:{wreset}:F>"
        daily = self.bot.Trove.daily_data[str(self.bot.Trove.time.now.weekday())]
        weekly = self.bot.Trove.weekly_data[str(self.bot.Trove.time.weekly_time)]
        e = CEmbed(description=text, color=self.bot.comment)
        e.add_field(name="Daily Bonus", value=f"\\{daily['emoji']}{daily['name']}")
        e.add_field(name="Weekly Bonus", value=f"\\{weekly['emoji']}{weekly['name']}")
        if self.bot.Trove.time.is_luxion or self.bot.Trove.time.is_corruxion:
            dragon = "Luxion is in hub" if self.bot.Trove.time.is_luxion else "Corruxion is in hub"
            e.add_field(name="Dragon Merchant", value=dragon)
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Display maximum Trove Mastery in PC Trove.", aliases=["m"])
    async def mastery(
        self,
        ctx,
        mode: Literal["live", "pts", "console"]=commands.Option(name="server", default=None, description="Pick a server."),
        update=commands.Option(name="value", default=None, description="Amount to update mastery with.")):
        if mode == None:
            e=CEmbed(color=self.bot.comment, timestamp=datetime.utcfromtimestamp((await self.bot.db.db_bot.find_one({"_id": "0511"}))["mastery"]["mastery_update"]))
            e.set_author(name="Trove Max Mastery", icon_url="https://i.imgur.com/t5aCX3u.png")
            live_level, live_points, live_level_points = self.bot.utils.points_to_mr(self.bot.Trove.max_live_mastery)
            pts_level, pts_points, pts_level_points = self.bot.utils.points_to_mr(self.bot.Trove.max_pts_mastery)
            console_level, console_points, console_level_points = self.bot.utils.points_to_mr(self.bot.Trove.max_console_mastery)
            live_text = f"\nLevel: **{live_level}**"
            pts_text = f"\nLevel: **{pts_level}**"
            console_text = f"\nLevel: **{console_level}**"
            if live_points > 0:
                live_text += f"\nExtra Points: **{live_points}**"
            if pts_points > 0:
                pts_text += f"\nExtra Points: **{pts_points}**"
            if console_points > 0:
                console_text += f"\nExtra Points: **{console_points}**"
            e.add_field(name="Live Maximum", value=f"Total Points: **{self.bot.Trove.max_live_mastery}**{live_text}\nMax PR: **{self.bot.Trove.values.max_pr(live_level - 500)}**" + f"\n{self.bot.utils.progress_bar(live_level_points, live_points, 20)}")
            e.add_field(name="PTS Maximum", value=f"Total Points: **{self.bot.Trove.max_pts_mastery}**{pts_text}\nMax PR: **{self.bot.Trove.values.max_pr(pts_level - 500, True)}**" + f"\n{self.bot.utils.progress_bar(pts_level_points, pts_points, 20)}")
            e.add_field(name="Console Maximum", value=f"Total Points: **{self.bot.Trove.max_console_mastery}**{console_text}\nMax PR: **{self.bot.Trove.values.max_pr(console_level - 500, False, True)}**" + f"\n{self.bot.utils.progress_bar(console_level_points, console_points, 20)}")
            e.set_footer(text="Last updated on")
            await ctx.send(embed=e)
            return
        if ctx.author.id in [562659821476773942] and mode == "console":
            ...
        elif ctx.author.id in [237634733264207872, 565097923025567755, 209712946534809600, 254602899038928897]:
            ...
        else:
            return
        if mode.lower() == "live":
            db = "mastery.max_live_mastery"
        elif mode.lower() == "pts":
            db = "mastery.max_pts_mastery"
        elif mode.lower() == "console":
            db = "mastery.max_console_mastery"
        else:
            await ctx.send("Invalid server!")
            return
        try:
            value = int(update)
        except:
            return await ctx.send("Invalid value!")
        if update.isdigit():
            await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set": {db: value, "mastery.mastery_update": datetime.utcnow().timestamp()}})
            await ctx.send(f"**{mode.capitalize()}** Max Mastery was set to **{value}**", ephemeral=True)
        else:
            if value > 0:
                await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$inc": {db: value}, "$set":{"mastery.mastery_update": datetime.utcnow().timestamp()}})
                await ctx.send(f"Added **{value}** to **{mode.capitalize()} Max Mastery**", ephemeral=True)
            else:
                await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$inc": {db: value}, "$set":{"mastery.mastery_update": datetime.utcnow().timestamp()}})
                await ctx.send(f"Removed **{value}** from **{mode.capitalize()} Max Mastery**", ephemeral=True)
        db_bot = await self.bot.db.db_bot.find_one({"_id": "0511"})
        self.bot.Trove.max_live_mastery = db_bot["mastery"]["max_live_mastery"]
        self.bot.Trove.max_console_mastery = db_bot["mastery"]["max_console_mastery"]
        difference = self.bot.Trove.max_live_mastery - db_bot["mastery"]["max_pts_mastery"]
        if difference > 0 and mode.lower() == "live":
            await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$inc": {"mastery.max_pts_mastery": difference}})
            db_bot = await self.bot.db.db_bot.find_one({"_id": "0511"})
        self.bot.Trove.max_pts_mastery = db_bot["mastery"]["max_pts_mastery"]
    
    async def _update_trovesaurus_mr(self, name, mastery):
        payload = {
            "SetMaxMastery": "",
            "Key": self.bot.keys["Trovesaurus"]["MasteryToken"],
            "Score": str(mastery),
            "Name": name
        }
        await self.bot.AIOSession.post("https://trovesaurus.com/", data=payload)

    @commands.command(slash_command=True, help="Display maximum Geode Mastery in PC Trove.", aliases=["mg", "gm"])
    async def mastery_geode(
        self,
        ctx,
        mode: Literal["live", "pts", "console"]=commands.Option(name="server", default=None, description="Pick a server."),
        update=commands.Option(name="value", default=None, description="Amount to update mastery with.")):
        if mode == None:
            e=CEmbed(color=self.bot.comment, timestamp=datetime.utcfromtimestamp((await self.bot.db.db_bot.find_one({"_id": "0511"}))["mastery"]["geode_mastery_update"]))
            e.set_author(name="Geode Max Mastery", icon_url="https://i.imgur.com/mJRDFtT.png")
            live_level, live_points, live_level_points = self.bot.utils.points_to_mr(self.bot.Trove.max_live_mastery_geode)
            pts_level, pts_points, pts_level_points = self.bot.utils.points_to_mr(self.bot.Trove.max_pts_mastery_geode)
            console_level, console_points, console_level_points = self.bot.utils.points_to_mr(self.bot.Trove.max_pts_mastery_geode)
            live_text = f"\nLevel: 100 ||(**{live_level}**)||"
            pts_text = f"\nLevel: 100 ||(**{pts_level}**)||"
            console_text = f"\nLevel: 100 ||(**{console_level}**)||"
            if live_points > 0:
                live_text += f"\nExtra Points: **{live_points}**"
            if pts_points > 0:
                pts_text += f"\nExtra Points: **{pts_points}**"
            if console_points > 0:
                console_text += f"\nExtra Points: **{console_points}**"
            e.add_field(name="Live Maximum", value=f"Total Points: **{self.bot.Trove.max_live_mastery_geode}**{live_text}" + f"\n{self.bot.utils.progress_bar(live_level_points, live_points, 20)}")
            e.add_field(name="PTS Maximum", value=f"Total Points: **{self.bot.Trove.max_pts_mastery_geode}**{pts_text}" + f"\n{self.bot.utils.progress_bar(pts_level_points, pts_points, 20)}")
            e.add_field(name="Console Maximum", value=f"Total Points: **{self.bot.Trove.max_console_mastery_geode}**{console_text}" + f"\n{self.bot.utils.progress_bar(console_level_points, console_points, 20)}")
            e.set_footer(text="Last updated on")
            await ctx.send(embed=e)
            return
        if ctx.author.id in [562659821476773942] and mode == "console":
            ...
        elif ctx.author.id in [237634733264207872, 565097923025567755, 209712946534809600, 254602899038928897]:
            ...
        else:
            return
        if mode.lower() == "live":
            db = "mastery.max_live_mastery_geode"
        elif mode.lower() == "pts":
            db = "mastery.max_pts_mastery_geode"
        elif mode.lower() == "console":
            db = "mastery.max_console_mastery_geode"
        else:
            await ctx.send("Invalid server!")
            return
        if update.lower().startswith("+"):
            try:
                value = int(update)
            except:
                await ctx.send("Invalid value!")
                return
            await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$inc": {db: value}, "$set":{"mastery.geode_mastery_update": datetime.utcnow().timestamp()}})
            await ctx.send(f"Added **{value}** to **{mode.capitalize()} Max Geode Mastery**", delete_after=8, ephemeral=True)
        elif update.lower().startswith("-"):
            try:
                value = int(update)
            except:
                await ctx.send("Invalid value!")
                return
            await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$inc": {db: value}, "$set":{"mastery.geode_mastery_update": datetime.utcnow().timestamp()}})
            await ctx.send(f"Removed **{value}** from **{mode.capitalize()} Max Geode Mastery**", delete_after=8,  ephemeral=True)
        else:
            try:
                value = int(update)
            except:
                await ctx.send("Invalid value!")
                return
            await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set": {db: value, "mastery.geode_mastery_update": datetime.utcnow().timestamp()}})
            await ctx.send(f"**{mode.capitalize()}** Max Geode Mastery was set to **{value}**", delete_after=8,  ephemeral=True)
        db_bot = await self.bot.db.db_bot.find_one({"_id": "0511"})
        self.bot.Trove.max_live_mastery_geode = db_bot["mastery"]["max_live_mastery_geode"]
        self.bot.Trove.max_console_mastery_geode = db_bot["mastery"]["max_console_mastery_geode"]
        if self.bot.Trove.max_live_mastery_geode > db_bot["mastery"]["max_pts_mastery_geode"]:
            await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$inc": {"mastery.max_pts_mastery_geode": self.bot.Trove.max_live_mastery_geode - db_bot["mastery"]["max_pts_mastery_geode"]}})
            db_bot = await self.bot.db.db_bot.find_one({"_id": "0511"})
        self.bot.Trove.max_pts_mastery_geode = db_bot["mastery"]["max_pts_mastery_geode"]

    @commands.command(slash_command=True, help="Shows when luxion is around and it's inventory.", aliases=["lux"])
    async def luxion(self, ctx):
        if self.bot.Trove.time.is_luxion:            
            initial_id = 84
            initial_id += int(self.bot.Trove.time.luxion_time[1])
            if not self.bot.Trove.luxion_inventory.get(str(initial_id)):
                msg = await ctx.send("<a:loading:844624767239192576> Looking for inventory in <https://trovesaurus.com/luxion>", delete_after=5)
                await asyncio.sleep(3)
                self.bot.Trove.luxion_inventory[str(initial_id)] = []
                trovesaurus = await (await self.bot.AIOSession.get(f"https://trovesaurus.com/luxion/visit/{initial_id}")).text()
                soup = BeautifulSoup(trovesaurus, "html.parser")
                data = soup.findAll("div", {"class": "navbar-secondary border"})
                if not data:
                    try:
                        await msg.delete()
                    except:
                        ...
                    return await ctx.send(f"Luxion is available. It will be gone {self.bot.Trove.time.luxion_end_rwts('R')}, yet inventory couldn't be fetched, try again later.")
                items = []
                for d in data:
                    d = d.parent
                    item = {}
                    item["name"] = d.find("a").getText().strip()
                    item["link"] = d.find("a")["href"]
                    item["price"] = int(d.find("p").getText().strip())
                    limit = d.find("span", {"class": "text-muted"})
                    if limit:
                        text = limit.getText()
                        limit = int(re.findall(r"([0-9]+)", text)[0])
                    item["limit"] = str(limit)
                    item_page = await (await self.bot.AIOSession.get(item["link"])).text()
                    soup = BeautifulSoup(item_page, "html.parser")
                    #item["tradeable"] = -bool(soup.findAll("strong", text="Cannot be traded"))
                    items.append(item)
                self.bot.Trove.luxion_inventory[str(initial_id)] = items
            e = CEmbed(description=f"Luxion is available. It will be gone {self.bot.Trove.time.luxion_end_rwts('R')}\nItem's info was fetched from **[Trovesaurus](https://trovesaurus.com/luxion)** made by **Etaew**", color=self.bot.comment)
            e.set_author(name="Current Luxion's Inventory", icon_url="https://i.imgur.com/9eOV0JD.png")
            for item in self.bot.Trove.luxion_inventory[str(initial_id)]:
                text = ""
                text += f'**[{item["name"]}]({item["link"]})**'
                text += f"\nPrice: **{item['price']} <:dragon_coin:858061506074378276>**"
                #text += f"\nStatus: **{'Tradeable' if item['tradeable'] else 'Not Tradeable'}**"
                text += f"\nLimit: **{item['limit']}**"
                e.add_field(name="\u200b", value=text)
            e.add_field(name="\u200b", value="\u200b")
            e.set_footer(text="Inventory from")
            e.timestamp = self.bot.Trove.time.rw_time(self.bot.Trove.time.luxion_start)
            await ctx.send(embed=e)
        else:
            e = CEmbed(
                description=f"It will be available on **{self.bot.Trove.time.luxion_start_rwts('F')}** until **{self.bot.Trove.time.luxion_end_rwts('F')}** **{self.bot.Trove.time.luxion_start_rwts('R')}**",
                color=self.bot.comment)
            e.set_author(name="Luxion is not available.", icon_url="https://i.imgur.com/0N0PYdp.png")
            await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Shows when corruxion is around.", aliases=["nlux"])
    async def corruxion(self, ctx):
        if self.bot.Trove.time.is_corruxion:
            e = CEmbed(description=f"Corruxion is available. It will be gone {self.bot.Trove.time.corruxion_end_rwts('R')}", color=self.bot.comment)
            e.description += "\n\nCorruxion items have a global purchase limit of 10 per visit."
            items = {
                "Empowered Water Gem Box": [15, "https://trovesaurus.com/item/lootbox/gems/empowered_blue"],
                "Empowered Fire Gem Box": [15, "https://trovesaurus.com/item/lootbox/gems/empowered_red"],
                "Empowered Air Gem Box": [15, "https://trovesaurus.com/item/lootbox/gems/empowered_yellow"],
                "Empowered Cosmic Gem Box": [15, "https://trovesaurus.com/item/lootbox/gems/empowered_cosmic"],
                "Lustrous Gem Box": [25, "https://trovesaurus.com/item/lootbox/gems/foci"],
                "Double Experience Potion": [3, "https://trovesaurus.com/item/consumable/xp_double"],
                "Bound Brilliance": [2, "https://trovesaurus.com/item/crafting/boundbrilliance"],
                "Chaos Dragon Egg Fragment": [1, "https://trovesaurus.com/item/dragon/egg/chaos_notrade_fragment"],
            }
            for item, price in items.items():
                text = f'[**{item}**]({price[1]})'
                text += f"\nPrice: **{price[0]} <:chaoscore:937042427636752455>**"
                e.add_field(name="\u200b", value=text)
            e.add_field(name="\u200b", value="\u200b")
            e.set_author(name="Corruxion", icon_url="https://i.imgur.com/BPNdE1w.png")
            await ctx.send(embed=e)
        else:
            e = CEmbed(
                description=f"It will be available on **{self.bot.Trove.time.corruxion_start_rwts('F')}** until **{self.bot.Trove.time.corruxion_end_rwts('F')}** **{self.bot.Trove.time.corruxion_start_rwts('R')}**",
                color=self.bot.comment)
            e.set_author(name="Corruxion is not available.", icon_url="https://i.imgur.com/BPNdE1w.png")
            await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Calculates coefficient given certain values.")
    async def sigil(
        self,
        ctx,
        powerrank: int=commands.Option(name="power_rank", description="Input power rank for sigil. [0-40000]"),
        masteryrank: int=commands.Option(name="mastery_rank", description="Input mastery rank for sigil. [0-999]")):
        if powerrank > 40000:
            await ctx.send("Power rank can't be that high. Max: 40000")
            return
        if masteryrank > 999:
            await ctx.send("Mastery rank can't be that high. Max: 999")
            return
        sigil = await self.bot.AIOSession.get(f"https://trove.slynx.xyz/sigil/?power={powerrank}&mastery={masteryrank}")
        sigil = BytesIO(await sigil.read())
        if not sigil:
            await ctx.send("That sigil is not in my database.")
            return
        e = CEmbed(color=self.bot.comment)
        e.set_image(url=f"attachment://sigil.png")
        await ctx.send(file=discord.File(sigil, filename="sigil.png"), embed=e)

 # Settings Commands

    @commands.group(name="settings", aliases=["set"])
    @perms.has_permissions("administrator")
    async def _settings(self, ctx):
        ...

    @_settings.command()
    async def game_server(self, ctx):
        data = await self.bot.db.db_servers.find_one({"_id": ctx.guild.id}, {"PTS mode": 1})
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"PTS mode": not data["PTS mode"]}})
        await ctx.reply(f"PTS Server mode set to **{not data['PTS mode']}**")

def setup(bot):
    bot.add_cog(Trove(bot))
