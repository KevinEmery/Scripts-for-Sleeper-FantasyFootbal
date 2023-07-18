import discord
import os

import adp
import trades

from datetime import datetime
from discord.ext import commands, tasks
from typing import List

# Actual limit is 25, we want to steer clear in case we add fields on top of the iteration
EMBED_FIELD_LIMIT = 20
FTA_ADP_THREAD_CONTENT = "The data here is for the FTA league format. \
These leagues are 14-team, 0.5 PPR Leagues that start \
1 QB, 2 RBs, 3 WRs, 1 TE, 1 W/R/T Flex, 1 K, and 1 DEF.\n\n"
ADP_GLOSSARY = "__**Glossary Terms**__\
```\n\
ADP: The average draft position across all drafts\n\
Min: The earliest a player was drafted\n\
Max: The latest a player was drafted\n\
N:   The number of times a player has been drafted\
```\n\
The designation \"X.Y\" represents a selection in Round X, at Pick Y"

FTA_TRADE_CHANNEL_PATH = "./bot_data/fta_trade_channel"
FTA_LAST_TRADE_TIMESTAMP_PATH = "./bot_data/fta_last_trade_timestamp"

FTAFFL_USER = "FTAFFL"
FTAFFL_LEAGUE_REGEX = "^FTA \#\d+.*$"

FTA_LEAGUE_ADMIN_ROLE = "League Admin"
LOB_COMMISH_ROLE = "Commissioner"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='&', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# FTA ADP Commands


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adps(ctx, forum: discord.ForumChannel):
    await post_fta_adp_all(ctx, forum)
    await post_fta_adp_qb(ctx, forum)
    await post_fta_adp_wr(ctx, forum)
    await post_fta_adp_rb(ctx, forum)
    await post_fta_adp_te(ctx, forum)


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_all(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, adp.INCLUDE_ALL, "All Players", discord.Colour.dark_blue())


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_qb(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, "QB", "Quarterback", discord.Colour.from_rgb(192, 94, 133))


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_wr(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, "WR", "Wide Receiver", discord.Colour.from_rgb(70, 162, 202))


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_rb(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, "RB", "Running Back", discord.Colour.from_rgb(115, 195, 166))


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_te(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, "TE", "Tight End", discord.Colour.from_rgb(204, 140, 74))


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_k(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, "K", "Kicker", discord.Colour.purple())


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def post_fta_adp_def(ctx, forum: discord.ForumChannel):
    await _post_fta_position_adp(ctx, forum, "DEF", "Team Defense", discord.Colour.from_rgb(154, 95, 78))


async def _post_fta_position_adp(ctx, forum: discord.ForumChannel, position_short: str, position_long: str, embed_color: discord.Colour):
    adp_data = adp.aggregate_adp_data(FTAFFL_USER, 14, position=position_short,
                                      league_regex_string=FTAFFL_LEAGUE_REGEX, output_format=adp.OutputFormat.FORMATTED_CSV)
    messages = _break_adp_content_into_messages(adp_data, embed_color)
    thread_title = _get_formatted_date() + ": " + position_long
    thread_content = FTA_ADP_THREAD_CONTENT + ADP_GLOSSARY
    thread = (await forum.create_thread(name=thread_title, content=thread_content))[0]
    for message in messages:
        await thread.send(embed=message)


def _break_adp_content_into_messages(content: List[str], embed_color: discord.Colour) -> List[discord.Embed]:
    split_content = []
    current_embed = discord.Embed(colour=embed_color)

    for line in content:
        if (len(current_embed.fields) >= EMBED_FIELD_LIMIT):
            split_content.append(current_embed)
            current_embed = discord.Embed(colour=embed_color)
        _convert_adp_csv_to_embed_field(line, current_embed)

    if len(current_embed.fields) > 0:
        split_content.append(current_embed)

    return split_content


def _convert_adp_csv_to_embed_field(content: str, embed: discord.Embed):
    player_data = content.split(",")
    template = "`ADP: {adp:<5} Min: {min:<5} Max: {max:<5} N: {n}`"
    embed.add_field(name=player_data[0], value=template.format(n=player_data[4],
                    adp=player_data[1], min=player_data[2], max=player_data[3]), inline=False)


def _get_formatted_date() -> str:
    now = datetime.now()
    return now.strftime("%m/%d/%y")

# FTA Trade Commands


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def start_posting_fta_trades(ctx):
    post_fta_trades.start()


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def stop_posting_fta_trades(ctx):
    post_fta_trades.cancel()


@tasks.loop(minutes=30.0)
async def post_fta_trades():
    trade_channel = _get_fta_trade_channel()

    if trade_channel is not None:
        # Get the last timestamp, determine if we need to pass it to the method as a starting point
        last_posted_trade_timestamp = _read_fta_last_trade_timestamp()

        if last_posted_trade_timestamp != "":
            print("FTA_Trades: Retrieving trades since: " + last_posted_trade_timestamp)
            all_trades = trades.fetch_and_filter_trades(
                FTAFFL_USER, league_regex_string=FTAFFL_LEAGUE_REGEX, start_date_string=last_posted_trade_timestamp)
        else:
            print("FTA_Trades: No previous timestamp found")
            all_trades = trades.fetch_and_filter_trades(FTAFFL_USER, league_regex_string=FTAFFL_LEAGUE_REGEX)

        # Post the trades
        for trade in all_trades:
            await trade_channel.send(content=trades.format_trades([trade]))

        # Write the timestamp of the last trade
        if len(all_trades) > 0:
            _write_fta_last_trade_timestamp(all_trades[-1].trade_time)
    else:
        print("FTA_Trades: No trade channel available")


@bot.command()
@commands.has_any_role(LOB_COMMISH_ROLE, FTA_LEAGUE_ADMIN_ROLE)
async def set_fta_trades_channel(ctx, channel: discord.TextChannel):
    file = open(FTA_TRADE_CHANNEL_PATH, "w")
    file.write(str(channel.id))
    file.close()


def _get_fta_trade_channel() -> discord.TextChannel:
    if os.path.isfile(FTA_TRADE_CHANNEL_PATH):
        file = open(FTA_TRADE_CHANNEL_PATH, "r")
        channel_id = file.read()
        file.close()
    else:
        return None

    return bot.get_channel(int(channel_id))


def _write_fta_last_trade_timestamp(timestamp: str):
    file = open(FTA_LAST_TRADE_TIMESTAMP_PATH, "w")
    file.write(str(timestamp))
    file.close()


def _read_fta_last_trade_timestamp() -> str:
    if os.path.isfile(FTA_LAST_TRADE_TIMESTAMP_PATH):
        file = open(FTA_LAST_TRADE_TIMESTAMP_PATH, "r")
        timestamp = file.read()
        file.close()
    else:
        return ""

    return timestamp


def _retrieve_token() -> str:
    token_file = open("./local/bot_token", "r")
    token_string = token_file.read()
    token_file.close()

    return token_string


bot.run(_retrieve_token())
