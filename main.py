'''
TITLE: Pigeon's Role Control Bot

PROGRAMERS: pigeonmen_ (Joshua West)

DISCRIPTION: Discord Bot to control & manage roles.

DATE CREATED: 21/08/2023
'''

#* Imports
import discord
from discord.ext import commands
from discord.commands import Option
from discord import ui
import os
import json
import asyncio
from discord.interactions import Interaction
from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timedelta
import re
import string
import requests
import logging
import colorlog
import sys

#* Load .env
load_dotenv()

#* Logging
logger = logging.getLogger('Discord Bot')

log_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s | %(levelname)s: %(message)s",
    datefmt="%d-%m-%Y %I:%M %p %Z",
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    },
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger.addHandler(console_handler)

logger.setLevel(logging.INFO)

def log_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception

#* Server Data Database (.db)
conn = sqlite3.connect('server_data.db')
c = conn.cursor()

#* Create Tables
# Roles the bot prevents users from having
c.execute('''CREATE TABLE IF NOT EXISTS roles
                (server_id int, role_id int)''')
# Roles the bot will ignore when preventing roles
c.execute('''CREATE TABLE IF NOT EXISTS bypass
                (server_id int, role_id int)''')
# Roles the bot will give to users when they join
c.execute('''CREATE TABLE IF NOT EXISTS auto
                (server_id int, role_id int)''')
# The bot's role for the server
c.execute('''CREATE TABLE IF NOT EXISTS bot_role
                (server_id int, role_id int)''')
# The bot's channel for announcements
c.execute('''CREATE TABLE IF NOT EXISTS announcements
                (server_id int, channel_id int)''')
# Roles that can manage the bot
c.execute('''CREATE TABLE IF NOT EXISTS manager_roles
                (server_id int, role_id int)''')
# Temp roles
c.execute('''CREATE TABLE IF NOT EXISTS temp_roles
                (server_id int, role_id int, user_id int, time int)''')
# Self roles Server ID, Channel ID, Message ID, Menu Type, and Role ID with emoji for that role
c.execute('''CREATE TABLE IF NOT EXISTS self_roles
                (server_id int, channel_id int, message_id int, menu_type text, role_id int, emoji text)''')
# self_role_templates
c.execute('''CREATE TABLE IF NOT EXISTS self_role_templates
                (server_id int, channel_id int, message_id int, menu_type text, role_id int, emoji text)''')
conn.commit()

#* Bot Prefix
bot = commands.Bot(command_prefix='rc-', intents=discord.Intents.all(), status=discord.Status.online, help_command=None)

owner = [1036616200211411034, 652498200447549450]

server_data = {}
self_roles_embeds = {}


#* Bot Startup
@bot.event
async def on_ready():
    print("----------------------------------------")
    logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    logger.info("Libaray: Python 3.11")
    logger.info("Prefix: rc-")
    logger.info("Bot Developers: " + ', '.join([str(bot.get_user(user_id)) for user_id in owner]))
    logger.info(f"Bot is ready! | Start time: {datetime.now().strftime('%d/%m/%Y %I:%M %p %Z')}")
    print("----------------------------------------")
    await bot.change_presence(activity=discord.Game(name='/help'))

    # support_server = bot.get_guild(1158967835616362626)
    # log_channel = support_server.get_channel(1143051391946981446)
    # embed = discord.Embed(title='Bot is ready.', description='Bot is ready.', color=0x00ff00)
    # embed.add_field(name='Bot is in', value=f'{len(bot.guilds)} servers.', inline=False)
    # embed.add_field(name='Bot is being used by', value=f'{len(bot.users)} users.', inline=False)
    # embed.add_field(name='Bot prefix is', value=f'`{bot.command_prefix}`', inline=False)
    # embed.add_field(name='Commands registered', value=f'{len(bot.commands)}', inline=False)
    # commands = []
    # for command in bot.commands:
    #     commands.append(command.name)
    # embed.add_field(name='Commands', value=f'{commands}', inline=False)
    # await channel.send(embed=embed)

bot_start_time = datetime.utcnow()


## ? Functions


#* Check if User Command
def user_command(interaction: discord.Interaction):
    return True

#* Check if Role Command
def role_command(interaction: discord.Interaction):
    if interaction.guild is None:
        return True
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    manager_role_id = c.fetchone()
    if manager_role_id:
        manager_role = discord.utils.get(interaction.author.roles, id=manager_role_id[0])
        if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
            return True
        elif manager_role:
            return True
        else:
            return False
    else:
        if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
            return True
        else:
            return False

#* Check if Setup Command
def setup_command(interaction: discord.Interaction):
    if interaction.guild is None:
        return True
    if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
        return True
    else:
        return False


#* Bot Error Handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('**Error:** `You do not have permission to use this command.`')
    elif isinstance(error, commands.MissingRequiredArgument):
        if ctx.author.id in owner:
            await ctx.reply(f'**Error:** `You are missing a required argument.`')
        else:
            pass
    elif isinstance(error, commands.CommandOnCooldown):
        if ctx.author.id in owner:
            await ctx.reply(f'**Error:** `You are on cooldown. Try again in {round(error.retry_after)} seconds.`')
        else:
            pass
    elif isinstance(error, commands.CommandNotFound):
        if ctx.author.id in owner:
            await ctx.reply(f'**Error:** `Command not found.`')
        else:
            pass
    else:
        if ctx.author.id in owner:
            await ctx.reply(f'**Error:** `{error}`')
        else:
            pass

async def on_slash_command_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await interaction.response.send_message('**Error:** `You are missing a required argument.`', ephemeral=True)
    elif isinstance(error, commands.CommandOnCooldown):
        await interaction.response.send_message(f'**Error:** `You are on cooldown. Try again in {round(error.retry_after)} seconds.`', ephemeral=True)
    else:
        await interaction.response.send_message(f'**Error:** `{error}`', ephemeral=True)



## ? Bot Commands

# * tos Command             
@bot.slash_command(name='tos', description='View the TOS.', checks=[user_command])
async def tos(interaction: discord.Interaction):
    tos = discord.Embed(title='Terms of Service | Role Control', description=f'By adding {bot.user.mention} to your server, you hereby acknowledge and agree to be bound by the following terms of service:', color=0x00ff00)
    tos.add_field(name='1. Compliance with Discord TOS & Guidelines', value=f'You shall not employ {bot.user.mention} in any manner that violates the [Discord Terms of Service](https://discord.com/terms) or [Discord Community Guidelines](https://discord.com/guidelines).', inline=False)
    tos.add_field(name='2. Prohibited Content & Activities', value=f'You shall refrain from using {bot.user.mention} in any server that endorses or engages in violence, hate speech *(Including but not limited to racism, transphobia, and other forms of discrimination)*, or any other unlawful activity.', inline=False)
    tos.add_field(name='3. NSFW Content', value=f'You shall not use {bot.user.mention} in any server that is primarily for NSFW *(Not Safe for Work)* content.', inline=False)
    tos.add_field(name='4. Anti-Disruption', value=f'You shall not use {bot.user.mention} for the purpose of raiding, spamming, or engaging in any activities that aim to disrupt or harass other users.', inline=False)
    tos.add_field(name='Subject to Change', value=f'These terms of service may be modified or updated at any time, and it is your responsibility to review them periodically. If you do not agree with the revised terms, you must promptly remove {bot.user.mention} from your server.', inline=False)
    tos.add_field(name='Violation of TOS', value=f'Violation of these terms of service may lead to {bot.user.mention} leaving your server and the blacklisting of your server.', inline=False)
    await interaction.response.send_message(embed=tos, ephemeral=True)

#* ping Command
@bot.slash_command(name='ping', description='View the bot\'s ping.', checks=[user_command])
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! {round(bot.latency * 1000)}ms', ephemeral=True)


#* myperms Command
@bot.slash_command(name='myperms', description='View your permissions.', checks=[user_command])
async def myperms(interaction: discord.Interaction):
    perms = interaction.author.guild_permissions
    perms_text = []

    for perm, value in perms:
        if value:
            perms_text.append(f'- **{perm}**')

    perms_text = '\n'.join(perms_text)

    embed = discord.Embed(title='Permissions', description=f'Permissions for {interaction.author.name}', color=0x00ff00)
    if interaction.author.avatar.url:
        embed.set_author(name=f'{interaction.author.name}', icon_url=f'{interaction.author.avatar.url}')
    else:
        embed.set_author(name=f'{interaction.author.name}', icon_url=f'{interaction.author.default_avatar.url}')

    if len(perms_text) > 1024:
        perms_text = perms_text.replace('**', '')
        with open('perms.txt', 'w') as f:
            f.write('Permissions: ' + interaction.author.name + '\n----------------------------------\n')
            f.write(perms_text)

        embed.add_field(name='Permissions', value='*Too many permissions to display. Sending in a text file.*', inline=False)
        await interaction.response.send_message(embed=embed, file=discord.File(f, 'perms.txt'), ephemeral=True)
        os.remove('perms.txt')
    else:
        embed.add_field(name='Permissions', value=perms_text, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)



#* Help Command
class AdminHelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=240)
        self.current_button = None

    async def on_timeout(self):
        em = discord.Embed(title='Role Control Help - Timed Out', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ\n\n', color=discord.Colour.red())
        em.description += f'Timed out after 4 minutes of inactivity!\n'
        em.description += f'Use </help:1145275940008636481> to view the help menu again.'
        try:
            await self.message.edit(embed=em, view=None)
        except:
            pass
        for child in self.children:
            child.style = discord.ButtonStyle.grey
            child.disabled = True
        await self.message.edit(view=self)

    async def render_buttons(self):
        for child in self.children:
            if child == self.current_button:
                child.style = discord.ButtonStyle.success
            else:
                child.style = discord.ButtonStyle.blurple
        await self.message.edit(view=self)


    @discord.ui.button(label='Administrator Commands', style=discord.ButtonStyle.success, emoji='🛠️')
    async def admin_commands(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_button = button
        await self.render_buttons()
        embed = discord.Embed(title='Role Control Help - Administrator Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)

        setup_commands = [
            cmd for cmd in bot.all_commands.values() if setup_command in cmd.checks
        ]

        embed_value = ''
        for cmd in setup_commands:
            embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

        embed.add_field(name='Setup Commands', value=embed_value, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Manager Commands', style=discord.ButtonStyle.blurple, emoji='👑')
    async def manager_commands(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_button = button
        await self.render_buttons()
        embed = discord.Embed(title='Role Control Help - Manager Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
        
        role_commands = [
            cmd for cmd in bot.all_commands.values() if role_command in cmd.checks
        ]

        embed_value = ''
        for cmd in role_commands:
            embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

        embed.add_field(name='Role Management', value=embed_value, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='User Commands', style=discord.ButtonStyle.blurple, emoji='👤')
    async def user_commands(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_button = button
        await self.render_buttons()
        embed = discord.Embed(title='Role Control Help - User Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
        
        user_commands = [
            cmd for cmd in bot.all_commands.values() if user_command in cmd.checks
        ]

        for cmd in user_commands:
            embed.add_field(name=f'</{cmd.name}:{cmd.id}>', value=cmd.description, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)

class ManagerHelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=240)
        self.current_button = None

    async def on_timeout(self):
        em = discord.Embed(title='Role Control Help - Timed Out', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ\n\n', color=discord.Colour.red())
        em.description += f'Timed out after 4 minutes of inactivity!\n'
        em.description += f'Use </help:1145275940008636481> to view the help menu again.'
        try:
            await self.message.edit(embed=em, view=None)
        except:
            pass
        for child in self.children:
            child.style = discord.ButtonStyle.grey
            child.disabled = True
        await self.message.edit(view=self)

    async def render_buttons(self):
        for child in self.children:
            if child == self.current_button:
                child.style = discord.ButtonStyle.success
            else:
                child.style = discord.ButtonStyle.blurple
        await self.message.edit(view=self)


    @discord.ui.button(label='Manager Commands', style=discord.ButtonStyle.success, emoji='👑')
    async def manager_commands(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_button = button
        await self.render_buttons()
        embed = discord.Embed(title='Role Control Help - Manager Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
        
        role_commands = [
            cmd for cmd in bot.all_commands.values() if role_command in cmd.checks
        ]

        embed_value = ''
        for cmd in role_commands:
            embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

        embed.add_field(name='Role Management', value=embed_value, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='User Commands', style=discord.ButtonStyle.blurple, emoji='👤')
    async def user_commands(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_button = button
        await self.render_buttons()
        embed = discord.Embed(title='Role Control Help - User Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
        
        user_commands = [
            cmd for cmd in bot.all_commands.values() if user_command in cmd.checks
        ]

        for cmd in user_commands:
            embed.add_field(name=f'</{cmd.name}:{cmd.id}>', value=cmd.description, inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=240)
        self.current_button = None

    async def on_timeout(self):
        em = discord.Embed(title='Role Control Help - Timed Out', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ\n\n', color=discord.Colour.red())
        em.description += f'Timed out after 4 minutes of inactivity!\n'
        em.description += f'Use </help:1145275940008636481> to view the help menu again.'
        try:
            await self.message.edit(embed=em, view=None)
        except:
            pass


@bot.slash_command(name='help', description='View available commands.', checks=[user_command])
async def help(interaction: discord.Interaction):

    user_commands = [
        cmd for cmd in bot.all_commands.values() if user_command in cmd.checks
    ]
    setup_commands = [
        cmd for cmd in bot.all_commands.values() if setup_command in cmd.checks
    ]
    role_commands = [
        cmd for cmd in bot.all_commands.values() if role_command in cmd.checks
    ]

    # if they have admin perms
    if interaction.guild is None:
        embed = discord.Embed(title='Role Control Help - Manager Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
        
        embed_value = ''
        for cmd in setup_commands:
            embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

        embed.add_field(name='Setup Commands', value=embed_value, inline=True)
        
        return await interaction.response.send_message(embed=embed, view=AdminHelpView(), ephemeral=True)
    manager_role_id = c.fetchone()
    if manager_role_id:
        manager_role = discord.utils.get(interaction.author.roles, id=manager_role_id[0])
        if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
            embed = discord.Embed(title='Role Control Help - Manager Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
            
            embed_value = ''
            for cmd in setup_commands:
                embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

            embed.add_field(name='Setup Commands', value=embed_value, inline=True)
            
            await interaction.response.send_message(embed=embed, view=AdminHelpView(), ephemeral=True)
        elif manager_role:
            embed = discord.Embed(title='Role Control Help - Manager Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
            
            embed_value = ''
            for cmd in role_commands:
                embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

            embed.add_field(name='Role Management', value=embed_value, inline=True)
            
            await interaction.response.send_message(embed=embed, view=ManagerHelpView(), ephemeral=True)
        else:
            embed = discord.Embed(title='Role Control Help - User Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
            
            for cmd in user_commands:
                embed.add_field(name=f'</{cmd.name}:{cmd.id}>', value=cmd.description, inline=False)

            await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)
    else:
        if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
            embed = discord.Embed(title='Role Control Help - Manager Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
            
            embed_value = ''
            for cmd in setup_commands:
                embed_value += f'**</{cmd.name}:{cmd.id}> :** {cmd.description}\n\n'

            embed.add_field(name='Setup Commands', value=embed_value, inline=True)
            
            await interaction.response.send_message(embed=embed, view=AdminHelpView(), ephemeral=True)
        else:
            embed = discord.Embed(title='Role Control Help - User Commands', description='Discord Bot to control & manage roles.\nSupport server: https://discord.gg/9HtyP4SJVJ', color=0x00ff00)
            
            for cmd in user_commands:
                embed.add_field(name=f'</{cmd.name}:{cmd.id}>', value=cmd.description, inline=False)

            await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)

#* Invite Command
@bot.slash_command(name='invite', description='Invite the bot to your server.', checks=[user_command])
async def invite(interaction: discord.Interaction):
    await interaction.response.send_message('**[Invite Me!](https://discord.com/api/oauth2/authorize?client_id=1143043056107528192&permissions=8&scope=bot)**\n*Join our server if you need support: https://discord.gg/9HtyP4SJVJ*', ephemeral=True)

#* Uptime command
@bot.slash_command(name='uptime', description='View the bot\'s uptime.', checks=[user_command])
async def uptime(interaction: discord.Interaction):
    # Calculate the current uptime based on bot startup time
    current_time = datetime.now()
    uptime_since_start = current_time - bot_start_time

    # Calculate the number of weeks, days, hours, minutes, seconds
    weeks = uptime_since_start.days // 7
    days = uptime_since_start.days % 7
    hours = uptime_since_start.seconds // 3600
    minutes = (uptime_since_start.seconds % 3600) // 60
    seconds = uptime_since_start.seconds % 60

    # Format the start time in UTC
    start_time_formatted = f'<t:{int(bot_start_time.timestamp())}:F>'

    # format uptime
    uptime_components = []
    
    if weeks > 0:
        uptime_components.append(f'{weeks} week{"s" if weeks > 1 else ""}')
    if days > 0:
        uptime_components.append(f'{days} day{"s" if days > 1 else ""}')
    if hours > 0:
        uptime_components.append(f'{hours} hour{"s" if hours > 1 else ""}')
    if minutes > 0:
        uptime_components.append(f'{minutes} minute{"s" if minutes > 1 else ""}')
    if seconds > 0:
        uptime_components.append(f'{seconds} second{"s" if seconds > 1 else ""}')

    uptime_str = ', '.join(uptime_components)

    embed = discord.Embed(title='Role Control | Uptime 🕐', color=0x00ff00)
    embed.add_field(name='Current Uptime', value=uptime_str, inline=False)
    embed.add_field(name='Started', value=start_time_formatted, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

#* Setup Command (Admin Only)
setup_roles = ()

@bot.slash_command(name='setup', description='Setup the bot for your server.', checks=[setup_command])
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
async def setup(
    interaction: discord.Interaction,
    channel: Option(discord.TextChannel, description='Announcement channel.', required=True),
    protect: Option(discord.Role, description='Role to protect from users.', required=False),
    bypass: Option(discord.Role, description='Role to bypass the bot.', required=False),
    auto: Option(discord.Role, description='Role to auto assign to new users.', required=False),
    manager: Option(discord.Role, description='Role that can manage the bot.', required=False)
):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)

    c.execute('SELECT role_id FROM roles WHERE server_id=?', (interaction.guild.id,))
    roles = c.fetchall()
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (interaction.guild.id,))
    auto_roles = c.fetchall()
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (interaction.guild.id,))
    bypass_roles = c.fetchall()
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
    channel_id = c.fetchall()
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    managers = c.fetchall()

    if channel_id not in [None, []]:
        return await interaction.response.send_message('You have already setup the bot for your server.\n> If you wish to reset the bot, use </reset:1145275940168024084>.', ephemeral=True)
    
    if ((protect == auto and protect is not None) or (protect == manager and protect is not None) or (protect == bypass and protect is not None) or (auto == manager and auto is not None) or (auto == bypass and auto is not None)):
        return await interaction.response.send_message('I\'m sorry but you can\'t use the same role twice *(Manager & Bypass can be the same)*.\n> Please try again!', ephemeral=True)

    if protect is None:
        pass
    else:
        c.execute('INSERT INTO roles VALUES (?, ?)', (interaction.guild.id, protect.id))
    if bypass is None:
        pass
    else:
        c.execute('INSERT INTO bypass VALUES (?, ?)', (interaction.guild.id, bypass.id))
    if auto is None:
        pass
    else:
        c.execute('INSERT INTO auto VALUES (?, ?)', (interaction.guild.id, auto.id))
    if manager is None:
        pass
    else:
        c.execute('INSERT INTO manager_roles VALUES (?, ?)', (interaction.guild.id, manager.id))

    c.execute('INSERT INTO announcements VALUES (?, ?)', (interaction.guild.id, channel.id))
    conn.commit()
        

    await interaction.response.send_message('Thank you for setting up the bot for your server.\nIf you wish to change the roles the bot is controlling, use </addrole:1145275940008636483> or </removerole:1145275940008636484>.\nYou can also change the Announcement channel using </setchannel:1145275940008636485>.\n> If you wish to reset the bot, use </reset:1145275940168024084>.', ephemeral=True)


    # c.execute('SELECT role_id FROM roles WHERE server_id=?', (interaction.guild.id,))
    # roles = c.fetchall()
    # c.execute('SELECT role_id FROM auto WHERE server_id=?', (interaction.guild.id,))
    # auto_roles = c.fetchall()
    # c.execute('SELECT role_id FROM bypass WHERE server_id=?', (interaction.guild.id,))
    # bypass_roles = c.fetchall()
    # c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
    # channel_id = c.fetchall()
    # c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    # managers = c.fetchall()

    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # setup = support_server.get_channel(1173865122528239698) # setup-logs
    # embed = discord.Embed(title='Role Control | Server Setup', description=f'Setup for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    # embed.add_field(name='Announcements', value=f'{channel.name} *(`{channel_id[0]}`)*', inline=False)
    # if protect is None:
    #     embed.add_field(name='Protect', value='None', inline=False)
    # else:
    #     embed.add_field(name='Protect', value=', '.join([f'<a:arrowr:1138793180494581841> {discord.utils.get(interaction.guild.roles, id=role[0]).name} *(`{role[0]}`)' for role in roles]), inline=False)
    # if auto is None:
    #     embed.add_field(name='Auto Assign', value='None', inline=False)
    # else:
    #     embed.add_field(name='Auto Assign', value=', '.join([f'<a:arrowr:1138793180494581841> {discord.utils.get(interaction.guild.roles, id=role[0]).name} *(`{role[0]}`)' for role in auto_roles]), inline=False)
    # if bypass is None:
    #     embed.add_field(name='Bypass', value='None', inline=False)
    # else:
    #     embed.add_field(name='Bypass', value=', '.join([f'<a:arrowr:1138793180494581841> {discord.utils.get(interaction.guild.roles, id=role[0]).name} *(`{role[0]}`)' for role in bypass_roles]), inline=False)
    # if manager is None:
    #     embed.add_field(name='Manager', value='None', inline=False)
    # else:
    #     embed.add_field(name='Manager', value=', '.join([f'<a:arrowr:1138793180494581841> {discord.utils.get(interaction.guild.roles, id=role[0]).name} *(`{role[0]}`)' for role in managers]), inline=False)
    # await setup.send(embed=embed)


#* Set Channel Command (Admin Only)
@bot.slash_command(name='setchannel', description='Set a channel for announcements.', checks=[setup_command])
async def setchannel(interaction: discord.Interaction, channel: Option(discord.TextChannel, description='Announcement channel.', required=True)):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
    channels = c.fetchall()
    if len(channels) == 0:
        c.execute('INSERT INTO announcements VALUES (?, ?)', (interaction.guild.id, channel.id))
        await interaction.response.send_message(f'Set channel `{channel}` as **Announcements Channel**.', ephemeral=True)
    elif channels[0][0] == channel.id:
        await interaction.response.send_message(f'Channel `{channel}` is already set to **Announcements Channel**.', ephemeral=True)
        return
    else:
        c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
        channel_id = c.fetchone()
        c.execute('UPDATE announcements SET channel_id=? WHERE server_id=?', (channel.id, interaction.guild.id))
        try:
            old_channel = bot.get_channel(channel_id[0])
            old_channel = f"**{old_channel.name}** *(`{old_channel.id}`)*"
        except:
            old_channel = 'None'
        if old_channel is None or old_channel in [None, []]:
            old_channel = 'None'
        await interaction.response.send_message(f'**Announcement Channel** updated from {old_channel} to **{channel.name}** *(`{channel.id}`)*.', ephemeral=True)

    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # setup = support_server.get_channel(1173865122528239698) # setup-logs
    # if len(channels) == 0:
    #     embed = discord.Embed(title='Role Control | Announcement Channel Set (Setup)', description=f'Setup for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    #     embed.add_field(name='Channel', value=f'{channel.name} *(`{channel.id}`)*', inline=False)
    # else:
    #     embed = discord.Embed(title='Role Control | Changed Announcement Channel', description=f'Setup for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    #     embed.add_field(name='Old Channel', value=old_channel, inline=False)
    #     embed.add_field(name='New Channel', value=f'{channel.name} *(`{channel.id}`)*', inline=False)
    # await setup.send(embed=embed)

    conn.commit()

#* Add Role Command (Admin Only)
@bot.slash_command(name='addrole', description='Add a role the bot will control, auto assign, or ignore.', checks=[setup_command])
async def addrole(interaction: discord.Interaction, type: Option(str, description='Type of role to add.', required=True, choices=['protected', 'bypass', 'auto', 'manager']), role: Option(discord.Role, description='Role to add.', required=True)):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    if interaction.author.id in owner:
        pass
    else:
        if not interaction.author.guild_permissions.administrator:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    c.execute('SELECT role_id FROM roles WHERE server_id=?', (interaction.guild.id,))
    roles = c.fetchall()
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (interaction.guild.id,))
    auto_roles = c.fetchall()
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (interaction.guild.id,))
    bypass_roles = c.fetchall()
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    managers = c.fetchall()
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
    channel_id = c.fetchone()
    if channel_id is None:
        return await interaction.response.send_message('You have not setup the bot for your server. Use </setup:1146779160996483114> to setup the bot for your server.', ephemeral=True)
    if type.lower() == 'protected':
        if role.id in [r[0] for r in roles]:
            return await interaction.response.send_message('That role is already in the database.', ephemeral=True)
        if role.id in [r[0] for r in auto_roles] or role.id in [r[0] for r in bypass_roles] or role.id in [r[0] for r in managers]:
            # get what type of role it is
            if role.id in [r[0] for r in auto_roles]:
                type = 'Auto'
            elif role.id in [r[0] for r in bypass_roles]:
                type = 'Bypass'
            elif role.id in [r[0] for r in managers]:
                type = 'Manager'
            return await interaction.response.send_message(f'That role is already in the database as a **{type} Role**.', ephemeral=True)
        c.execute('INSERT INTO roles VALUES (?, ?)', (interaction.guild.id, role.id))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` added to database.\nThe bot will now protect this role from users.', ephemeral=True)
    elif type.lower() == 'bypass':
        if role.id in [r[0] for r in bypass_roles]:
            return await interaction.response.send_message('That role is already in the database.', ephemeral=True)
        if role.id in [r[0] for r in roles] or role.id in [r[0] for r in auto_roles]:
            # get what type of role it is
            if role.id in [r[0] for r in auto_roles]:
                type = 'Auto'
            elif role.id in [r[0] for r in roles]:
                type = 'Protected'
            return await interaction.response.send_message(f'That role is already in the database as a **{type} Role**.', ephemeral=True)
        c.execute('INSERT INTO bypass VALUES (?, ?)', (interaction.guild.id, role.id))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` added to database.\nUsers with this role will now bypass the bot.', ephemeral=True)
    elif type.lower() == 'auto':
        if role.id in [r[0] for r in auto_roles]:
            return await interaction.response.send_message('That role is already in the database.', ephemeral=True)
        if role.id in [r[0] for r in roles] or role.id in [r[0] for r in bypass_roles] or role.id in [r[0] for r in managers]:
            # get what type of role it is
            if role.id in [r[0] for r in roles]:
                type = 'Protected'
            elif role.id in [r[0] for r in bypass_roles]:
                type = 'Bypass'
            elif role.id in [r[0] for r in managers]:
                type = 'Manager'
            return await interaction.response.send_message(f'That role is already in the database as a **{type} Role**.', ephemeral=True)
        c.execute('INSERT INTO auto VALUES (?, ?)', (interaction.guild.id, role.id))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` added to database.\nThe bot will now auto assign this role to new users.', ephemeral=True)
    elif type.lower() == 'manager':
        if role.id in [r[0] for r in managers]:
            return await interaction.response.send_message('That role is already in the database.', ephemeral=True)
        if role.id in [r[0] for r in roles] or role.id in [r[0] for r in auto_roles]:
            # get what type of role it is
            if role.id in [r[0] for r in roles]:
                type = 'Protected'
            elif role.id in [r[0] for r in auto_roles]:
                type = 'Auto'
            return await interaction.response.send_message(f'That role is already in the database as a **{type}** Role.', ephemeral=True)
        c.execute('INSERT INTO manager_roles VALUES (?, ?)', (interaction.guild.id, role.id))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` added to database.\nUsers with this role can now manage the bot.', ephemeral=True)
    else:
        await interaction.response.send_message('Invalid type. Use `protected`, `bypass`, or `auto`.\n</addrole:1145275940008636483>', ephemeral=True)


    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # log_channel = support_server.get_channel(1173865122528239698)
    # embed = discord.Embed(title='Role Control | Role Added', description=f'Role added for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    # embed.add_field(name='Type', value=type, inline=False)
    # embed.add_field(name='Role', value=f'{role.name} *(`{role.id}`)*', inline=False)
    # await log_channel.send(embed=embed)

#* Remove Role Command (Admin Only) (has to be at least one role in the database)
class RemoveRoleView(discord.ui.View):
    def __init__(self, role):
        self.role = role
        super().__init__()

    @discord.ui.button(label='Both', custom_id='both', style=discord.ButtonStyle.blurple)
    async def both(self, button: discord.ui.Button, interaction: discord.Interaction):
        c.execute('DELETE FROM manager_roles WHERE role_id=?', (self.role.id,))
        c.execute('DELETE FROM bypass WHERE role_id=?', (self.role.id,))
        conn.commit()
        await interaction.response.edit_message(content=f'Role `{self.role}` removed from **Manager Roles** and **Bypass Roles**.', view=None)

        # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
        # log_channel = support_server.get_channel(1173865122528239698)
        # embed = discord.Embed(title='Role Control | Role Removed', description=f'Role removed for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
        # embed.add_field(name='Type', value='Bypass & Manager', inline=False)
        # embed.add_field(name='Role', value=f'{self.role.name} *(`{self.role.id}`)*', inline=False)
        # await log_channel.send(embed=embed)

    @discord.ui.button(label='Manager', custom_id='manager', style=discord.ButtonStyle.green)
    async def manager(self, button: discord.ui.Button, interaction: discord.Interaction):
        c.execute('DELETE FROM manager_roles WHERE role_id=?', (self.role.id,))
        conn.commit()
        await interaction.response.edit_message(content=f'Role `{self.role}` removed from **Manager Roles**.', view=None)

        # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
        # log_channel = support_server.get_channel(1173865122528239698)
        # embed = discord.Embed(title='Role Control | Role Removed', description=f'Role removed for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
        # embed.add_field(name='Type', value='Manager', inline=False)
        # embed.add_field(name='Role', value=f'{self.role.name} *(`{self.role.id}`)*', inline=False)
        # await log_channel.send(embed=embed)

    @discord.ui.button(label='Bypass', custom_id='bypass', style=discord.ButtonStyle.green)
    async def bypass(self, button: discord.ui.Button, interaction: discord.Interaction):
        c.execute('DELETE FROM bypass WHERE role_id=?', (self.role.id,))
        conn.commit()
        await interaction.response.edit_message(content=f'Role `{self.role}` removed from **Bypass Roles**.', view=None)

        # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
        # log_channel = support_server.get_channel(1173865122528239698)
        # embed = discord.Embed(title='Role Control | Role Removed', description=f'Role removed for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
        # embed.add_field(name='Type', value='Bypass', inline=False)
        # embed.add_field(name='Role', value=f'{self.role.name} *(`{self.role.id}`)*', inline=False)
        # await log_channel.send(embed=embed)

    @discord.ui.button(label='Cancel', custom_id='cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content='Command cancelled.', view=None)

@bot.slash_command(name='removerole', description='Remove a role the bot was controlling, auto assigning, or ignoring.', checks=[setup_command])
async def removerole(
    interaction: discord.Interaction,
    role: Option(discord.Role, description='Role to remove.', required=True)
    ):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    if interaction.author.id in owner:
        pass
    else:
        if not interaction.author.guild_permissions.administrator:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    c.execute('SELECT role_id FROM roles WHERE server_id=?', (interaction.guild.id,))
    roles = c.fetchall()
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (interaction.guild.id,))
    auto_roles = c.fetchall()
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (interaction.guild.id,))
    bypass_roles = c.fetchall()
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    managers = c.fetchall()
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
    channel_id = c.fetchone()
    if channel_id is None:
        return await interaction.response.send_message('You have not setup the bot for your server. Use </setup:1146779160996483114> to setup the bot for your server.', ephemeral=True)
    # check what type of role it is
    if role.id in [r[0] for r in roles]:
        type = 'Protected'
    elif role.id in [r[0] for r in auto_roles]:
        type = 'Auto'
    elif role.id in [r[0] for r in bypass_roles]:
        type = 'Bypass'
    elif role.id in [r[0] for r in managers]:
        type = 'Manager'
    else:
        return await interaction.response.send_message('Role is not in database.', ephemeral=True)
    
    if type == 'Manager' and role.id in [r[0] for r in bypass_roles] or type == 'Bypass' and role.id in [r[0] for r in managers]:
        return await interaction.response.send_message(f'Role `{role}` is in both **Manager Roles** and **Bypass Roles**.\n> Which one do you want to remove it from?', view=RemoveRoleView(role=role), ephemeral=True)
    
    if type == 'Protected':
        c.execute('DELETE FROM roles WHERE role_id=?', (role.id,))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` removed from **{type} Roles**.\nThe bot will no longer protect this role from users.', ephemeral=True)
    elif type == 'Auto':
        c.execute('DELETE FROM auto WHERE role_id=?', (role.id,))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` removed from **{type} Roles**.\nThe bot will no longer auto assign this role to new users.', ephemeral=True)
    elif type == 'Bypass':
        c.execute('DELETE FROM bypass WHERE role_id=?', (role.id,))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` removed from **{type} Roles**.\nUsers with this role will no longer bypass the bot.', ephemeral=True)
    elif type == 'Manager':
        c.execute('DELETE FROM manager_roles WHERE role_id=?', (role.id,))
        conn.commit()
        await interaction.response.send_message(f'Role `{role}` removed from **{type} Roles**.\nUsers with this role can no longer manage the bot.', ephemeral=True)

    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # log_channel = support_server.get_channel(1173865122528239698)
    # embed = discord.Embed(title='Role Control | Role Removed', description=f'Role removed for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    # embed.add_field(name='Type', value=type, inline=False)
    # embed.add_field(name='Role', value=f'{role.name} *(`{role.id}`)*', inline=False)
    # await log_channel.send(embed=embed)

#* removenulls (Admin Only)
@bot.slash_command(name='removenulls', description='Remove all \'0\'s from the database.', checks=[setup_command])
async def removenulls(interaction: discord.Interaction):
    if interaction.author.id in owner:
        pass
    else:
        if not interaction.author.guild_permissions.administrator:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    c.execute('DELETE FROM roles WHERE role_id=0')
    c.execute('DELETE FROM auto WHERE role_id=0')
    c.execute('DELETE FROM bypass WHERE role_id=0')
    c.execute('DELETE FROM manager_roles WHERE role_id=0')
    conn.commit()
    await interaction.response.send_message('Removed all \'0\'s *(Invalid Roles)* from the database.', ephemeral=True)

    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # log_channel = support_server.get_channel(1173865122528239698)
    # embed = discord.Embed(title='Role Control | Removed Nulls', description=f'Removed all \'0\'s *(Invalid Roles)* for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    # await log_channel.send(embed=embed)

#* showsetup Command (Admin Only)
@bot.slash_command(name='showsetup', description='Shows the bot\'s setup for your server.', checks=[role_command])
async def showsetup(interaction: discord.Interaction):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    manager_role_id = c.fetchone()
    if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
        pass
    elif manager_role_id:
        manager_role = discord.utils.get(interaction.author.roles, id=manager_role_id[0])
        if manager_role:
            pass
        else:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    else:
        return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    
    c.execute('SELECT role_id FROM roles WHERE server_id=?', (interaction.guild.id,))
    roles = c.fetchall()
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (interaction.guild.id,))
    auto_roles = c.fetchall()
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (interaction.guild.id,))
    bypass_roles = c.fetchall()
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    managers = c.fetchall()
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (interaction.guild.id,))
    channel_id = c.fetchone()

    if channel_id is None:
        return await interaction.response.send_message('You have not set up the bot for your server. Use </setup:1146779160996483114> to set up the bot for your server.', ephemeral=True)
    
    embed = discord.Embed(title='Role Control | Roles', description='Discord Bot to control & manage roles.', color=0x00ff00)

    for role_list, name in [(roles, 'Roles'), (auto_roles, 'Auto Roles'), (bypass_roles, 'Bypass Roles'), (managers, 'Manager Roles')]:
        formatted_roles = '\n'.join([f'<a:arrowr:1138793180494581841> <@&{role[0]}> *(`{role[0]}`)*' for role in role_list])
        if formatted_roles:
            embed.add_field(name=name, value=formatted_roles, inline=False)
        else:
            embed.add_field(name=name, value='None', inline=False)

    embed.add_field(name='Announcement Channel', value=f'<#{channel_id[0]}> *({channel_id[0]})*', inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

#* Role Info Command (Admin Only)
@bot.slash_command(name='roleinfo', description='Get info about a role.', checks=[role_command])
async def roleinfo(interaction: discord.Interaction, role: Option(discord.Role, description='Role to get info about.', required=True)):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    manager_role_id = c.fetchone()
    if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
        pass
    elif manager_role_id:
        manager_role = discord.utils.get(interaction.author.roles, id=manager_role_id[0])
        if manager_role:
            pass
        else:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    else:
        return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    c.execute('SELECT role_id FROM roles WHERE server_id=?', (interaction.guild.id,))
    roles = c.fetchall()
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (interaction.guild.id,))
    auto_roles = c.fetchall()
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (interaction.guild.id,))
    bypass_roles = c.fetchall()
    embed = discord.Embed(title=f'Role Info | {role.name}', description=f'Role ID: {role.id}', color=role.color)
    # position (display position number and role above and below
    # get roles above and below
    roles_above = []
    roles_below = []
    max_position = 0

    # display name of role above and below
    for r in interaction.guild.roles:
        if r.position == role.position - 1:
            roles_above.append(r.name)
        if r.position == role.position + 1:
            roles_below.append(r.name)
        if r.position > max_position:
            max_position = r.position
    if len(roles_above) == 0:
        roles_above = 'None'
    if len(roles_below) == 0:
        roles_below = 'None'

    # check if the role is below the bot's highest role
    c.execute('SELECT role_id FROM bot_role WHERE server_id=?', (interaction.guild.id,))
    bot_role_id = c.fetchone()
    try:
        bot_role = discord.utils.get(interaction.guild.roles, id=bot_role_id[0])
    except:
        bot_role = None
        logger.error(f'Error getting bot role in roleinfo command: {bot_role}')

    if bot_role is None:
        managed_role = '<a:alert:1159043049498882048> Inconclusive?'
    else:
        if role.id == bot_role.id:
            managed_role = 'True *(Bot\'s Personal Role!)*'
        elif role.position < bot_role.position:
            managed_role = 'True'
        else:
            managed_role = 'False'

    # format below and above
    roles_above = str(roles_above).replace('[', '').replace(']', '').replace("'", '')
    roles_below = str(roles_below).replace('[', '').replace(']', '').replace("'", '')
    embed.add_field(name='Position', value=f'{role.position}/{max_position}\n> **Below:** {roles_below}\n> **Above:** {roles_above}', inline=False)
    embed.add_field(name='Created', value=role.created_at, inline=False)
    embed.add_field(name='Mentionable', value=role.mentionable, inline=False)
    embed.add_field(name='Manageable *(Bot can Manage role)*', value=managed_role, inline=False)
    embed.add_field(name='Hoisted *(Displays seperately)*', value=role.hoist, inline=False)
    # permissions
    perms = []
    for perm in role.permissions:
        if perm[1] == True:
            # perms.append(f'- **{perm[0]}:** {perm[1]}')
            perms.append(f'- **{perm[0]}**')
    perms = '\n'.join(perms)
    perms = str(perms).replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace(',', '').replace("'", '')
    if len(perms) > 1024:
        permstxt = []
        for perm in role.permissions:
            if perm[1] == True:
                # permstxt.append(f'- {perm[0]}: {perm[1]}')
                permstxt.append(f'- {perm[0]}')
        permstxt = '\n'.join(permstxt)
        permstxt = str(permstxt).replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace(',', '').replace("'", '')
        with open('perms.txt', 'w') as f:
            f.write('Permissions for the role: ' + role.name + '\n----------------------------------\n')
            f.write(permstxt)
        with open('perms.txt', 'rb') as f:
            embed.add_field(name='Permissions', value=f'*Too many permissions to display. Sending in a text file.*', inline=False)
            await interaction.response.send_message(embed=embed, file=discord.File(f, 'perms.txt'), ephemeral=True)
        os.remove('perms.txt')
    else:
        embed.add_field(name='Permissions', value=f'Perms the role has:\n{perms}', inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

#* Role Users Command (Managers Only)
@bot.slash_command(name='roleusers', description='List all users with a role.', checks=[role_command])
async def roleusers(interaction: discord.Interaction, role: Option(discord.Role, description='Role to get users from.', required=True)):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    manager_role_id = c.fetchone()
    if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
        pass
    elif manager_role_id:
        manager_role = discord.utils.get(interaction.author.roles, id=manager_role_id[0])
        if manager_role:
            pass
        else:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    else:
        return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    users = []
    

    for user in role.members:
        users.append(f'- **{user.name}** *({user.id})*')
    users = '\n'.join(users)
    users = str(users).replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace(',', '').replace("'", '')

    # users format for file
    userstxt = []

    if len(users) > 1024:
        userstxt = []
        for user in role.members:
            userstxt.append(f'- {user.name} ({user.id})')
        userstxt = '\n'.join(userstxt)
        userstxt = str(userstxt).replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace(',', '').replace("'", '')
        with open('users.txt', 'w') as f:
            f.write('Users with the role: ' + role.name + '\n----------------------------------\n')
            f.write(userstxt)
        with open('users.txt', 'rb') as f:
            embed = discord.Embed(title=f'Role Users | {role.name}', description=f'Role ID: {role.id}', color=role.color)
            embed.add_field(name='Users', value=f'*Too many users to display. Sending in a text file.*', inline=False)
            await interaction.response.send_message(embed=embed, file=discord.File(f, 'users.txt'), ephemeral=True)
        os.remove('users.txt')
    else:
        embed = discord.Embed(title=f'Role Users | {role.name}', description=f'Role ID: {role.id}', color=role.color)
        embed.add_field(name='Users', value=f'{users}', inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


#* rolehierarchy Command (Managers Only)
@bot.slash_command(name='rolehierarchy', description='List all roles in the server.', checks=[user_command])
async def rolehierarchy(interaction: discord.Interaction):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    roles = interaction.guild.roles  # Get all roles in the server
    roles.sort(key=lambda x: x.position, reverse=True)  # Sort roles by position in descending order

    roles_formatted = []
    rolestxt_formatted = []
    for role in roles:
        roles_formatted.append(f'- {role.mention if role.id != interaction.guild.id else "@everyone"} *({role.id})*')
        rolestxt_formatted.append(f'- {role.name if role.id != interaction.guild.id else "everyone"} ({role.id})')

    roles_text = '\n'.join(roles_formatted)
    rolestxt_text = '\n'.join(rolestxt_formatted)

    # Check if the roles fit within a single message or need to be saved to a file
    if len(rolestxt_text) > 1024 or len(roles_text) > 1024:
        with open('roles.txt', 'w') as f:
            f.write(f'Roles in the server: {interaction.guild.name}\n----------------------------------\n')
            f.write(rolestxt_text)

        with open('roles.txt', 'rb') as f:
            embed = discord.Embed(title=f'Role Hierarchy | {interaction.guild.name}', description=f'Server ID: {interaction.guild.id}', color=0x00ff00)
            embed.add_field(name='Roles', value=f'*Too many roles to display. Sending in a text file.*', inline=False)
            await interaction.response.send_message(embed=embed, file=discord.File(f, 'roles.txt'), ephemeral=True)

        os.remove('roles.txt')
    else:
        embed = discord.Embed(title=f'Role Hierarchy | {interaction.guild.name}', description=f'Server ID: {interaction.guild.id}', color=0x00ff00)
        embed.add_field(name='Roles', value=roles_text, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

#* Reset Command (Admin Only)
@bot.slash_command(name='reset', description='Reset the bot for your server.', checks=[setup_command])
async def reset(interaction: discord.Interaction):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    if interaction.author.id in owner:
        pass
    else:
        if not interaction.author.guild_permissions.administrator:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    c.execute('DELETE FROM roles WHERE server_id=?', (interaction.guild.id,))
    c.execute('DELETE FROM bypass WHERE server_id=?', (interaction.guild.id,))
    c.execute('DELETE FROM auto WHERE server_id=?', (interaction.guild.id,))
    c.execute('DELETE FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    c.execute('DELETE FROM announcements WHERE server_id=?', (interaction.guild.id,))
    conn.commit()
    await interaction.response.send_message('Reset server data.', ephemeral=True)

    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # log_channel = support_server.get_channel(1173865122528239698)
    # embed = discord.Embed(title='Role Control | Server Reset', description=f'Server reset for **{interaction.guild.name}** *(`{interaction.guild.id}`)*', color=0x00ff00)
    # await log_channel.send(embed=embed)

#* Temp Role Command (Managers Only)
def parse_duration(duration):
    total_minutes = 0
    for part in re.findall(r'(\d+[wdhms])', duration):
        unit = part[-1]
        value = int(part[:-1])

        if unit == 'w':
            total_minutes += value * 7 * 24 * 60
        elif unit == 'd':
            total_minutes += value * 24 * 60
        elif unit == 'h':
            total_minutes += value * 60
        elif unit == 'm':
            total_minutes += value
        elif unit == 's':
            total_minutes += value / 60

    return total_minutes

@bot.slash_command(name='temprole', description='Give or remove a temporary role to a user.', checks=[role_command])
async def temprole(
    interaction: discord.Interaction,
    action: Option(str, description='`give` or remove', required=True, choices=['give', 'remove']),
    role: Option(discord.Role, description='Role to give or remove.', required=True),
    user: Option(discord.Member, description='User to give or remove the role from.', required=True),
    duration: Option(str, description='Duration. Format: 1w 1d 1h 1m 1s (Ignore if removing)', required=False)
    ):
    if interaction.guild is None:
        return await interaction.response.send_message('**Error:** `This command cannot be used in private messages.`', ephemeral=True)
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (interaction.guild.id,))
    manager_role_id = c.fetchone()
    if interaction.author.guild_permissions.administrator or interaction.author.id in owner:
        pass
    elif manager_role_id:
        manager_role = discord.utils.get(interaction.author.roles, id=manager_role_id[0])
        if manager_role:
            pass
        else:
            return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    else:
        return await interaction.response.send_message('**Error:** `You do not have permission to use this command.`', ephemeral=True)
    
    if role.position >= interaction.author.top_role.position:
        if interaction.author.id == interaction.guild.owner_id:
            pass
        else:
            return await interaction.response.send_message('**Error:** `You cannot give a role higher or equal to your highest role.`', ephemeral=True)
        
    if role.position >= interaction.guild.me.top_role.position:
        return await interaction.response.send_message('**Error:** `You cannot give a role higher or equal to my highest role.`', ephemeral=True)
    
    if action not in ("give", "remove"):
        return await interaction.response.send_message('Invalid action. Use `give` or `remove`.', ephemeral=True)
    if duration is None:
        if action == "remove":
            pass
        else:
            return await interaction.response.send_message('Please specify a duration. Use `1w 1d 1h 1m 1s`.', ephemeral=True)
    else:
        total_minutes = parse_duration(duration)

        if total_minutes == 0:
            return await interaction.response.send_message('Invalid duration. Use `1w 1d 1h 1m 1s`.', ephemeral=True)

        end_time = datetime.now() + timedelta(minutes=total_minutes)

    if action == "remove":
        await user.remove_roles(role)
        # delete from database
        c.execute("DELETE FROM temp_roles WHERE server_id=? AND role_id=? AND user_id=?", (interaction.guild.id, role.id, user.id))
        conn.commit()
        try:
            await user.send(f'Your temporary role `{role.name}` in **{interaction.guild.name}** *(`{interaction.guild.id}`)* has been removed manully by **{interaction.author.name}** *(`{interaction.author.id}`)*.')
        except:
            pass
        return await interaction.response.send_message(f'Removed {role.mention} from {user.mention} manually.', ephemeral=True)
    elif action == "give":
        await user.add_roles(role)
        # add to database
        c.execute("INSERT INTO temp_roles VALUES (?, ?, ?, ?)", (interaction.guild.id, role.id, user.id, end_time))
        conn.commit()
        return await interaction.response.send_message(f'Gave {role.mention} to {user.mention} for `{duration}`.', ephemeral=True)
    else:
        return await interaction.response.send_message('Invalid action. Use `give` or `remove`.', ephemeral=True)


## ? Dev Commands

#* Dev help Command
@bot.command()
@commands.is_owner()
async def devhelp(ctx):
    embed = discord.Embed(title='Role Control | Dev Help', description='Discord Bot to control & manage roles.', color=0x00ff00)
    embed.add_field(name='rc-inviteme <guild id>', value='Get a invite link for a server.', inline=False)
    embed.add_field(name='rc-servers', value='List all servers the bot is in.', inline=False)
    embed.add_field(name='rc-serverinfo <guild id>', value='Get info about a server the bot is in.', inline=False)
    embed.add_field(name='rc-devshowsetup <guild id>', value='Show the bot\'s setup for your server.', inline=False)
    embed.add_field(name='rc-leave <guild id>', value='Leave a server.', inline=False)
    embed.add_field(name='rc-announce', value='Send a announcement to all servers the bot is in.\nUse **[e:emoji_id]** to use a emoji.', inline=False)
    embed.add_field(name='rc-announce_to <guild ids>', value='Send a announcement to specific servers.\nUse **[e:emoji_id]** to use a emoji.', inline=False)
    embed.add_field(name='rc-forcereset <guild id>', value='Force a server to reset it\'s setup.', inline=False)
    embed.add_field(name='rc-blacklist <add / remove> <guild id> [reason]', value='Blacklist a server and server owner.', inline=False)
    embed.add_field(name='rc-listblacklist', value='List all blacklisted servers.', inline=False)
    embed.add_field(name='rc-dmpurge', value='Delete all messages in yours and the bot\'s DMs.', inline=False)
    embed.add_field(name='rc-getemojis <guild id>', value='Get all emojis in a server.', inline=False)
    embed.add_field(name='rc-embed <#channel> "<title>" "<description>" "<footer>" <colour>', value='Send a embed.', inline=False)
    embed.add_field(name='rc-showrawdata <guild id>', value='Show raw data for a server.', inline=False)
    embed.add_field(name='rc-showdb', value='Show the structure of the database.', inline=False)
    embed.add_field(name='rc-givechannelaccess <#channel> [guild id]', value='Gives you access to the mentioned channel.', inline=False)
    await ctx.reply(embed=embed)

#* givechannelaccess Command (can be used in DMs)
@bot.command()
@commands.is_owner()
async def givechannelaccess(ctx, channel: discord.TextChannel, guild_id: int=None):
    if guild_id is None:
        if ctx.guild is None:
            return await ctx.reply('**Error:** `You must specify a guild id or use this command in a server.`')
        guild_id = ctx.guild.id

    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('**Error:** `That guild does not exist.`')
    
    if guild is None:
        return await ctx.reply('**Error:** `That guild does not exist.`')
        
    else:
        try:
            await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        except:
            return await ctx.reply('**Error:** `I do not have permission to edit that channel.`')
        await ctx.reply(f'Gave you access to {channel.mention} | **{channel.name}** *(`{channel.id}`)*\nGuild: **{guild.name}** *(`{guild.id}`)*')

#* Show Database Command
@bot.command()
@commands.is_owner()
async def showdb(ctx):
    c.execute("PRAGMA table_info(roles)")
    roles = c.fetchall()
    c.execute("PRAGMA table_info(bypass)")
    bypass = c.fetchall()
    c.execute("PRAGMA table_info(auto)")
    auto = c.fetchall()
    c.execute("PRAGMA table_info(bot_role)")
    bot_role = c.fetchall()
    c.execute("PRAGMA table_info(announcements)")
    announcements = c.fetchall()
    c.execute("PRAGMA table_info(manager_roles)")
    manager_roles = c.fetchall()
    c.execute("PRAGMA table_info(temp_roles)")
    temp_roles = c.fetchall()
    c.execute("PRAGMA table_info(self_roles)")
    self_roles = c.fetchall()
    c.execute("PRAGMA table_info(self_role_templates)")
    self_role_templates = c.fetchall()
    
    embed = discord.Embed(title='Role Control | Database', description='Database structure.', color=0x00ff00)
    embed.add_field(name='roles', value=f'{roles}', inline=False)
    embed.add_field(name='bypass', value=f'{bypass}', inline=False)
    embed.add_field(name='auto', value=f'{auto}', inline=False)
    embed.add_field(name='bot_role', value=f'{bot_role}', inline=False)
    embed.add_field(name='announcements', value=f'{announcements}', inline=False)
    embed.add_field(name='manager_roles', value=f'{manager_roles}', inline=False)
    embed.add_field(name='temp_roles', value=f'{temp_roles}', inline=False)
    embed.add_field(name='self_roles', value=f'{self_roles}', inline=False)
    embed.add_field(name='self_role_templates', value=f'{self_role_templates}', inline=False)
    await ctx.reply(embed=embed)

#* Show Raw Data Command
@bot.command()
@commands.is_owner()
async def showrawdata(ctx, guild_id: int):
    # send embed with server info
    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('That server does not exist or I am not in that server.')
    embed = discord.Embed(title=f'Raw Data | {guild.name}', description=f'Raw data for {guild.name} is in the file.', color=0x00ff00)
    embed.add_field(name='Server ID', value=f'{guild.id}', inline=False)
    embed.add_field(name='Owner', value=f'{guild.owner.name} *({guild.owner.id})*', inline=False)
    embed.add_field(name='Members', value=f'Total: {guild.member_count}\nUsers: {len([member for member in guild.members if not member.bot])}\nBots: {len([member for member in guild.members if member.bot])}', inline=False)
    embed.add_field(name='Channels', value=f'{len(guild.channels)}', inline=False)
    embed.add_field(name='Roles', value=f'{len(guild.roles)}', inline=False)
    embed.add_field(name='Created', value=f'{guild.created_at}', inline=False)
    embed.add_field(name='Verification Level', value=f'{guild.verification_level}', inline=False)
    embed.add_field(name='Boosts', value=f'{guild.premium_subscription_count}', inline=False)
    embed.add_field(name='Boost Level', value=f'{guild.premium_tier}', inline=False)
    embed.add_field(name='Emojis', value=f'{len(guild.emojis)}', inline=False)

    # create file with raw database data
    c.execute('SELECT * FROM roles WHERE server_id=?', (guild.id,))
    roles = c.fetchall()
    c.execute('SELECT * FROM bypass WHERE server_id=?', (guild.id,))
    bypass = c.fetchall()
    c.execute('SELECT * FROM auto WHERE server_id=?', (guild.id,))
    auto = c.fetchall()
    c.execute('SELECT * FROM bot_role WHERE server_id=?', (guild.id,))
    bot_role = c.fetchall()
    c.execute('SELECT * FROM announcements WHERE server_id=?', (guild.id,))
    announcements = c.fetchall()
    c.execute('SELECT * FROM manager_roles WHERE server_id=?', (guild.id,))
    manager_roles = c.fetchall()
    c.execute('SELECT * FROM temp_roles WHERE server_id=?', (guild.id,))
    temp_roles = c.fetchall()
    c.execute('SELECT * FROM self_roles WHERE server_id=?', (guild.id,))
    self_roles = c.fetchall()
    c.execute('SELECT * FROM self_role_templates WHERE server_id=?', (guild.id,))
    self_role_templates = c.fetchall()
    
    # create formatted file
    with open('raw_data.txt', 'w') as f:
        f.write('Raw Data for the server: ' + guild.name + '\n----------------------------------\n')
        f.write('Roles the bot prevents users from having:\n')
        for role in roles:
            f.write(f'{role[1]}\n')
        
        f.write('\nRoles the bot will ignore when preventing roles:\n')
        for role in bypass:
            f.write(f'{role[1]}\n')
        
        f.write('\nRoles the bot will give to users when they join:\n')
        for role in auto:
            f.write(f'{role[1]}\n')
        
        f.write('\nThe bot\'s role for the server:\n')
        for role in bot_role:
            f.write(f'{role[1]}\n')
        
        f.write('\nRoles that can manage the bot:\n')
        for role in manager_roles:
            f.write(f'{role[1]}\n')
        
        f.write('\nThe bot\'s channel for announcements:\n')
        for channel in announcements:
            f.write(f'{channel[1]}\n')
        
        f.write('\nTemp roles:\n')
        for role in temp_roles:
            for user_id, role_id, minutes in temp_roles:
                user = bot.get_user(user_id)
                role = bot.get_guild(guild.id).get_role(role_id)
                f.write(f'{user} ({user_id}) has role {role} ({role_id}) for {minutes} minutes\n')
        
        f.write('\nSelf roles:\n')
        for row in self_roles:
            server_id, channel_id, message_id, menu_type, role_id, emoji = row
            channel = guild.get_channel(channel_id)
            if channel is None:
                print(f"Channel with ID {channel_id} not found in the guild.")
                continue

            try:
                message = await channel.fetch_message(message_id)
                self_roles_list = []
                role = guild.get_role(role_id)
                self_roles_list.append(f'{role.name} ({role.id}) > {emoji}')
                self_roles_list = '\n'.join(self_roles_list)
                f.write(f'Channel: {channel.name} ({channel.id})\nMessage: {message.jump_url}\nRoles:\n{self_roles_list}\n\n')
            except discord.errors.NotFound:
                print(f"Message with ID {message_id} not found in channel {channel.id}")
            except Exception as e:
                print(f"An error occurred while processing channel {channel.id}: {e}")
        
        f.write('\nSelf role templates:\n')
        f.write('Not yet implemented.\n')
        #for role in self_role_templates:
        #    f.write(f'{role[1]}\n')

    with open('raw_data.txt', 'rb') as f:
        await ctx.reply(embed=embed, file=discord.File(f, 'raw_data.txt'))
    try:
        os.remove('raw_data.txt')
    except:
        pass

#* Embed Command
@bot.command()
@commands.is_owner()
async def embed(ctx, channel: discord.TextChannel, title: str, description: str, footer: str, colour: str):
    if channel.guild != ctx.guild:
        return await ctx.reply('**Error:** `That channel is not in this server?!`')
    try:
        colour = int(colour, 16)
    except:
        return await ctx.reply('**Error:** `Invalid hex colour.`')
    embed = discord.Embed(title=title, description=description, color=colour)
    embed.set_footer(text=footer)
    # ask if they want a role mentioned
    question = discord.Embed(title='Mention', description='Do you want to mention a role? Reply with "yes" or "no".', color=0x00ff00)
    await ctx.reply(embed=question)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        reply = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        return await ctx.reply('**Error:** `You took too long to reply.`')
    if reply.content.lower() == 'yes':
        question = discord.Embed(title='Mention', description='What role do you want to mention? Reply with the role id or mention.', color=0x00ff00)
        await ctx.reply(embed=question)
        try:
            reply = await bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.reply('**Error:** `You took too long to reply.`')
        try:
            role = await commands.RoleConverter().convert(ctx, reply.content)
        except:
            return await ctx.reply('**Error:** `Invalid role.`')
        await ctx.reply(f'Mentioning **{role.name}** *({role.id})*.')
        await channel.send(role.mention, embed=embed)
    elif reply.content.lower() == 'no':
        await ctx.reply('Not mentioning a role. Sending embed.')
        await channel.send(embed=embed)
    await ctx.reply(f'Sent embed to {channel.mention}.')

#* Get Emojis Command
@bot.command()
@commands.is_owner()
async def getemojis(ctx, guild_id: int):
    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('That server does not exist or I am not in that server.')
    emojis = []
    for emoji in guild.emojis:
        emojis.append(f'<:{emoji.name}:{emoji.id}>')
    emojis = '\n'.join(emojis)
    emojis = str(emojis).replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace(',', '').replace("'", '')
    if len(emojis) > 1024:
        with open('emojis.txt', 'w') as f:
            f.write('Emojis for the server: ' + guild.name + '\n----------------------------------\n')
            f.write(emojis)
        with open('emojis.txt', 'rb') as f:
            embed = discord.Embed(title=f'Emojis | {guild.name}', description=f'Emojis for {guild.name}', color=0x00ff00)
            embed.add_field(name='Emojis', value=f'*Too many emojis to display.*', inline=False)
            await ctx.reply(embed=embed, file=discord.File(f, 'emojis.txt'))
        os.remove('emojis.txt')
    else:
        embed = discord.Embed(title=f'Emojis | {guild.name}', description=f'Emojis for {guild.name}', color=0x00ff00)
        embed.add_field(name='Emojis', value=f'{emojis}', inline=False)
        await ctx.reply(embed=embed)


#* Server Info Command
@bot.command()
@commands.is_owner()
async def serverinfo(ctx, guild_id: int):
    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('That server does not exist or I am not in that server.')
    
    embed = discord.Embed(title=f'Server Info | {guild.name}', description=f'Server ID: {guild.id}', color=0x00ff00)
    embed.add_field(name='Owner', value=f'{guild.owner.name} *({guild.owner.id})*', inline=False)
    embed.add_field(name='Members', value=f'Total: {guild.member_count}\nUsers: {len([member for member in guild.members if not member.bot])}\nBots: {len([member for member in guild.members if member.bot])}', inline=False)
    embed.add_field(name='Channels', value=f'{len(guild.channels)}', inline=False)
    embed.add_field(name='Roles', value=f'{len(guild.roles)}', inline=False)
    embed.add_field(name='Created', value=f'{guild.created_at}', inline=False)
    embed.add_field(name='Verification Level', value=f'{guild.verification_level}', inline=False)
    embed.add_field(name='Boosts', value=f'{guild.premium_subscription_count}', inline=False)
    embed.add_field(name='Boost Level', value=f'{guild.premium_tier}', inline=False)
    embed.add_field(name='Emojis', value=f'{len(guild.emojis)}', inline=False)
    await ctx.reply(embed=embed)

#* Dev Show Setup Command
@bot.command()
@commands.is_owner()
async def devshowsetup(ctx, guild_id: int):
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (guild_id,))
    manager_roles = c.fetchone()
    c.execute('SELECT role_id FROM roles WHERE server_id=?', (guild_id,))
    roles = c.fetchall()
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (guild_id,))
    auto_roles = c.fetchall()
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (guild_id,))
    bypass_roles = c.fetchall()
    c.execute('SELECT role_id FROM manager_roles WHERE server_id=?', (guild_id,))
    managers = c.fetchall()
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (guild_id,))
    channel_id = c.fetchone()
    if channel_id is None:
        return await ctx.reply('This server has not setup the bot!')
    await ctx.reply('Getting roles from database...')
    await asyncio.sleep(1)
    embed = discord.Embed(title=f'Role Control | {bot.get_guild(guild_id).name}\'s Setup', description='Discord Bot to control & manage roles.', color=0x00ff00)
    if len(roles) == 0 or roles == '0':
        embed.add_field(name='Control Roles', value='0 Roles Set', inline=False)
    else:
        embed.add_field(name='Control Roles', value=f'{len(roles)} Roles Set', inline=False)

    if len(auto_roles) == 0 or auto_roles == '0':
        embed.add_field(name='Auto Roles', value='0 Roles Set', inline=False)
    else:
        embed.add_field(name='Auto Roles', value=f'{len(auto_roles)} Roles Set', inline=False)

    if len(bypass_roles) == 0 or bypass_roles == '0':
        embed.add_field(name='Bypass Roles', value='0 Roles Set', inline=False)
    else:
        embed.add_field(name='Bypass Roles', value=f'{len(bypass_roles)} Roles Set', inline=False)

    if len(managers) == 0 or managers == '0':
        embed.add_field(name='Manager Roles', value='0 Roles Set', inline=False)
    else:
        embed.add_field(name='Manager Roles', value=f'{len(manager_roles)} Roles Set', inline=False)
    if channel_id == None:
        embed.add_field(name='Announcement Channel', value='Not set!?', inline=False)
    else:
        embed.add_field(name='Announcement Channel', value=f'**#{bot.get_channel(channel_id[0]).name}** *({channel_id[0]})*', inline=False)
    await ctx.reply(embed=embed)


#* Dmpurge Command
@bot.command()
@commands.is_owner()
async def dmpurge(ctx):
    channel = ctx.message.channel
    deleted_count = 0

    if isinstance(channel, discord.TextChannel):
        dm_channel = ctx.author.dm_channel
        if not dm_channel:
            dm_channel = await ctx.author.create_dm()
        async for message in dm_channel.history(limit=None):
            if message.author == bot.user:
                await message.delete()
                deleted_count += 1
        if deleted_count == 0:
            await ctx.send("No messages to delete.")
        else:
            await ctx.send(f"Deleted {deleted_count} message(s) in your DMs.")

#* Invite Command
@bot.command()
@commands.is_owner()
async def inviteme(ctx, guild_id: int):
    # check if server exists
    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('That server does not exist.')
    # check if the bot is in the server
    if guild not in bot.guilds:
        return await ctx.reply('I am not in that server.')
    # create invite link that doesn't expire and can only be used once
    try:
        for channel in guild.text_channels:
            try:
                invite = await channel.create_invite(max_uses=1, max_age=3600, reason=f'Invite requested by bot developer {ctx.author.name} *({ctx.author.id})*')
                break
            except:
                pass
    except:
        return await ctx.reply('I failed to create a invite link for that server.')
    await ctx.reply(f'Invite link for {guild.name}: {invite}')

#* Servers Command (List all servers the bot is in - Name and ID. Each server is on a new line, and format is: Server Name (Server ID))
@bot.command()
@commands.is_owner()
async def servers(ctx):
    servers = []
    for guild in bot.guilds:
        servers.append(f'- **{guild.name}** *({guild.id})*')
    servers = '\n'.join(servers)
    embed = discord.Embed(title='Role Control | Servers', description='Discord Bot to control & manage roles.', color=0x00ff00)
    embed.add_field(name='Servers', value=f'{servers}', inline=False)
    await ctx.reply(embed=embed)


#* Leave Command
@bot.command()
@commands.is_owner()
async def leave(ctx, guild_id: int):
    # check if server exists
    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('That server does not exist.')
    # check if the bot is in the server
    if guild not in bot.guilds:
        return await ctx.reply('I am not in that server.')
    await guild.leave()
    await ctx.reply(f'Left {guild.name}.')

#* Announce Command
@bot.command()
@commands.is_owner()
async def announce(ctx):
    await ctx.reply('Send an announcement to all servers the bot is in...')
    await asyncio.sleep(1)
    await ctx.reply('Please enter the announcement.\nYou have 5 minutes to respond. If you wish to cancel, type `cancel`.')

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=300)
    except asyncio.TimeoutError:
        await ctx.reply('You took too long to respond.')
    else:
        if msg.content.lower() == 'cancel':
            await ctx.reply('Announcement cancelled.')
        else:
            # Emojis (Support for users wihout nitro - converts emoji codes to emojis)
            if '[e:' in msg.content:
                emojis = re.findall(r'\[e:(\d+)\]', msg.content)
                for emoji in emojis:
                    try:
                        emoji = bot.get_emoji(int(emoji))
                        msg.content = msg.content.replace(f'[e:{emoji.id}]', f'{emoji}')
                    except:
                        msg.content = msg.content.replace(f'[e:{emoji}]', '*`?Unknown Emoji?`*')
            embed = discord.Embed(title='Announcement', description=f'{msg.content}', color=0x00ff00)
            if ctx.author.avatar.url:
                embed.set_author(name=f'{ctx.author.name}', icon_url=f'{ctx.author.avatar.url}')
            else:
                embed.set_author(name=f'{ctx.author.name}', icon_url=f'{ctx.author.default_avatar.url}')
            embed.set_footer(text=f'This announcement has been sent to all servers the bot is in.')

            for guild in bot.guilds:
                try:
                    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (guild.id,))
                    channel_id = c.fetchone()[0]
                    channel = bot.get_channel(channel_id)
                    await channel.send(embed=embed)
                except:
                    try:
                        for channel in guild.text_channels:
                            try:
                                await channel.send(f'{guild.owner.mention}\nIf you would like to set a channel for announcements, use </setchannel:1145275940008636482>.')
                                break
                            except:
                                continue
                    except:
                        await guild.owner.send(f'**NOTICE:** I failed to send the announcement to the server **{guild.name}** *({guild.id})*\nPlease make sure I have the permission `Administrator` and that there is at least one text channel.', embed=embed)
            await ctx.reply('Announcement sent to all servers.')

#* Announce to Command (Announce to a specific server(s))
@bot.command()
@commands.is_owner()
async def announce_to(ctx, guilds: commands.Greedy[int]):
    if not guilds:
        return await ctx.reply('Please specify server(s) to announce to.')
    await ctx.reply('Send an announcement to specified servers...')
    await asyncio.sleep(1)
    await ctx.reply('Please enter the announcement.\nYou have 5 minutes to respond. If you wish to cancel, type `cancel`.')

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=300)
    except asyncio.TimeoutError:
        await ctx.reply('You took too long to respond.')
    else:
        if msg.content.lower() == 'cancel':
            await ctx.reply('Announcement cancelled.')
        else:
            # Emojis (Support for users wihout nitro - converts emoji codes to emojis)
            if '[e:' in msg.content:
                emojis = re.findall(r'\[e:(\d+)\]', msg.content)
                for emoji in emojis:
                    try:
                        emoji = bot.get_emoji(int(emoji))
                        msg.content = msg.content.replace(f'[e:{emoji.id}]', f'{emoji}')
                    except:
                        msg.content = msg.content.replace(f'[e:{emoji}]', '*`?Unknown Emoji?`*')
            embed = discord.Embed(title='Announcement', description=f'{msg.content}', color=0x00ff00)
            if ctx.author.avatar.url:
                embed.set_author(name=f'{ctx.author.name}', icon_url=f'{ctx.author.avatar.url}')
            else:
                embed.set_author(name=f'{ctx.author.name}', icon_url=f'{ctx.author.default_avatar.url}')
            embed.set_footer(text=f'This announcement has been sent to specific servers.')

            for guild_id in guilds:
                try:
                    guild = bot.get_guild(guild_id)
                    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (guild.id,))
                    channel_id = c.fetchone()[0]
                    channel = bot.get_channel(channel_id)
                    await channel.send(embed=embed)
                except:
                    try:
                        for channel in guild.text_channels:
                            try:
                                await channel.send(f'{guild.owner.mention}\nIf you would like to set a channel for announcements, use </setchannel:1145275940008636482>.')
                                break
                            except:
                                continue
                    except:
                        await guild.owner.send(f'**NOTICE:** I failed to send the announcement to the server **{guild.name}** *({guild.id})*\nPlease make sure I have the permission `Administrator` and that there is at least one text channel.', embed=embed)
            await ctx.reply(f'Announcement sent to {len(guilds)} servers.')

#* Reset Command
@bot.command()
@commands.is_owner()
async def forcereset(ctx, guild_id: int):
    # check if server exists
    try:
        guild = bot.get_guild(guild_id)
    except:
        return await ctx.reply('That server does not exist.')
    # check if the bot is in the server
    if guild not in bot.guilds:
        return await ctx.reply('I am not in that server.')
    c.execute('DELETE FROM roles WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM bypass WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM auto WHERE server_id=?', (guild.id,))
    conn.commit()
    await ctx.reply(f'Reset {guild.name}\'s data.')

    # support_server = bot.get_guild(1158967835616362626) # Role Control Support Server
    # log_channel = support_server.get_channel(1173865122528239698)
    # embed = discord.Embed(title='Role Control | Server Reset', description=f'Server reset for **{guild.name}** *({guild.id})*', color=0x00ff00)
    # embed.set_footer(text=f'Force reset by {ctx.author.name} *({ctx.author.id})*')
    # await log_channel.send(embed=embed)

#* Blacklist Command
@bot.command()
@commands.is_owner()
async def blacklist(ctx, action, guild_id: str, *, reason=None):
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)
    if action.lower() == 'add':
        # check if server is already blacklisted
        with open('blacklist.json', 'r') as f:
            blacklist = json.load(f)
        if str(guild_id) in blacklist['servers']:
            return await ctx.reply('That server is already blacklisted.')
        if reason is None:
            reason = 'No reason given.'
        # add server to blacklist
        blacklist['servers'].append(str(guild_id))
        blacklist['reasons'][str(guild_id)] = reason
        try:
            guild = bot.get_guild(guild_id)
            if guild:
                blacklist['names'][str(guild_id)] = guild.name
            else:
                blacklist['names'][str(guild_id)] = 'Unknown Server'
        except:
            blacklist['names'][str(guild_id)] = 'Unknown Server'
        with open('blacklist.json', 'w') as f:
            json.dump(blacklist, f, indent=4)
        await ctx.reply(f'Added server with ID {guild_id} to blacklist.')

        # Notify server owner (whether bot is in the guild or not)
        try:
            guild = bot.get_guild(guild_id)
            if guild:
                owner = guild.owner
                try:
                    await owner.send('Your server has been blacklisted from using Role Control.\nIf you believe this is a mistake, please contact the developer *(652498200447549450)*.')
                except:
                    try:
                        for channel in guild.text_channels:
                            try:
                                await channel.send(f'{guild.owner.mention} This server has been blacklisted from using Role Control.\nIf you believe this is a mistake, please contact the developer. *(652498200447549450)*')
                                break
                            except:
                                continue
                    except:
                        pass

            await guild.leave()
        except:
            pass

    elif action.lower() == 'remove':
        # check if server is already blacklisted
        with open('blacklist.json', 'r') as f:
            blacklist = json.load(f)
        if str(guild_id) not in blacklist['servers']:
            return await ctx.reply('That server is not blacklisted.')
        # remove server from blacklist
        blacklist['servers'].remove(str(guild_id))
        del blacklist['reasons'][str(guild_id)]
        del blacklist['names'][str(guild_id)]
        with open('blacklist.json', 'w') as f:
            json.dump(blacklist, f, indent=4)
        await ctx.reply(f'Removed server with ID {guild_id} from blacklist.')
    
    else:
        await ctx.reply('Invalid action. Use `add` or `remove`.')

#* List Blacklist Command
@bot.command()
@commands.is_owner()
async def listblacklist(ctx):
    with open('blacklist.json', 'r') as f:
        blacklist = json.load(f)
    
    servers = []
    for guild_id in blacklist['servers']:
        servers.append(f'- **{blacklist["names"][guild_id]}** *({guild_id})*\n> **Reason:** {blacklist["reasons"][guild_id]}')
        
    if not servers:
        servers.append('No blacklisted servers.')
    
    servers_list = '\n'.join(servers)
    embed = discord.Embed(title='Role Control | Blacklist', description='Discord Bot to control & manage roles.', color=0x00ff00)
    embed.add_field(name='Servers', value=servers_list, inline=False)
    await ctx.reply(embed=embed)

## ? Bot Events

#* When Bot Joins Server
@bot.event
async def on_guild_join(guild):
    await asyncio.sleep(2.5) # wait 2.5 seconds to make sure no errors occur
    embed = discord.Embed(title='Terms of Service', description='By adding this bot to your server, you agree to the following terms of service.', color=0x00ff00)
    embed.add_field(name='1.', value='You will not use this bot to break the [Discord TOS](https://discord.com/terms) or [Discord Guidelines](https://discord.com/guidelines).', inline=False)
    embed.add_field(name='2.', value='You will not use this bot in any server that promotes violence, hate speech (racism, transphobia, etc), or any other illegal activity.', inline=False)
    embed.add_field(name='3.', value='You will not use this bot on any server that is primary for NSFW content.', inline=False)
    embed.add_field(name='4.', value='You will not use this bot to raid, spam, or otherwise annoy other users.', inline=False)
    embed.add_field(name='Subject to change', value='These terms of service are subject to change at any time. If you do not agree to these terms of service, remove the bot from your server.', inline=False)
    embed.add_field(name="Violation of TOS", value="Violation of these terms of service will result in the bot leaving your server, your server being blacklisted, and a report being sent to Discord if necessary.", inline=False)

    promo = discord.Embed(title='Partner', description='This bot is a close partner of [**Skyline Hosting**](https://discord.gg/F3HCDcuMks) & [**SkyNet**](https://discord.gg/4RgSMTDe).', color=0x00ff00)
    promo.add_field(name='Skyline Hosting', value='Skyline Hosting is a hosting company that offers reasonable prices, excellent support, and constant uptime. They offer Minecraft Server, Discord Bot, Web Hosting, and more!', inline=False)
    promo.add_field(name='SkyNet', value='SkyNet is a newly created Minecraft Network in development.', inline=False)
    try:
        for channel in guild.text_channels:
            try:
                await guild.owner.send(f'Thank you for inviting me to your server **{guild.name}**\nUse </setup:1146779160996483114> to setup the bot for your server.\nIf any issues occur, report them on **[our server](<https://discord.gg/9HtyP4SJVJ>)**.', embed=embed)
                await guild.owner.send(embed=promo)
                break # if sent successfully, break out of loop
            except Exception as e:
                logger.error(f"An error occured while sending join message to Guild Owner ({guild.owner.id}) of {guild.name} ({guild.id}): {e}")
                
                continue # if error, continue
    except:
        logger.warning(f"An error occured while sending join message to Guild Owner ({guild.owner.id}) of {guild.name} ({guild.id}). Sending to server instead.")
        try:
            await channel.send(f'Thank you for inviting me!\nUse </setup:1146779160996483114> to setup the bot for your server.\nIf any issues occur, report them on **[our server](<https://discord.gg/9HtyP4SJVJ>)**.', embed=embed)
            await channel.send(embed=promo)
        except:
            logger.error(f"An error occured while sending join message to {channel.name} in {guild.name} ({guild.id}): {e}")
    # get the bot's role
    for role in guild.roles:
        if role.name == 'Role Control':
            bot_role = role
    # add bot role to database
    c.execute('INSERT INTO bot_role VALUES (?, ?)', (guild.id, bot_role.id))
    conn.commit()

    # support_server = bot.get_guild(1158967835616362626) # get the support server
    # log_channel = support_server.get_channel(1173867643707600897) # get the bot server logs channel
    # embed = discord.Embed(title='Bot Joined Server', description=f'Bot joined server **{guild.name}** *(`{guild.id}`)*', color=0x00ff00)
    # embed.add_field(name='Owner', value=f'{guild.owner.name} *({guild.owner.id})*', inline=False)
    # embed.add_field(name='Members', value=f'Total: {guild.member_count}\nUsers: {len([member for member in guild.members if not member.bot])}\nBots: {len([member for member in guild.members if member.bot])}', inline=False)
    # embed.add_field(name='Channels', value=f'{len(guild.channels)}', inline=False)
    # embed.add_field(name='Roles', value=f'{len(guild.roles)}', inline=False)
    # embed.add_field(name='Created', value=f'{guild.created_at}', inline=False)
    # embed.add_field(name='Verification Level', value=f'{guild.verification_level}', inline=False)
    # embed.add_field(name='Boosts', value=f'{guild.premium_subscription_count}', inline=False)
    # embed.add_field(name='Boost Level', value=f'{guild.premium_tier}', inline=False)    
    # embed.add_field(name='Emojis', value=f'{len(guild.emojis)}', inline=False)
    # embed.set_footer(text=f'Bot is now in {len(bot.guilds)} servers.')
    # await log_channel.send(embed=embed)


#* On Member Join
@bot.event
async def on_member_join(member):
    # check if the user joined using a invite created by the bot



    # get auto roles
    c.execute('SELECT role_id FROM auto WHERE server_id=?', (member.guild.id,))
    auto_roles = c.fetchall()

    # add auto roles
    if len(auto_roles) == 0:
        return
    
    for role in auto_roles:
        if role[0] == 0:
            return
        await member.add_roles(member.guild.get_role(role[0]))

#* On Member Update
@bot.event
async def on_member_update(before, after):
    # check if user has bypass role
    c.execute('SELECT role_id FROM bypass WHERE server_id=?', (after.guild.id,))
    bypass_roles = c.fetchall()
    # check if user has role(s)
    for role in bypass_roles:
        if after.guild.get_role(role[0]) in after.roles:
            return
    # check if user has role(s)
    c.execute('SELECT role_id FROM roles WHERE server_id=?', (after.guild.id,))
    roles = c.fetchall()
    for role in roles:
        if after.guild.get_role(role[0]) in after.roles:
            if after.bot:
                return
            # get the person who gave the role via audit logs
            async for log in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if log.target.id == after.id:
                    giver = log.user
                    break
            else:
                giver = None
            if giver:
                # tell the giver that they gave the role
                await giver.send(f'You gave the role `{after.guild.get_role(role[0])}` to `{after}` *({after.id})* in the server `{after.guild.name}` *({after.guild.id})*\nThis role is protected and has been removed!')
            else:
                await after.guild.owner.send(f'Role `{after.guild.get_role(role[0])}` was given to `{after}` *({after.id})* by an unknown user in the server `{after.guild.name}` *({after.guild.id})*\nThis role is protected and has been removed!')
            try:
                await after.remove_roles(after.guild.get_role(role[0]))
            except:
                await after.guild.owner.send(f'Failed to remove role `{after.guild.get_role(role[0])}` from `{after}` *({after.id})* in the server `{after.guild.name}` *({after.guild.id})*\nPlease make sure I have the permission `Manage Roles` and that my role is above the role!')

#* On Role Delete
@bot.event
async def on_guild_role_delete(role):
    await asyncio.sleep(1.5)
    if role.guild not in bot.guilds:
        return
    
    type = 'Unknown'

    c.execute('SELECT role_id FROM roles WHERE role_id=?', (role.id,))
    if c.fetchone() is not None:
        type = 'Protected'
        await role.guild.owner.send(f'Role `{role}` was deleted. I have removed it from my database.')
        # remove role from database
        c.execute('DELETE FROM roles WHERE role_id=?', (role.id,))

    c.execute('SELECT role_id FROM bypass WHERE role_id=?', (role.id,))
    if c.fetchone() is not None:
        type = 'Bypass'
        await role.guild.owner.send(f'Role `{role}` was deleted. I have removed it from my database.')
        # remove role from database
        c.execute('DELETE FROM bypass WHERE role_id=?', (role.id,))

    c.execute('SELECT role_id FROM auto WHERE role_id=?', (role.id,))
    if c.fetchone() is not None:
        type = 'Auto'
        await role.guild.owner.send(f'Role `{role}` was deleted. I have removed it from my database.')
        # remove role from database
        c.execute('DELETE FROM auto WHERE role_id=?', (role.id,))

    c.execute('SELECT role_id FROM manager_roles WHERE role_id=?', (role.id,))
    if c.fetchone() is not None:
        type = 'Manager'
        await role.guild.owner.send(f'Role `{role}` was deleted. I have removed it from my database.')
        # remove role from database
        c.execute('DELETE FROM manager_roles WHERE role_id=?', (role.id,))

    c.execute('SELECT role_id FROM self_roles WHERE role_id=?', (role.id,))
    if c.fetchone() is not None:
        type = 'Self-Role'
        await role.guild.owner.send(f'Self-Role `{role}` was deleted.\nI cannot remove it from my database as it is a self-role. Please remove or replace it manually.')
    conn.commit()

    if type == 'Self-Role' or type == 'Unknown':
        return
    # support_server = bot.get_guild(1158967835616362626) # get the support server
    # log_channel = support_server.get_channel(1173865122528239698) # get the bot setup logs channel
    # embed = discord.Embed(title='Role Control | Role Deleted', description=f'Role `{role}` *({role.id})* was deleted in server **{role.guild.name}** *(`{role.guild.id}`)*', color=0x00ff00)
    # embed.add_field(name='Type', value=type, inline=False)
    # embed.add_field(name='Role', value=f'{role.name} *(`{role.id}`)*', inline=False)
    # await log_channel.send(embed=embed)

#* On server leave
@bot.event
async def on_guild_remove(guild):
    # delete server from all databases
    c.execute('DELETE FROM roles WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM bypass WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM auto WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM bot_role WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM announcements WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM manager_roles WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM self_roles WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM temp_roles WHERE server_id=?', (guild.id,))
    c.execute('DELETE FROM self_role_templates WHERE server_id=?', (guild.id,))
    conn.commit()

    # support_server = bot.get_guild(1158967835616362626) # get the support server
    # log_channel = support_server.get_channel(1173867643707600897) # get the bot server logs channel
    # embed = discord.Embed(title='Bot Left Server', description=f'Bot left server **{guild.name}** *(`{guild.id}`)*', color=0x00ff00)
    # embed.set_footer(text=f'Bot is now in {len(bot.guilds)} servers.')
    # await log_channel.send(embed=embed)

# When the bot's personal role is updated (Administrator Permissions removed)
@bot.event
async def on_guild_role_update(before, after):
    # get the bot's role from the database
    c.execute('SELECT role_id FROM bot_role WHERE server_id=?', (after.guild.id,))
    bot_role = c.fetchone()

    # check if the role is the bot's role
    if bot_role is not None:
        if after.id == bot_role[0]:
            if before.permissions.administrator and not after.permissions.administrator:
                message = 'I have detected that my **Administrator Permissions** have been removed. ' \
                            'Please give me **Administrator Permissions** to ensure I work correctly.' \
                            '\n\nIf you do not want to give me **Administrator Permissions**, please give me the following permissions:\n' \
                            '> `Send Messages` : I need this permission to send messages.\n' \
                            '> `Manage Roles` : I need this permission to manage roles as that is my purpose.\n' \
                            '> `View Audit Log` : I need this permission to retrieve the person who gave a protected role.\n' \
                            '> `Create Invite` : I need this permission to invite the developer if deemed necessary.\n' \
                            '> `Embed Links` : I need this permission to send embeds.\n' \
                            '> `Add Reactions` : I need this permission to add reactions to messages.\n' \
                            '> `Use External Emojis` : I need this permission to use emojis from my server.\n' \

                # send message to guild owner
                try:
                    await after.guild.owner.send(message)
                except:
                    try:
                        for channel in after.guild.text_channels:
                            try:
                                await channel.send(f'{after.guild.owner.mention},\n {message}')
                                break
                            except:
                                continue
                    except:
                        pass
    else:
        # find a role the bot manages
        for role in after.guild.roles:
            if role.managed and role.name == 'Role Control':
                # add bot role to database
                c.execute('INSERT INTO bot_role VALUES (?, ?)', (after.guild.id, role.id))
                conn.commit()
                break
            else:
                logger.error(f'Failed to find the bot\'s role in {after.guild.name} ({after.guild.id})')
                break

@bot.event
async def on_guild_channel_delete(channel):
    c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (channel.guild.id,))
    channel_id = c.fetchone()

    if channel_id is not None and channel_id[0] == channel.id:
        logger.info(f'Announcement Channel Deleted: {channel.name} ({channel.id}) in {channel.guild.name} ({channel.guild.id})')

        guild_owner = channel.guild.owner

        embed = discord.Embed(title='Role Control | Announcement Channel Deleted', description='Discord Bot to control & manage roles.', color=0x00ff00)
        embed.add_field(name='Announcement Channel ID', value=channel_id[0], inline=False)

        # support_server = bot.get_guild(1158967835616362626) # get the support server
        # log_channel = support_server.get_channel(1173865122528239698)

        # await log_channel.send(embed=embed)

        try:
            await guild_owner.send(f'{guild_owner.mention}, you have deleted the announcement channel for {bot.user.mention} in your server **{channel.guild.name}** *(`{channel.guild.id}`)*.\nUse </setchannel:1145275940008636482> to set a new announcement channel.', embed=embed)
        except:
            try:
                for channel in channel.guild.text_channels:
                    try:
                        await channel.send(f'{guild_owner.mention}, you have deleted the announcement channel for {bot.user.mention} in your server **{channel.guild.name}** *(`{channel.guild.id}`)*.\nUse </setchannel:1145275940008636482> to set a new announcement channel.', embed=embed)
                        break
                    except:
                        continue
            except Exception as e:
                logger.error(f'Failed to send announcement channel deleted message to guild owner of {channel.guild.name} ({channel.guild.id}): {e}')
                pass

        c.execute('DELETE FROM announcements WHERE server_id=?', (channel.guild.id,))
        conn.commit()


## ? Loops

#* Setup reminder
async def setup_reminder():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            c.execute('SELECT role_id FROM roles WHERE server_id=?', (guild.id,))
            roles = c.fetchall()
            c.execute('SELECT role_id FROM auto WHERE server_id=?', (guild.id,))
            auto_roles = c.fetchall()
            c.execute('SELECT role_id FROM bypass WHERE server_id=?', (guild.id,))
            bypass_roles = c.fetchall()
            c.execute('SELECT channel_id FROM announcements WHERE server_id=?', (guild.id,))
            channel_id = c.fetchone()
            if channel_id is None:
                try:
                    await guild.owner.send(f'You have not setup the bot for your server ({guild.name} *({guild.id})*). Use </setup:1146779160996483114> to setup the bot for your server.')
                    logger.info(f'Sent setup reminder to {guild.owner.name} ({guild.owner.id}) of {guild.name} ({guild.id})')

                    embed = discord.Embed(title='Role Control | Setup Reminder', description=f'Setup Reminder for server **{guild.name}** *(`{guild.id}`)*', color=0x00ff00)
                    embed.add_field(name='Owner', value=f'{guild.owner.name} *({guild.owner.id})*', inline=False)
                    embed.add_field(name='Members', value=f'Total: {guild.member_count}\nUsers: {len([member for member in guild.members if not member.bot])}\nBots: {len([member for member in guild.members if member.bot])}', inline=False)
                    embed.add_field(name='Channels', value=f'{len(guild.channels)}', inline=False)
                    embed.add_field(name='Roles', value=f'{len(guild.roles)}', inline=False)
                    embed.add_field(name='Emojis', value=f'{len(guild.emojis)}', inline=False)
                    embed.add_field(name='Created', value=f'{guild.created_at}', inline=False)
                    for member in guild.members:
                        if member.id == bot.user.id:
                            embed.add_field(name='Joined', value=f'{member.joined_at}', inline=False)
                            break
                    # support_server = bot.get_guild(1158967835616362626) # get the support server
                    # log_channel = support_server.get_channel(1173882245753339964) # get the setup reminders channel
                    # await log_channel.send(embed=embed)
                except:
                    try:
                        for channel in guild.text_channels:
                            try:
                                await channel.send(f'{guild.owner.mention} You have not setup the bot for your server ({guild.name} *({guild.id})*). Use </setup:1146779160996483114> to setup the bot for your server.')
                                logger.info(f'Sent setup reminder to {guild.owner.name} ({guild.owner.id}) of {guild.name} ({guild.id})')
                                
                                # support_server = bot.get_guild(1158967835616362626) # get the support server
                                # log_channel = support_server.get_channel(1173882245753339964) # get the setup reminders channel
                                # embed = discord.Embed(title='Role Control | Setup Reminder', description=f'Setup Reminder for server **{guild.name}** *(`{guild.id}`)*', color=0x00ff00)
                                # embed.add_field(name='Owner', value=f'{guild.owner.name} *({guild.owner.id})*', inline=False)
                                # embed.add_field(name='Members', value=f'Total: {guild.member_count}\nUsers: {len([member for member in guild.members if not member.bot])}\nBots: {len([member for member in guild.members if member.bot])}', inline=False)
                                # embed.add_field(name='Channels', value=f'{len(guild.channels)}', inline=False)
                                # embed.add_field(name='Roles', value=f'{len(guild.roles)}', inline=False)
                                # embed.add_field(name='Emojis', value=f'{len(guild.emojis)}', inline=False)
                                # embed.add_field(name='Created', value=f'{guild.created_at}', inline=False)
                                # for member in guild.members:
                                #     if member.id == bot.user.id:
                                #         embed.add_field(name='Joined', value=f'{member.joined_at}', inline=False)
                                #         break
                                # await log_channel.send(embed=embed)
                                
                                break
                            except:
                                continue
                    except:
                        pass
        await asyncio.sleep(86400) # 24 hours

#* Check if server is blacklisted
async def check_blacklist():
    await bot.wait_until_ready()
    while not bot.is_closed():
        with open('blacklist.json', 'r') as f:
            blacklist = json.load(f)
        for guild in bot.guilds:
            if str(guild.id) in blacklist['servers']:
                try:
                    await guild.owner.send(f'Your server **{guild.name}** *({guild.id})* has been blacklisted from using Role Control.\nIf you believe this is a mistake, please contact the developer. *(652498200447549450)*')
                except:
                    try:
                        for channel in guild.text_channels:
                            try:
                                await channel.send(f'{guild.owner.mention} This server has been blacklisted from using Role Control.\nIf you believe this is a mistake, please contact the developer. *(652498200447549450)*')
                                break
                            except:
                                continue
                    except:
                        pass
                await guild.leave()
        await asyncio.sleep(60) # 1 minute

#* Check temp roles
async def check_temproles():
    await bot.wait_until_ready()
    while not bot.is_closed():
        c.execute("SELECT * FROM temp_roles")
        temp_roles = c.fetchall()
        current_time = datetime.now()

        for temp_role in temp_roles:
            timestamp_str = temp_role[3]  # Get the timestamp string
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')  # Parse the string to a datetime

            if current_time >= timestamp:
                guild = bot.get_guild(temp_role[0])
                role = guild.get_role(temp_role[1])
                user = guild.get_member(temp_role[2])
                try:
                    await user.remove_roles(role)
                    try:
                        await user.send(f'Your temporary role `{role.name}` in `{guild.name}` *({guild.id})* has expired and has been removed.')
                    except:
                        pass
                except:
                    logger.warning(f'User doesn\'t have role {role.name} in {guild.name} ({guild.id})?\nProceeding to remove from database.')
                    try:
                        await user.send(f'Your temporary role `{role.name}` in `{guild.name}` *({guild.id})* has expired and has been removed.\n> **Note:** I was unable to remove the role from you. Perhaps it was already removed? *(Contact the server\'s staff if you still have it)*')
                    except:
                        pass
                c.execute("DELETE FROM temp_roles WHERE server_id=? AND role_id=? AND user_id=?", (guild.id, role.id, user.id))
                conn.commit()
        await asyncio.sleep(60) # 1 minute

#* Find bot role
async def find_botrole():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            managed_roles = [role for role in guild.me.roles if role.managed]

            if managed_roles:
                for role in managed_roles:
                    c.execute('SELECT role_id FROM bot_role WHERE server_id=?', (guild.id,))
                    if not c.fetchone():
                        c.execute('INSERT INTO bot_role VALUES (?, ?)', (guild.id, role.id))
                        conn.commit()
            else:
                logger.error(f'Failed to find managed role in {guild.name} ({guild.id})')

        await asyncio.sleep(86400) # 24 hours


## ? Bot startup
if __name__ == '__main__':
    bot.loop.create_task(setup_reminder())
    bot.loop.create_task(check_blacklist())
    bot.loop.create_task(check_temproles())
    bot.loop.create_task(find_botrole())
    bot.run(os.getenv('TOKEN'))