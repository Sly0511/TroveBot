import asyncio
from copy import deepcopy
from random import Random, choices, seed
from string import ascii_letters, digits
from utils.CustomObjects import Dict

from motor.motor_asyncio import AsyncIOMotorClient


class DatabaseID(Random):
    def __init__(self, server_id=0, user_id=0):
        super().__init__(server_id+user_id<<2)
    
    def __str__(self):
        return self.GetID
    
    @property
    def GetID(self):
        return "".join(self.choices(ascii_letters+digits, k=32))

class Profile():
    def __init__(self, data=None):
        self._data = data

class DB():
    def __init__(self, database):
        self.client = AsyncIOMotorClient()
        self.database = self.client[database]
        asyncio.create_task(self._database_setup())

    async def _database_setup(self):
        await self._setup_collections_shortcuts()

    async def _setup_collections_shortcuts(self):
        collections = await self.database.list_collection_names()
        for collection in collections:
            setattr(self, "db_"+collection, self.database[collection])

class Database(DB):
    def __init__(self, database="trove"):
        super().__init__(database=database)
        asyncio.create_task(self._ensure_database())

    async def _ensure_database(self):
        while True:
            if hasattr(self, "db_bot"):
                bot = await self.db_bot.find_one({"_id": "0511"}, {"_id": 1})
                if not bot:
                    await self.db_bot.insert_one(self._default_bot())
                break
            await asyncio.sleep(1)

    async def database_check(self, server_id=None, user_id=None):
        if user_id:
            data = await self.db_users.find_one({"_id": user_id})
            new_data = self._default_user(user_id)
            if not data:
                try:
                    await self.db_users.insert_one(new_data)
                except:
                    ...
            else:
                new_data = Dict(deepcopy(data)).fix(new_data)
                if new_data != data:
                    await self.db_users.update_one({"_id": user_id}, {"$set": new_data})
        if server_id:
            data = await self.db_servers.find_one({"_id": server_id})
            new_data = self._default_server(server_id)
            if not data:
                await self.db_servers.insert_one(new_data)
            else:
                new_data = Dict(deepcopy(data)).fix(new_data)
                if new_data != data:
                    await self.db_servers.update_one({"_id": server_id}, {"$set": new_data})
            return new_data
        
    async def stats_list(self):
        stats = []
        async for doc in self.db_profiles.find({}, {"Bot Settings": 0, "Collected Mastery": 0, "Clubs": 0, "_id": 0}):
            for i in doc["Classes"].keys():
                stats.extend(list(self._return_stat_names(doc["Classes"][i], "Classes.Class.")))
            del doc["Classes"]
            stats.extend(list(self._return_stat_names(doc)))
        return sorted(list(set(stats)))

    def _return_stat_names(self, data: dict, nest=""):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "Last Update":
                    continue
                if not isinstance(value, (dict, int, float, list)):
                    continue 
                if not nest and isinstance(value, (int, float)):
                    yield key
                if nest:
                    yield nest + key
                for ret in self._return_stat_names(value, nest=nest+key+"."):
                    yield ret

    def _default_bot(self):
        return {
            "_id": "0511",
            "blacklist": [],
            "prefixes": {
                "servers": {},
                "users": {}
            },
            "mastery": {
                "mastery_update": 0,
                "geode_mastery_update": 0,
                "max_live_mastery": 0,
                "max_live_mastery_geode": 0,
                "max_pts_mastery": 0,
                "max_pts_mastery_geode": 0
            },
            "giveaway": [],
            "anti_scam": {
                "domains": []
            }
        }

    def _default_server(self, server_id: int):
        return {
            "_id": server_id,
            "settings": {
                "prefixes": []
            },
            "locale": "en",
            "PTS mode": False,
            "self_cleanup": False,
            "commands": {
                "list_mode": 0,
                "list": {}
            },
            "leaderboards": {
                "list": []
            },
            "automation": {
                "daily": {
                    "voice": {
                        "channel": None
                    },
                    "text": {
                        "channel": None,
                        "role": None
                    }
                },
                "weekly": {
                    "voice": {
                        "channel": None
                    },
                    "text": {
                        "channel": None,
                        "role": None
                    }
                },
                "dragon_merchant": {
                    "voice": {
                        "channel": None
                    },
                    "text": {
                        "channel": None,
                        "role": None
                    }
                },
                "nickname": {
                    "toggle": False
                },
                "club": {
                    "name": None,
                    "member_role": None,
                    "member_role_only_profile": False
                }
            },
            "stat_roles": {
                "settings": {},
                "roles": {}
            },
            "clock": {
                "channel": None,
                "format": None,
                "slowmode": 5
            },
            "forums_posts": {},
            "twitch": {
                "channel": None,
                "message": None,
                "channels": [],
                "notified": []
            },
            "blacklist": {
                "channel": None
            },
            "anti_scam": {
                "settings": {
                    "toggle": True,
                    "log_channel": None,
                    "mode": -1,
                    "custom_domains": []
                },
                "hit_count": 0,
                "domains": {}
            }
        }

    def _default_user(self, user_id: int):
        return {
            "_id": user_id,
            "settings": {
                "prefixes": []
            },
            "builds": {
                "saved": []
            }
        }