from __future__ import annotations

import os
import argparse
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# add args for cli debugging mode
parser = argparse.ArgumentParser(description="RODIN Discord Bot")
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    help="Enable debug logging",
)
args = parser.parse_args()
DEBUG = args.debug


def debug_log(*items):
    if DEBUG:
        print("[DEBUG]", *items)


# load from bot token from .env file
BASE_DIR = Path(__file__).resolve().parents[1]  # RODIN/
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise RuntimeError("BACKEND_URL is missing in .env")
BACKEND_URL = BACKEND_URL.rstrip("/")

if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is missing in .env")

# RODIN bot setup
intents = discord.Intents.default()
intents.message_content = True  # required for prefix commands in many servers

bot = commands.Bot(command_prefix="!", intents=intents)


# create call to backend
async def call_backend(user_id: str, message: str) -> dict:
    payload = {"user_id": user_id, "message": message}
    debug_log("Calling backend", payload)

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/ask", json=payload) as resp:
            debug_log("Backend status:", resp.status)

            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Backend returned {resp.status}: {text}")

            return await resp.json()


def format_sources(structured: dict, max_sources: int = 5) -> str:
    sources = structured.get("sources", []) or []
    if not sources:
        return "No sources returned."
    lines = []
    for s in sources[:max_sources]:
        title = s.get("title", "Unknown")
        chunk = s.get("chunk_index", "?")
        lines.append(f"- {title} (chunk {chunk})")
    return "\n".join(lines)


# log debug event on receiving message
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    debug_log(
        f"Received message in #{message.channel}",
        f"from {message.author}",
        f"content={message.content!r}",
    )

    # IMPORTANT: keep commands working
    await bot.process_commands(message)


# runs lore lookup command + optional debug logging
@bot.command(name="lore")
async def lore(ctx: commands.Context, *, query: str):
    """Ask RODIN a BioShock lore question."""
    debug_log("!lore invoked", f"user={ctx.author}", f"query={query!r}")

    async with ctx.typing():
        try:
            data = await call_backend(str(ctx.author.id), query)
            debug_log("Backend response received")
        except Exception as e:
            debug_log("Backend call failed:", repr(e))
            await ctx.send(f"Error calling backend: {e}")
            return

    structured = data.get("structured", {}) or {}
    summary = structured.get("summary") or data.get("answer") or "No answer returned."
    confidence = structured.get("confidence", "unknown")

    summary = summary[:3500]

    embed = discord.Embed(
        title="RODIN Lore Answer",
        description=summary,
    )
    embed.add_field(name="Confidence", value=str(confidence), inline=True)
    embed.add_field(name="Sources", value=format_sources(structured), inline=False)

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot logged in as: {bot.user}")
    debug_log("Registered commands:", [c.name for c in bot.commands])
    debug_log("BACKEND_URL:", BACKEND_URL)
    debug_log("Message Content Intent enabled:", intents.message_content)


if __name__ == "__main__":
    debug_log("Starting bot with DEBUG=True")
    bot.run(DISCORD_BOT_TOKEN)
