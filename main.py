import asyncio
import json
import logging
import os
import re
from datetime import datetime

import discord
from aiohttp import ClientSession
from discord.ext import commands, tasks

from base.DBAPI import Database
from utils.CustomObjects import TroveTime
from utils.modules import get_modules
from utils.objects import Values

#Logging
log_time = datetime.utcnow()
log_time = f"{log_time.year}_{log_time.month}_{log_time.day} - {log_time.hour}-{log_time.minute}-{log_time.second}"
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=f'logs/{log_time}_discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

keys = json.load(open("keys.json"))

class Dummy():
    ...

class TroveContext(commands.Context):
    async def get_guild_data(self, **keys):
        if not keys:
            keys.setdefault('_id', 1)
        return self.bot.utils.json(await self.bot.db.db_servers.find_one({"_id": self.guild.id}, keys))

    async def get_wild_data(self, database: str, finder, **keys):
        if not keys:
            keys.setdefault('_id', 1)
        if isinstance(finder, dict):
            data = await self.bot.db[database].find_one(finder, keys)
        else:
            data = await self.bot.db[database].find_one({"_id": finder}, keys)
        return data

    async def locale(self, key):
        data = await self.get_guild_data(locale=1)
        string = self.bot.locale[data["locale"]].get(key)
        if not string:
            string = self.bot.locale["en"].get(key)
        return str(string)

class Trove(commands.AutoShardedBot):
    def __init__(self, is_clone=False):
        self.is_clone = is_clone
        super().__init__(
            command_prefix=self.prefix,
            case_insensitive=True,
            intents=self._get_intents(),
            description="Trove",
            pm_help=None,
            status=discord.Status.dnd,
            activity=discord.Game(f"Starting Up..."),
            chunk_guilds_at_startup=True,
            allowed_mentions=discord.AllowedMentions(replied_user=False)
        )

    def _get_intents(self):
        intents = discord.Intents(
            # Enabled
            bans=True,
            dm_messages=True,
            emojis=True,
            guild_messages=True,
            guild_reactions=True,
            guilds=True,
            members=True,
            presences=True,
            # Disabled
            dm_reactions=False,
            integrations=False,
            invites=False,
            typing=False,
            voice_states=False,
            webhooks=False
        )
        return intents

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or TroveContext)

    async def prefix(self, bot, message):
        await bot.wait_until_ready()
        await self.db.database_check(server_id=message.guild.id if message.guild else None, user_id=message.author.id)
        prefixes = []
        if message.guild:
            server_prefixes = (await self.db.db_servers.find_one({"_id": message.guild.id}, {"settings.prefixes": 1}))["settings"]["prefixes"]
            prefixes.extend(server_prefixes)
        users_prefixes = (await self.db.db_users.find_one({"_id": message.author.id}, {"settings.prefixes": 1}))["settings"]["prefixes"]
        prefixes.extend(users_prefixes)
        return commands.when_mentioned_or(*(prefixes or ["n!"]))(self, message)

    async def on_ready(self):
        print("Bot connected as " + self.user.name + "#" + self.user.discriminator)
        info = list({m for m in (await self.application_info()).team.members})
        print("Owner: " + str(info[0].name) + "#" + str(info[0].discriminator) + " [" + str(info[0].id) + "]")
        print("Serving " + str(len(self.users)) + " users in " + str(len(self.guilds)) + " guilds!")
        print("===================================================")

    def shard_guilds(self):
        return {
            shard: [g for g in self.guilds if g.shard_id == shard]
            for shard in self.shards.keys()
        }

    async def setup(self):
        self.remove_command('help')
       # Database
        self._start_database()
       # Blacklist
        self._build_blacklist.start()
        self._load_locales()
       # Setup Bot constants
        await self._set_constants()
       # Webhooks
        await self._load_webhooks()
       # Load Modules
        await self._load_modules()
       # Run Status Change
        self._status_task.start()
        await super().setup()

    def _start_database(self):
        self.db = Database()

    @tasks.loop(seconds=60)         
    async def _build_blacklist(self):
        try:
            guild = self.get_guild(834505270075457627)
            self.blacklist = [ban.user.id for ban in await guild.bans() if not ban.user.bot]
        except:
            if not hasattr(self, "blacklist"):
                self.blacklist = []

    def _load_locales(self):
        self.locale = {}
        for language in os.listdir("locales"):
            self.locale[language] = {}
            for f in os.listdir("locales/"+language):
                module, ext = f.split(".")
                if ext != "lang":
                    continue
                with open(f"locales/{language}/"+f, "r+") as _file:
                    text = _file.read().replace("\n", "")
                    data = dict(re.findall(r"(?i)\$([a-z0-9_]+):([^$]*)", text, re.MULTILINE))
                    self.locale[language] = data

    async def _set_trove_constants(self):
        setattr(self, "Trove", Dummy())
        setattr(self.Trove, "values", Values())
        setattr(self.Trove, "time", TroveTime())
        setattr(self.Trove, "sheets", {})
        setattr(self.Trove, "daily_data", json.load(open(f"/home/{keys['Bot']['User']}/nucleo/data/daily_buffs.json")))
        setattr(self.Trove, "weekly_data", json.load(open(f"/home/{keys['Bot']['User']}/nucleo/data/weekly_buffs.json")))
        db_bot = (await self.db.db_bot.find_one({"_id": "0511"}, {"mastery": 1}))["mastery"]
        for key, value in db_bot.items():
            if key.startswith("max"):
                setattr(self.Trove, key, value)

    async def _set_constants(self):
        authors = [
            117951235423731712, # Etaew
            209758232502206464, # TFMHisztike
            237634733264207872, # Nikstar
            523714260090748938, # LunarStation
        ]
        self.authors = {author: self.get_user(author) or await self.fetch_user(author) for author in authors}
        self.owners = {m.id for m in (await self.application_info()).team.members}
        self.admin_ids = [
            103696281297231872, # Dan
            163788520836694016, # Tom
            237634733264207872, # Nik
            350322003040927745, # Toff
            565097923025567755  # Sly
        ]
        self.sage_moderators = {
            565097923025567755, # Sly
            163788520836694016, # Tom
            350322003040927745, # Toff
            953591740621803550  # Trovesaurus Role
        }
        self.comment = 0x000080
        self.success = 0x008000
        self.error = 0x800000
        self.progress = 0xf9d71c
        self.version = "3.5.77", 1651748924
        self.time = TroveTime()
        self.uptime = datetime.utcnow().timestamp()
        self._last_exception = None
        all_perms = discord.Permissions.all().value
        self.invite = f"https://discord.com/oauth2/authorize?client_id=425403525661458432&permissions={all_perms}&scope=bot%20applications.commands"
        self.keys = keys
        await self._set_trove_constants()
     
    async def _load_webhooks(self):
        self.AIOSession = ClientSession()
        try:
            self.commands_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["commands_logger"], session=self.AIOSession)
            self.slash_commands_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["slash_commands_logger"], session=self.AIOSession)
            self.blacklist_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["blacklist_logger"], session=self.AIOSession)
            self.error_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["error_logger"], session=self.AIOSession)
            self.guild_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["guild_logger"], session=self.AIOSession)
            self.profiles_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["profiles_logger"], session=self.AIOSession)
            self.appeal_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["appeal_logger"], session=self.AIOSession)
            self.dm_logger = discord.Webhook.from_url(self.keys["Bot"]["Webhook"]["dm_logger"], session=self.AIOSession)
        except:
            ...

    async def _load_modules(self):
        await self.change_presence(activity=discord.Game(f"Loading Modules..."), status=discord.Status.idle)
        self.modules = get_modules
        for m in self.modules("cogs/"):
            if not m.priority:
                continue
            try:
                self.load_extension(m.load)
            except Exception as e:
                print(e)
                pass

    @tasks.loop(seconds=1)         
    async def _status_task(self):
        await self.wait_until_ready()
        statuses = [
            "n!help",
            "slynx.xyz/trovebot",
            f"in {len(self.guilds)} communities",
            f"v{self.version[0]}"
        ]
        for status in statuses:
            await self.change_presence(
                activity=discord.Activity(
                    name=status,
                    type=discord.ActivityType.playing
                )
            )
            await asyncio.sleep(60)

    async def on_message(self, message):
        if not hasattr(self, "owners") or message.author.id not in self.owners:
            return
        await self.process_commands(message)

    async def on_message_edit(self, _, message):
        if not hasattr(self, "owners") or message.author.id not in self.owners:
            return
        await self.process_commands(message)

loop = asyncio.get_event_loop()

for i in range(len(keys["Bot"]["Tokens"])):
    Token = keys["Bot"]["Tokens"][i]
    loop.create_task(Trove(i!=0).start(keys["Bot"]["Tokens"][i], reconnect=True))
    break

loop.run_forever()