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

# ดึงค่า Token: รองรับทั้งแบบใส่ในโค้ดและดึงจากระบบ (Discloud)
TOKEN = os.getenv('DISCORD_TOKEN')
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_GROUP_ID = os.getenv('LINE_GROUP_ID')

configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
last_msg_ids = {}

def get_thai_date():
    tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(tz).date()

# ฟังก์ชันส่งการแจ้งเตือนไป LINE
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

# ฟังก์ชันดึงรายการรวมของทุกคนในวันนี้
def get_todo_list_text(today_str):
    cursor.execute("SELECT task, status FROM todos WHERE created_at = ?", (today_str,))
    rows = cursor.fetchall()
    if not rows:
        return "📅 ยังไม่มีรายการใดๆ สำหรับวันนี้"
    
    text = ""
    for i, row in enumerate(rows, start=1):
        emoji = "✅" if row[1] == 'done' else "⬜"
        text += f"{emoji} {i}. {row[0]}\n"
    return text

class TodoView(discord.ui.View):
    def __init__(self, rows):
        super().__init__(timeout=300)
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
            # ใช้ defer เพื่อป้องกัน Unknown interaction error ขณะกดปุ่ม
            await interaction.response.defer() 
            
            today_str = get_thai_date().isoformat()
            cursor.execute("UPDATE todos SET status = 'done' WHERE id = ?", (task_id,))
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM todos WHERE created_at = ? AND status = 'pending'", (today_str,))
            pending_count = cursor.fetchone()[0]

            if pending_count == 0:
                send_to_line(f"🎊 ยินดีด้วย! ภารกิจรวมวันนี้เสร็จสิ้นทั้งหมดแล้วครับ!\n(รายการล่าสุด: {task_name} โดย {interaction.user.display_name})")
                cursor.execute("DELETE FROM todos WHERE created_at = ?", (today_str,))
                conn.commit()
                embed = discord.Embed(title="🎊 ภารกิจวันนี้เสร็จสิ้น!", color=discord.Color.gold())
                await interaction.followup.send(embed=embed)
                last_msg_ids.clear() 
            else:
                list_text = get_todo_list_text(today_str)
                send_to_line(f"✅ {interaction.user.display_name} ทำรายการสำเร็จ: {task_name}\n\n📝 ลิสต์ปัจจุบัน:\n{list_text}")
                
                cursor.execute("SELECT id, task, status FROM todos WHERE created_at = ?", (today_str,))
                updated_rows = cursor.fetchall()
                embed = discord.Embed(title="📝 To-do List รวม (อัปเดตล่าสุด)", color=discord.Color.green())
                embed.description = list_text
                await interaction.edit_original_response(embed=embed, view=TodoView(updated_rows))
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

@bot.tree.command(name="add", description="เพิ่มรายการลงในลิสต์รวม")
async def add(interaction: discord.Interaction, task: str):
    await interaction.response.defer(ephemeral=True)
    today_str = get_thai_date().isoformat()
    
    if 'global' in last_msg_ids:
        try:
            old_msg = await interaction.channel.fetch_message(last_msg_ids['global'])
            await old_msg.delete()
        except: pass

    cursor.execute("INSERT INTO todos (user_id, task, status, created_at) VALUES (?, ?, ?, ?)", 
                   (interaction.user.id, task, 'pending', today_str))
    conn.commit()

    current_list = get_todo_list_text(today_str)
    send_to_line(f"📌 {interaction.user.display_name} เพิ่มงานใหม่: {task}\n\n📝 รายการรวมทั้งหมดวันนี้:\n{current_list}")

    cursor.execute("SELECT id, task, status FROM todos WHERE created_at = ?", (today_str,))
    rows = cursor.fetchall()
    embed = discord.Embed(title="📝 To-do List รวม (ปัจจุบัน)", description=current_list, color=discord.Color.blue())
    
    await interaction.followup.send(f"✅ เพิ่มรายการ '**{task}**' แล้ว", ephemeral=True)
    new_msg = await interaction.channel.send(embed=embed, view=TodoView(rows))
    last_msg_ids['global'] = new_msg.id

@bot.tree.command(name="list", description="ดูรายการ To-do รวมของทุกคน")
async def list_todo(interaction: discord.Interaction):
    # ใช้ defer เพื่อขยายเวลาตอบกลับ ป้องกัน Error 10062
    await interaction.response.defer(ephemeral=True) 
    
    today_str = get_thai_date().isoformat()
    cursor.execute("SELECT id, task, status FROM todos WHERE created_at = ?", (today_str,))
    rows = cursor.fetchall()
    
    if not rows:
        await interaction.followup.send("📅 ยังไม่มีรายการสำหรับวันนี้", ephemeral=True)
        return

    list_text = get_todo_list_text(today_str)
    embed = discord.Embed(title="📝 รายการ To-do รวมของทุกคน", description=list_text, color=discord.Color.blue())
    await interaction.followup.send(embed=embed, view=TodoView(rows), ephemeral=True)

@bot.tree.command(name="clear", description="ล้างรายการรวมทั้งหมดของวันนี้")
async def clear(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    today_str = get_thai_date().isoformat()
    cursor.execute("DELETE FROM todos WHERE created_at = ?", (today_str,))
    conn.commit()
    
    send_to_line(f"🗑️ {interaction.user.display_name} ล้างรายการ To-do ทั้งหมดเรียบร้อยแล้ว")
    await interaction.followup.send("🗑️ ล้างรายการรวมของวันนี้ทั้งหมดแล้ว", ephemeral=True)

if TOKEN:
    bot.run(TOKEN)