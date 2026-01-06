import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import re
import aiohttp
import io
import random
import logging
import asyncio
from flask import Flask, request, jsonify
import threading

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for API
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'bot': 'running'}), 200

@app.route('/api/send-ic', methods=['POST'])
def send_ic_message():
    try:
        data = request.json
        command = data.get('command', 'ic-info')
        message = data.get('message', '')
        channel_id = data.get('channelId', '')
        
        logger.info(f"Received IC message: {command} to {channel_id}")
        
        # Map channel IDs to Discord channel tokens
        channel_map = {
            'ic-events': icinfo_token,
            'supernatural-events': spninfo_token,
            'general-ic': icinfo_token
        }
        
        target_channel_token = channel_map.get(channel_id, icinfo_token)
        admin_channel_token = icinfoadmin_token if channel_id == 'ic-events' else (spninfoadmin_token if channel_id == 'supernatural-events' else None)
        
        # Send message using existing process_info function
        asyncio.create_task(send_game_message(target_channel_token, admin_channel_token, message))
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error processing IC message: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

async def send_game_message(channel_token, admin_channel_token, message):
    try:
        channel = bot.get_channel(channel_token)
        admin_channel = bot.get_channel(admin_channel_token) if admin_channel_token else None
        
        if channel:
            await channel.send(message)
            if admin_channel:
                await admin_channel.send(f"**Game IC Message:**\n{message}")
            logger.info("Successfully sent game IC message to Discord")
        else:
            logger.error("Channel not found")
    except Exception as e:
        logger.error(f"Error sending game message: {e}")

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot_token = os.getenv('TOKEN')
spninfo_token = int(os.getenv('SPNINFO'))
spninfoadmin_token = int(os.getenv('SPNINFOADMIN')) if os.getenv('SPNINFOADMIN') else None
icinfo_token = int(os.getenv('ICINFO'))
icinfoadmin_token = int(os.getenv('ICINFOADMIN')) if os.getenv('ICINFOADMIN') else None

bot = commands.Bot(command_prefix='!', intents=intents)

def is_image_url(url):
    return re.match(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:jpg|jpeg|png|gif)$', url) is not None

def has_permission(ctx):
    if not isinstance(ctx.author, discord.Member):
        return True
    tester_role = int(os.getenv('TESTERROLE'))
    player_role = int(os.getenv('PLAYERROLE'))
    mercy_mainer_role = int(os.getenv('MERCYMAINERROLE'))
    allowed_user_id = int(os.getenv('QQUSERID'))
    allowed_roles = [tester_role, player_role, mercy_mainer_role]
    return any(role.id in allowed_roles for role in ctx.author.roles) or ctx.author.id == allowed_user_id

bot.add_check(has_permission)

@bot.event
async def on_ready():
    logger.info(f'Bot connected as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Отсутствуют обязательные аргументы.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Неверный формат аргумента.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("Произошла ошибка при выполнении команды.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.command(name='ic-info')
async def ic_info(ctx, *, args=None):
    await process_info(ctx, icinfo_token, icinfoadmin_token, args)

@bot.command(name='spn-info')
async def spn_info(ctx, *, args=None):
    await process_info(ctx, spninfo_token, spninfoadmin_token, args)

async def process_info(ctx, channel_token, admin_channel_token, args):
    if not args:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Вы не предоставили сообщение",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        return

    try:
        channel = bot.get_channel(channel_token)
        admin_channel = bot.get_channel(admin_channel_token) if admin_channel_token else None

        if not channel:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Канал не найден",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        urls = re.findall(r'http[s]?://\S+\.(?:jpg|jpeg|png|gif)', args)
        url = urls[0] if urls else None
        content = args.replace(url, '').strip() if url else args
        admin_content = f"**{ctx.author.display_name}** отправил(а):\n{content}"

        if url and is_image_url(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        embed = discord.Embed(
                            title="❌ Ошибка",
                            description="Не удалось загрузить изображение",
                            color=0xFF0000
                        )
                        await ctx.send(embed=embed)
                        return

                    data = io.BytesIO(await resp.read())
                    await channel.send(content, file=discord.File(data, 'image.png'))
                    if admin_channel:
                        data.seek(0) 
                        await admin_channel.send(admin_content, file=discord.File(data, 'image.png'))
        else:
            await channel.send(content)
            if admin_channel:
                await admin_channel.send(admin_content)
        
        # Success confirmation
        embed = discord.Embed(
            title="✅ Отправлено",
            description="Ваше сообщение было успешно отправлено",
            color=0x00FF00
        )
        confirmation = await ctx.send(embed=embed)
        
        # Delete both messages after 3 seconds
        await asyncio.sleep(3)
        await ctx.message.delete()
        await confirmation.delete()
        
    except Exception as e:
        logger.error(f"Error in process_info: {e}")
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Произошла ошибка при отправке сообщения",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

@bot.command(name='send_to_thread')
async def send_to_thread(ctx, thread_id: int, *, args=None):
    thread = bot.get_channel(thread_id)
    if not isinstance(thread, discord.Thread):
        await ctx.send("Указанный канал не является тредом.")
        return

    await process_info(ctx, thread_id, None, args)


@bot.command(name='info')
async def info(ctx):
    embed = discord.Embed(
        title="🎭 IC System Bot",
        description="Бот для анонимных внутриигровых событий",
        color=0x8B0000
    )
    
    embed.add_field(
        name="📢 Основные команды",
        value=(
            "**`!ic-info`** - Отправить IC событие\n"
            "**`!spn-info`** - Отправить сверхъестественное событие\n"
            "**`!dice`** - Бросить кубики\n"
            "**`!send_to_thread`** - Отправить в тред"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🖼️ Изображения",
        value=(
            "Добавьте URL изображения в сообщение:\n"
            "`!ic-info Вой волков на обсерватории https://i.ibb.co/example.png`\n"
            "⚠️ Используйте внешние хостинги (не Discord/Imgur)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎲 Кубики",
        value="`!dice [стороны] [количество]` - от 1-10 сторон, до 20 кубиков",
        inline=False
    )
    
    embed.set_footer(text="Все команды анонимны • Ваше сообщение будет удалено")
    await ctx.send(embed=embed)

@bot.command(name='info-dice')
async def info_dice(ctx):
    embed = discord.Embed(
        title="🎲 Система кубиков",
        color=0x4169E1
    )
    
    embed.add_field(
        name="Использование",
        value="`!dice [стороны] [количество]`",
        inline=False
    )
    
    embed.add_field(
        name="Параметры",
        value=(
            "**Стороны:** 1-10\n"
            "**Количество:** 1-20 кубиков"
        ),
        inline=True
    )
    
    embed.add_field(
        name="Примеры",
        value=(
            "`!dice 10` - один d10\n"
            "`!dice 10 5` - пять d10\n"
            "`!dice 6 3` - три d6"
        ),
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def dice(ctx, sides: int, number_of_dice: int = 1):
    if sides < 1 or sides > 10:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Количество сторон должно быть от 1 до 10",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        return
        
    if number_of_dice < 1 or number_of_dice > 20:
        embed = discord.Embed(
            title="❌ Ошибка", 
            description="Количество кубиков должно быть от 1 до 20",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        return
        
    results = [random.randint(1, sides) for _ in range(number_of_dice)]
    total = sum(results)
    
    embed = discord.Embed(
        title="🎲 Результат броска",
        color=0x00FF00
    )
    
    embed.add_field(
        name=f"{number_of_dice}d{sides}",
        value=f"**Результаты:** {' • '.join(map(str, results))}\n**Сумма:** {total}",
        inline=False
    )
    
    embed.set_footer(text=f"Бросок от {ctx.author.display_name}")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    # Start Flask API in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Discord bot
    bot.run(bot_token)
