import asyncio
from ..config import settings
from ..database import SessionLocal
from ..models import Incident
from ..agents.workflow import run_demo_workflow, classify

async def run_discord_bot():
    if not settings.discord_bot_token: return
    try:
        import discord
    except ImportError: return
    intents=discord.Intents.default(); intents.message_content=True
    client=discord.Client(intents=intents)
    @client.event
    async def on_ready(): print(f"Discord bot connected as {client.user}")
    @client.event
    async def on_message(message):
        if message.author.bot: return
        if settings.discord_channel_id and str(message.channel.id)!=settings.discord_channel_id: return
        text=message.content.strip()
        if not text or not any(k in text.lower() for k in ["@campuspulse","wifi","wi-fi","projector","maintenance","water","electricity","network"]): return
        category,priority,location=classify(text)
        db=SessionLocal()
        try:
            incident=Incident(title=f"{category} report",description=text,category=category,priority=priority,location=location,reporter=str(message.author))
            db.add(incident); db.commit(); db.refresh(incident)
            run_demo_workflow(db,incident)
            await message.reply(f"CampusPulse received incident **#{incident.id}** ({incident.priority}). Pulse has routed it for investigation. This bot's workflow is currently demo-mode unless live Switch execution is configured. No physical fix is claimed.")
        finally: db.close()
    await client.start(settings.discord_bot_token)
