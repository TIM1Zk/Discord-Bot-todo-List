import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# --- LINE SDK v3 ---
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)

# --- การตั้งค่าเบื้องต้น ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_GROUP_ID = os.getenv('LINE_GROUP_ID')

configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
last_msg_ids = {}

def get_thai_date():
    tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(tz).date()

# ฟังก์ชันส่งการแจ้งเตือนไป LINE (รองรับการส่งข้อความยาวๆ)
def send_to_line(message):
    if LINE_ACCESS_TOKEN and LINE_GROUP_ID:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            text_message = TextMessage(text=str(message))
            push_message_request = PushMessageRequest(
                to=LINE_GROUP_ID,
                messages=[text_message]
            )
            try:
                line_bot_api.push_message(push_message_request)
            except Exception as e:
                print(f"LINE Notification Error: {e}")

# --- ตั้งค่าฐานข้อมูล ---
conn = sqlite3.connect('todo_list.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        status TEXT,
        created_at TEXT
    )
''')
conn.commit()

# ฟังก์ชันช่วยดึงลิสต์รายการทั้งหมดมาเป็นข้อความ
def get_todo_list_text(user_id, today_str):
    cursor.execute("SELECT task, status FROM todos WHERE user_id = ? AND created_at = ?", (user_id, today_str))
    rows = cursor.fetchall()
    if not rows:
        return "ไม่มีรายการในขณะนี้"
    
    text = ""
    for i, row in enumerate(rows, start=1):
        emoji = "✅" if row[1] == 'done' else "⬜"
        text += f"{emoji} {i}. {row[0]}\n"
    return text

class TodoView(discord.ui.View):
    def __init__(self, user_id, rows):
        super().__init__(timeout=300)
        self.user_id = user_id
        for i, row in enumerate(rows, start=1):
            task_id, task, status = row
            if status == 'pending':
                button = discord.ui.Button(
                    label=f"ทำรายการที่ {i} เสร็จแล้ว", 
                    style=discord.ButtonStyle.success,
                    custom_id=f"todo_{task_id}"
                )
                button.callback = self.create_callback(task_id, task)
                self.add_item(button)

    def create_callback(self, task_id, task_name):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ นี่ไม่ใช่รายการของคุณครับ", ephemeral=True)
                return
            
            today_str = get_thai_date().isoformat()
            cursor.execute("UPDATE todos SET status = 'done' WHERE id = ? AND user_id = ?", (task_id, self.user_id))
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM todos WHERE user_id = ? AND created_at = ? AND status = 'pending'", (self.user_id, today_str))
            pending_count = cursor.fetchone()[0]

            if pending_count == 0:
                send_to_line(f"🎊 ยินดีด้วย! ภารกิจวันนี้เสร็จสิ้นทั้งหมดแล้วครับ!\n(รายการล่าสุด: {task_name})")
                cursor.execute("DELETE FROM todos WHERE user_id = ? AND created_at = ?", (self.user_id, today_str))
                conn.commit()
                embed = discord.Embed(title="🎊 ภารกิจวันนี้เสร็จสิ้น!", color=discord.Color.gold())
                await interaction.response.edit_message(embed=embed, view=None)
                last_msg_ids.pop(self.user_id, None)
            else:
                list_text = get_todo_list_text(self.user_id, today_str)
                send_to_line(f"✅ ทำรายการสำเร็จ: {task_name}\n\n📝 ลิสต์ปัจจุบัน:\n{list_text}")
                
                cursor.execute("SELECT id, task, status FROM todos WHERE user_id = ? AND created_at = ?", (self.user_id, today_str))
                updated_rows = cursor.fetchall()
                embed = discord.Embed(title="📝 To-do List อัปเดตล่าสุด", color=discord.Color.green())
                embed.description = list_text
                await interaction.response.edit_message(embed=embed, view=TodoView(self.user_id, updated_rows))
        return callback

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# --- Slash Commands ---

@bot.tree.command(name="add", description="เพิ่มรายการและส่งลิสต์ไป LINE")
async def add(interaction: discord.Interaction, task: str):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    today_str = get_thai_date().isoformat()
    
    # ลบข้อความเก่าในแชนเนล Discord
    if user_id in last_msg_ids:
        try:
            old_msg = await interaction.channel.fetch_message(last_msg_ids[user_id])
            await old_msg.delete()
        except: pass

    cursor.execute("INSERT INTO todos (user_id, task, status, created_at) VALUES (?, ?, ?, ?)", (user_id, task, 'pending', today_str))
    conn.commit()

    # ดึงลิสต์ทั้งหมดส่งไป LINE
    current_list = get_todo_list_text(user_id, today_str)
    send_to_line(f"📌 เพิ่มงานใหม่: {task}\n\n📝 รายการทั้งหมดวันนี้:\n{current_list}")

    cursor.execute("SELECT id, task, status FROM todos WHERE user_id = ? AND created_at = ?", (user_id, today_str))
    rows = cursor.fetchall()
    embed = discord.Embed(title="📝 To-do List ปัจจุบัน", description=current_list, color=discord.Color.blue())
    
    await interaction.followup.send(f"✅ เพิ่มรายการ '**{task}**' แล้ว", ephemeral=True)
    new_msg = await interaction.channel.send(embed=embed, view=TodoView(user_id, rows))
    last_msg_ids[user_id] = new_msg.id

@bot.tree.command(name="list", description="ดูรายการ To-do ทั้งหมด")
async def list_todo(interaction: discord.Interaction):
    user_id = interaction.user.id
    today_str = get_thai_date().isoformat()
    
    cursor.execute("SELECT id, task, status FROM todos WHERE user_id = ? AND created_at = ?", (user_id, today_str))
    rows = cursor.fetchall()
    
    if not rows:
        await interaction.response.send_message("📅 ยังไม่มีรายการสำหรับวันนี้", ephemeral=True)
        return

    list_text = get_todo_list_text(user_id, today_str)
    embed = discord.Embed(title="📝 รายการ To-do ของคุณ", description=list_text, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=TodoView(user_id, rows), ephemeral=True)

@bot.tree.command(name="clear", description="ล้างรายการทั้งหมดของวันนี้")
async def clear(interaction: discord.Interaction):
    user_id = interaction.user.id
    today_str = get_thai_date().isoformat()
    
    cursor.execute("DELETE FROM todos WHERE user_id = ? AND created_at = ?", (user_id, today_str))
    conn.commit()
    
    send_to_line("🗑️ รายการ To-do ทั้งหมดถูกล้างเรียบร้อยแล้ว")
    await interaction.response.send_message("🗑️ ล้างรายการของวันนี้ทั้งหมดแล้ว", ephemeral=True)

bot.run(TOKEN)