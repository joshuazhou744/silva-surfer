import discord

def build_valorant_player_embed(player):
    embed = discord.Embed(
        title=f"{player.name}#{player.tag}",
        color=discord.Color.purple()
    )
    player_title = player.player_title or "No Title"
    embed.set_image(url=player.player_card)
    embed.description = f"{player_title} • {player.region.upper()}"

    # Rank icon
    embed.set_thumbnail(url=player.current_rank_icon)

    embed.add_field(
        name="🏆 Current Rank",
        value=f"{player.current_rank}\n{player.current_rr} RR",
        inline=False
    )

    embed.add_field(
        name="👑 Peak Rank",
        value=f"{player.peak_rank}\nAct: {player.peak_rank_act}",
        inline=False
    )
    return embed