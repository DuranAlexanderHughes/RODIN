from __future__ import annotations

import os
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parents[1]  # RODIN/
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is missing in .env")

# Message content intent is required for prefix commands in many servers
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def call_backend(user_id: str, message: str) -> dict:
    payload = {"user_id": user_id, "message": message}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/ask", json=payload) as resp:
            # Show helpful error if backend returns non-200
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


@bot.command(name="lore")
async def lore(ctx: commands.Context, *, query: str):
    """Ask RODIN a BioShock lore question."""
    await ctx.trigger_typing()

    try:
        data = await call_backend(str(ctx.author.id), query)
    except Exception as e:
        await ctx.send(f"Error calling backend: {e}")
        return

    structured = data.get("structured", {}) or {}
    summary = structured.get("summary") or data.get("answer") or "No answer returned."
    confidence = structured.get("confidence", "unknown")

    # Discord embed description limit is 4096; keep margin
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


if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
