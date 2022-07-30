import asyncio
import importlib.util
import os

import discord
from discord.ext import interaction
from flask import Flask
from functools import partial
from threading import Thread

from config.config import get_config
from config.log_config import log

from utils.token import token

if __name__ == "__main__":
    directory = os.path.dirname(os.path.abspath(__file__))

    log.info("CraftBOT을 불러오는 중입니다.")
    default_prefix = "$"
    parser = get_config()
    if parser.getboolean("DEFAULT", "AutoShard"):
        log.info("Config 파일에서 AutoShard가 켜져있습니다. AutoShard 기능을 킵니다.")
        bot = interaction.AutoShardedClient(
            command_prefix=default_prefix,
            intents=discord.Intents.default(),
            enable_debug_events=True,
            global_sync_command=True
        )
    else:
        bot = interaction.Client(
            command_prefix=default_prefix,
            intents=discord.Intents.default(),
            enable_debug_events=True,
            global_sync_command=True
        )

    app = Flask(__name__)

    asyncio.run(bot.load_extensions('cogs', directory))
    asyncio.run(bot.load_extensions('tasks', directory))
    partial_run = partial(app.run, host="0.0.0.0", port=3201, debug=True, use_reloader=False)

    views = [
        "views." + file[:-3] for file in os.listdir(
            os.path.join(directory, "views")
        ) if file.endswith(".py")
    ]
    for view in views:
        spec = importlib.util.find_spec(view)
        if spec is None:
            log.error("Extension Not Found: {0}".format(view))
            continue

        lib = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            log.error("Extension Failed: {0} ({1})".format(view, e.__class__.__name__))
            continue

        try:
            blueprint = getattr(lib, 'bp')
            setattr(lib, 'bot', bot)
        except AttributeError:
            log.error("No Entry Point Error: {0}".format(view))
            continue

        try:
            app.register_blueprint(blueprint)
        except Exception as e:
            log.error("Extension Failed: {0} ({1})".format(view, e.__class__.__name__))
            continue

    thread = Thread(target=partial_run)
    thread.start()

    bot.run(token.token)
