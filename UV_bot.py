import discord
from discord.ext import commands, tasks
import requests
import os
from datetime import datetime
import sqlite3
import asyncio
import logging

# Add logging configuration near the top of the file after imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Remove any dotenv loading since we're using Docker environment variables directly
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
TOKEN = os.getenv('TOKEN')

# Verify environment variables are available
if not WEATHER_API_KEY or not TOKEN:
    raise ValueError("Missing required environment variables. Make sure WEATHER_API_KEY and TOKEN are set.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

def init_db():
    conn = sqlite3.connect('/app/data/user_preferences.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences
                 (user_id INTEGER PRIMARY KEY,
                  location TEXT,
                  location_name TEXT,
                  notification_time TEXT,
                  uv_threshold FLOAT)''')
    conn.commit()
    conn.close()

async def store_user_preference(user_id, location, location_name, uv_threshold):
    conn = sqlite3.connect('/app/data/user_preferences.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO user_preferences 
                 (user_id, location, location_name, uv_threshold)
                 VALUES (?, ?, ?, ?)''', 
                 (user_id, location, location_name, uv_threshold))
    conn.commit()
    conn.close()

async def get_user_preference(user_id):
    conn = sqlite3.connect('/app/data/user_preferences.db')
    c = conn.cursor()
    c.execute('SELECT location, location_name, uv_threshold FROM user_preferences WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

async def search_locations(query):
    url = f"http://api.weatherapi.com/v1/search.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": query
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return data[:5]  # Return top 5 matches
    except Exception as e:
        return []

async def get_uv_index(location):
    url = f"http://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": location,
        "aqi": "no"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        uv_index = data['current']['uv']
        location_name = data['location']['name']
        region = data['location']['region']
        country = data['location']['country']
        return uv_index, f"{location_name}, {region}, {country}"
    except Exception as e:
        return None, str(e)

@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user}')
    init_db()
    daily_notification.start()
    scheduler_test.start()
    logging.info('Started daily notification and scheduler test loops')

@bot.command(name='uv')
async def uv(ctx, *, location_query=None):
    if not location_query:
        await ctx.send("Please provide a location. Usage: $uv <location>")
        return

    # Search for locations matching the query
    locations = await search_locations(location_query)
    
    if not locations:
        await ctx.send("No locations found. Please try a different search term.")
        return
    
    if len(locations) == 1:
        location = f"{locations[0]['lat']},{locations[0]['lon']}"
    else:
        # Create a numbered list of locations
        location_list = "\n".join([f"{i+1}. {loc['name']}, {loc['region']}, {loc['country']}" 
                                 for i, loc in enumerate(locations)])
        await ctx.send(f"Multiple locations found. Reply with a number to select:\n{location_list}")
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()
        
        try:
            response = await bot.wait_for('message', timeout=30.0, check=check)
            selection = int(response.content)
            if 1 <= selection <= len(locations):
                location = f"{locations[selection-1]['lat']},{locations[selection-1]['lon']}"
            else:
                await ctx.send("Invalid selection.")
                return
        except TimeoutError:
            await ctx.send("Selection timed out. Please try again.")
            return

    uv_index, location_name = await get_uv_index(location)
    
    if uv_index is not None:
        risk_level = "Low" if uv_index <= 2 else "Moderate" if uv_index <= 5 else "High" if uv_index <= 7 else "Very High" if uv_index <= 10 else "Extreme"
        await ctx.send(f"Current UV Index for {location_name}: {uv_index:.1f} ({risk_level})")
    else:
        await ctx.send(f"Error: {location_name}")

@bot.command(name='setlocation')
async def setlocation(ctx, *, location_query=None):
    if not location_query:
        await ctx.send("Please provide a location. Usage: $setlocation <location>")
        return

    locations = await search_locations(location_query)
    
    if not locations:
        await ctx.send("No locations found. Please try a different search term.")
        return
    
    if len(locations) == 1:
        location = f"{locations[0]['lat']},{locations[0]['lon']}"
        location_name = f"{locations[0]['name']}, {locations[0]['region']}, {locations[0]['country']}"
    else:
        # Create a numbered list of locations
        location_list = "\n".join([f"{i+1}. {loc['name']}, {loc['region']}, {loc['country']}" 
                                 for i, loc in enumerate(locations)])
        await ctx.send(f"Multiple locations found. Reply with a number to select:\n{location_list}")
        
        try:
            response = await bot.wait_for('message', 
                                        timeout=30.0, 
                                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit())
            selection = int(response.content)
            if 1 <= selection <= len(locations):
                selected = locations[selection-1]
                location = f"{selected['lat']},{selected['lon']}"
                location_name = f"{selected['name']}, {selected['region']}, {selected['country']}"
            else:
                await ctx.send("Invalid selection.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Selection timed out. Please try again.")
            return

    uv_options = """Please select your UV index notification threshold:
1. Low (UV Index > 2)
2. Moderate (UV Index > 5)
3. High (UV Index > 7)
4. Very High (UV Index > 10)"""
    
    await ctx.send(uv_options)
    
    try:
        response = await bot.wait_for('message',
                                    timeout=30.0,
                                    check=lambda m: m.author == ctx.author and 
                                                  m.channel == ctx.channel and 
                                                  m.content in ['1', '2', '3', '4'])
        
        uv_thresholds = {
            '1': 2.0,  # Low
            '2': 5.0,  # Moderate
            '3': 7.0,  # High
            '4': 10.0  # Very High
        }
        
        threshold = uv_thresholds[response.content]
        await store_user_preference(ctx.author.id, location, location_name, threshold)
        
        threshold_names = {2.0: 'Low', 5.0: 'Moderate', 7.0: 'High', 10.0: 'Very High'}
        await ctx.send(f"Your default location has been set to: {location_name}\nYou will be notified when UV index is {threshold_names[threshold]} or higher (UV > {threshold})")
    
    except asyncio.TimeoutError:
        await ctx.send("Selection timed out. Please try again.")
        return

@bot.command(name='mylocation')
async def mylocation(ctx):
    result = await get_user_preference(ctx.author.id)
    if result:
        location, location_name, uv_threshold = result
        uv_index, _ = await get_uv_index(location)
        if uv_index is not None:
            risk_level = "Low" if uv_index <= 2 else "Moderate" if uv_index <= 5 else "High" if uv_index <= 7 else "Very High" if uv_index <= 10 else "Extreme"
            threshold_names = {2.0: 'Low', 5.0: 'Moderate', 7.0: 'High', 10.0: 'Very High'}
            await ctx.send(f"Current UV Index for {location_name}: {uv_index:.1f} ({risk_level})\nNotification threshold: {threshold_names[uv_threshold]} (UV > {uv_threshold})")
    else:
        await ctx.send("No default location set. Use $setlocation to set one.")

@tasks.loop(hours=24)
async def daily_notification():
    logging.info("Starting daily UV notification check")
    conn = sqlite3.connect('/app/data/user_preferences.db')
    c = conn.cursor()
    c.execute('SELECT user_id, location, location_name, uv_threshold FROM user_preferences')
    users = c.fetchall()
    conn.close()

    logging.info(f"Found {len(users)} users to check")
    for user_id, location, location_name, uv_threshold in users:
        uv_index, _ = await get_uv_index(location)
        if uv_index is not None:
            risk_level = "Low" if uv_index <= 2 else "Moderate" if uv_index <= 5 else "High" if uv_index <= 7 else "Very High" if uv_index <= 10 else "Extreme"
            logging.info(f"User {user_id} - Location: {location_name} - UV Index: {uv_index:.1f} - Threshold: {uv_threshold}")
            
            # Only notify if UV index exceeds user's threshold
            if uv_index > uv_threshold:
                user = await bot.fetch_user(user_id)
                try:
                    await user.send(f"⚠️ UV Alert! Current UV Index for {location_name}: {uv_index:.1f} ({risk_level})")
                    logging.info(f"Successfully sent notification to user {user_id}")
                except discord.Forbidden:
                    logging.error(f"Cannot send DM to user {user_id}")

@daily_notification.before_loop
async def before_daily_notification():
    await bot.wait_until_ready()
    now = datetime.now()
    # Wait until 9 AM
    target_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target_time:
        target_time = target_time.replace(day=target_time.day + 1)
    seconds_until_target = (target_time - now).total_seconds()
    logging.info(f"Daily notification will start in {seconds_until_target:.1f} seconds (at {target_time})")
    await asyncio.sleep(seconds_until_target)


bot.run(TOKEN)
