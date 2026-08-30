import os
import json
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# Configuração do Flask para manter o bot online 24/7 no Render
app = Flask('')

@app.route('/')
def home():
    return "Bot da gangue está online e funcionando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def manter_online():
    t = Thread(target=run)
    t.start()

# Configuração do Bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

ARQUIVO_DADOS = "dados_gangue.json"

def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return {"canal_comprovantes": None, "canal_lista": None, "pagamentos": {}}
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"canal_comprovantes": None, "canal_lista": None, "pagamentos": {}}

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos de barra.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

@bot.tree.command(name="set-comprovantes", description="Define o canal de envio de comprovantes")
@commands.has_permissions(administrator=True)
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    
    dados = carregar_dados()
    dados["canal_comprovantes"] = canal.id
    salvar_dados(dados)
    
    await interaction.followup.send(f"Canal de comprovantes definido para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="set-lista", description="Define o canal onde a lista de pagamentos será exibida")
@commands.has_permissions(administrator=True)
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    
    dados = carregar_dados()
    dados["canal_lista"] = canal.id
    salvar_dados(dados)
    
    await interaction.followup.send(f"Canal da lista definido para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="lista-pagamentos", description="Mostra o status de pagamentos da gangue")
async def lista_pagamentos(interaction: discord.Interaction):
    await interaction.response.defer()
    
    dados = carregar_dados()
    embed = discord.Embed(
        title="📊 Status de Pagamentos da Gangue",
        description="Controle financeiro atualizado.",
        color=discord.Color.blue()
    )
    
    pagamentos = dados.get("pagamentos", {})
    if not pagamentos:
        embed.add_field(name="Registros", value="Nenhum pagamento registrado ainda.", inline=False)
    else:
        texto = ""
        for user_id, status in pagamentos.items():
            texto += f"<@_{user_id}>: **{status}**\n"
        embed.add_field(name="Membros", value=texto, inline=False)
        
    await interaction.followup.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    dados = carregar_dados()
    canal_comprovantes_id = dados.get("canal_comprovantes")

    if canal_comprovantes_id and message.channel.id == canal_comprovantes_id:
        if message.attachments:
            try:
                await message.add_reaction("✅")
            except Exception:
                pass

    await bot.process_commands(message)

# Inicia o servidor Flask e o Bot
if __name__ == "__main__":
    manter_online()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Erro: A variável de ambiente DISCORD_TOKEN não foi configurada no Render!")
