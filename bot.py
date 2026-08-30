import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# Configuração do servidor web básico para o Render não dar timeout de porta
app = Flask('')

@app.route('/')
def home():
    return "Bot da Gangue está online!"

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Configuração do Bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "dados_gangue.json"

def carregar_dados():
    if not os.path.exists(DATA_FILE):
        return {"canal_comprovantes": None, "canal_lista": None, "membros": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(e)

@bot.tree.command(name="set-comprovantes", description="Define o canal de envio de comprovantes")
@commands.has_permissions(administrator=True)
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    dados = carregar_dados()
    dados["canal_comprovantes"] = canal.id
    salvar_dados(dados)
    await interaction.response.send_message(f"Canal de comprovantes definido para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="set-lista", description="Define o canal onde a lista de pagamentos será exibida")
@commands.has_permissions(administrator=True)
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    dados = carregar_dados()
    dados["canal_lista"] = canal.id
    salvar_dados(dados)
    await interaction.response.send_message(f"Canal da lista definido para {canal.mention}!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    dados = carregar_dados()
    canal_comp = dados.get("canal_comprovantes")

    if canal_comp and message.channel.id == canal_comp:
        if message.attachments:
            user_id = str(message.author.id)
            user_name = message.author.display_name

            if "membros" not in dados:
                dados["membros"] = {}
            if user_id not in dados["membros"]:
                dados["membros"][user_id] = {"nome": user_name, "pago": False}

            dados["membros"][user_id]["pago"] = True
            salvar_dados(dados)

            await message.add_reaction("✅")

    await bot.process_commands(message)

@bot.tree.command(name="lista-pagamentos", description="Mostra o status de pagamentos da gangue")
async def lista_pagamentos(interaction: discord.Interaction):
    dados = carregar_dados()
    membros = dados.get("membros", {})
    
    if not membros:
        await interaction.response.send_message("Nenhum registro de pagamento encontrado.", ephemeral=True)
        return

    texto = "**Status de Pagamentos da Gangue:**\n\n"
    for uid, info in membros.items():
        status = "Pago ✅" if info["pago"] else "Pendente ❌"
        texto += f"- {info['nome']}: {status}\n"

    await interaction.response.send_message(texto)

# Inicia o servidor web em segundo plano para o Render
keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
