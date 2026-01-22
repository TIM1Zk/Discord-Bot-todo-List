import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# --- ตั้งค่าฐานข้อมูล ---
conn = sqlite3.connect('todo_list.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        status TEXT,
        created_at DATE
    )
''')
conn.commit()

# --- ตั้งค่าบอท ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# --- Slash Commands ---

@bot.tree.command(name="add", description="เพิ่มรายการที่ต้องทำ")
async def add(interaction: discord.Interaction, task: str):
    user_id = interaction.user.id
    today = date.today()
    cursor.execute("INSERT INTO todos (user_id, task, status, created_at) VALUES (?, ?, ?, ?)",
                   (user_id, task, 'pending', today))
    conn.commit()
    await interaction.response.send_message(f"✅ เพิ่มรายการ: **{task}** เรียบร้อยแล้ว!")

@bot.tree.command(name="list", description="ดูรายการ To-do ของวันนี้")
async def list_todo(interaction: discord.Interaction):
    user_id = interaction.user.id
    today = date.today()
    cursor.execute("SELECT id, task, status FROM todos WHERE user_id = ? AND created_at = ?", (user_id, today))
    rows = cursor.fetchall()
    
    if not rows:
        await interaction.response.send_message("📅 วันนี้คุณยังไม่มีรายการที่ต้องทำเลย!")
        return

    embed = discord.Embed(title=f"📝 To-do List ของคุณวันนี้", color=discord.Color.blue())
    for row in rows:
        status_emoji = "✅" if row[2] == 'done' else "⏳"
        embed.add_field(name=f"ID: {row[0]}", value=f"{status_emoji} {row[1]}", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="done", description="ทำเครื่องหมายว่ารายการนั้นเสร็จแล้ว")
async def done(interaction: discord.Interaction, task_id: int):
    cursor.execute("UPDATE todos SET status = 'done' WHERE id = ? AND user_id = ?", (task_id, interaction.user.id))
    conn.commit()
    await interaction.response.send_message(f"🎉 ยินดีด้วย! รายการ ID: {task_id} สำเร็จแล้ว")

@bot.tree.command(name="clear", description="ลบรายการทั้งหมดของวันนี้")
async def clear(interaction: discord.Interaction):
    today = date.today()
    cursor.execute("DELETE FROM todos WHERE user_id = ? AND created_at = ?", (interaction.user.id, today))
    conn.commit()
    await interaction.response.send_message("🗑️ ลบรายการของวันนี้ทั้งหมดแล้ว")

bot.run(TOKEN)