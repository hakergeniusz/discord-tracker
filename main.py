import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import time

# get the token
load_dotenv()
TOKEN = os.environ.get("TOKEN")


# make the bot
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print("-" * 40)
    print(f"Logged on as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    print("-" * 40)
    print(f"{message.author.name} sent a message.")
    print(f"Author ID: {message.author.id}")
    print(f"Message ID: {message.id}")
    print(f"Timestamp: {int(time.time())}")
    print(f"**Message**: {message.content}")


@bot.event
async def on_message_delete(message: discord.Message):
    print("-" * 40)
    print(f"{message.author.name} deleted a message.")
    print(f"Author ID: {message.author.id}")
    print(f"Message ID: {message.id}")
    print(f"Timestamp: {int(time.time())}")
    print(f"**Message**: {message.content}")


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    print("-" * 40)
    print(f"{after.author.name} edited a message.")
    print(f"Author ID: {after.author.id}")
    print(f"Message ID: {before.id}")
    print(f"Timestamp: {int(time.time())}")
    print(f"**Original message**: {before.content}")
    print(f"**New message**: {after.content}")


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    print("-" * 40)
    if payload.cached_message:
        msg = payload.cached_message
        print(f"{msg.author.name} deleted a message")
        print(f"Author ID: {msg.author.id}")
        print(f"Message ID: {msg.id}")
        print(f"Timestamp: {int(time.time())}")
        print(f"Content: {msg.content}")
    else:
        print("Someone unknown deleted a message.")
        print(f"Message ID: {payload.message_id}")
        print("Message not in cache (content unknown).")


bot.run(TOKEN)
