import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot da gangue está online e funcionando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def manter_online():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Memória global do bot (não depende de arquivos que apagam no Render)
CONFIG_CANAIS = {
    "canal_comprovantes": None,
    "canal_lista": None
}
PAGAMENTOS = {}

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")
    try:
        GUILD_ID = os.getenv("DISCORD_GUILD_ID")
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"Sincronizados {len(synced)} comandos na guilda.")
        else:
            synced = await bot.tree.sync()
            print(f"Sincronizados {len(synced)} comandos globais.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

@bot.tree.command(name="set-comprovantes", description="Define o canal de envio de comprovantes")
@commands.has_permissions(administrator=True)
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    CONFIG_CANAIS["canal_comprovantes"] = canal.id
    await interaction.followup.send(f"Canal de comprovantes definido para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="set-lista", description="Define o canal onde a lista de pagamentos será exibida")
@commands.has_permissions(administrator=True)
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    CONFIG_CANAIS["canal_lista"] = canal.id
    await interaction.followup.send(f"Canal da lista definido para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="lista-pagamentos", description="Mostra o status de pagamentos da gangue")
async def lista_pagamentos(interaction: discord.Interaction):
    await interaction.response.defer()
    
    embed = discord.Embed(
        title="📊 Status de Pagamentos da Gangue",
        description="Controle financeiro atualizado.",
        color=discord.Color.blue()
    )
    
    if not PAGAMENTOS:
        embed.add_field(name="Registros", value="Nenhum pagamento registrado ainda.", inline=False)
    else:
        texto = ""
        for user_id, info in PAGAMENTOS.items():
            texto += f"<@{user_id}>: **{info}**\n"
        embed.add_field(name="Membros", value=texto, inline=False)
        
    await interaction.followup.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    canal_comprovantes_id = CONFIG_CANAIS.get("canal_comprovantes")

    if canal_comprovantes_id and message.channel.id == canal_comprovantes_id:
        if message.attachments:
            user_id = str(message.author.id)
            texto_enviado = message.content if message.content else "Pago"
            
            # Salva na memória instantaneamente
            PAGAMENTOS[user_id] = texto_enviado

            try:
                await message.add_reaction("✅")
            except Exception:
                pass

    await bot.process_commands(message)

if __name__ == "__main__":
    manter_online()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Erro: A variável de ambiente DISCORD_TOKEN não foi configurada no Render!")
