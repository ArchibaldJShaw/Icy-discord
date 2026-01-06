import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import re
import aiohttp
import io
import random
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot_token = os.getenv('TOKEN')
spninfo_token = int(os.getenv('SPNINFO'))
spninfoadmin_token = int(os.getenv('SPNINFOADMIN'))
icinfo_token = int(os.getenv('ICINFO'))
icinfoadmin_token = int(os.getenv('ICINFOADMIN'))

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
        await ctx.send("Вы не предоставили сообщение.")
        return

    try:
        channel = bot.get_channel(channel_token)
        admin_channel = bot.get_channel(admin_channel_token) if admin_channel_token else None

        if not channel:
            await ctx.send("Канал не найден.")
            return

        urls = re.findall(r'http[s]?://\S+\.(?:jpg|jpeg|png|gif)', args)
        url = urls[0] if urls else None
        content = args.replace(url, '').strip() if url else args
        admin_content = f"{ctx.author.display_name} отправил(а): {content}"

        if url and is_image_url(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await ctx.send("Не удалось загрузить изображение.")
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
                
        await ctx.message.delete()
    except Exception as e:
        logger.error(f"Error in process_info: {e}")
        await ctx.send("Произошла ошибка при отправке сообщения.")

@bot.command(name='send_to_thread')
async def send_to_thread(ctx, thread_id: int, *, args=None):
    thread = bot.get_channel(thread_id)
    if not isinstance(thread, discord.Thread):
        await ctx.send("Указанный канал не является тредом.")
        return

    await process_info(ctx, thread_id, None, args)


@bot.command(name='info')
async def info(ctx):
    response = (
        f"`Привет, {ctx.author.display_name}!\n\n"
        "С моей помощью вы сможете:\n"
        "- Отправить анонимные сообщения в #события и #сверхъестественные-события используя команды !ic-info и !spn-info.\n Укажите URL изображения первым аргументом, если хотите прикрепить картинку. Так же, важно прикрепить ссылку на изображение (с окончанием .jpeg, .jpg, .png и т. п.) и не использовать в качестве хостинга дискорд или imgur.\n Вот пример правильного использования: !ic-info На обсерватории слышен вой волков. https://i.ibb.co/h2pWd66/image.png\n"
        "- Отправить сообщение в определенный тред с URL изображения, используя команду !send_to_thread [ID треда] [сообщение].`"
    )
    await ctx.send(response)

@bot.command(name='info-dice')
async def info_dice(ctx):
    await ctx.send("`Чтобы бросить кубы, воспользуйся командой !dice [количество сторон кубов (1-10)] [количество кубов (до 20)].`")

@bot.command()
async def dice(ctx, sides: int, number_of_dice: int = 1):
    if sides < 1 or sides > 10:
        await ctx.send("```Количество сторон кубика должно быть от 1 до 10.")
        return
    if number_of_dice < 1 or number_of_dice > 20:
        await ctx.send("```Количество кубиков должно быть от 1 до 20.")
        return
    results = [random.randint(1, sides) for _ in range(number_of_dice)]
    await ctx.send(f"🎲 Результаты броска: {' '.join(map(str, results))}")

bot.run(bot_token)
