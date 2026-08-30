import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Arquivo para salvar os dados
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

# Comando para definir o canal onde os comprovantes serão enviados
@bot.tree.command(name="set-comprovantes", description="Define o canal de envio de comprovantes")
@commands.has_permissions(administrator=True)
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    dados = carregar_dados()
    dados["canal_comprovantes"] = canal.id
    salvar_dados(dados)
    await interaction.response.send_message(f"Canal de comprovantes definido para {canal.mention}!", ephemeral=True)

# Comando para definir o canal onde a lista de pagamento vai aparecer
@bot.tree.command(name="set-lista", description="Define o canal onde a lista de pagamentos será exibida")
@commands.has_permissions(administrator=True)
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    dados = carregar_dados()
    dados["canal_lista"] = canal.id
    salvar_dados(dados)
    await interaction.response.send_message(f"Canal da lista definido para {canal.mention}!", ephemeral=True)

# Monitora as mensagens enviadas no canal de comprovantes
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    dados = carregar_dados()
    canal_comp = dados.get("canal_comprovantes")

    # Verifica se a mensagem foi enviada no canal configurado de comprovantes e se tem imagem/anexo
    if canal_comp and message.channel.id == canal_comp:
        if message.attachments:
            user_id = str(message.author.id)
            user_name = message.author.display_name

            # Inicializa o membro se não existir nos dados
            if "membros" not in dados:
                dados["membros"] = {}
            if user_id not in dados["membros"]:
                dados["membros"][user_id] = {"nome": user_name, "pago": False}

            # Marca como pago ao enviar o comprovante (ou você pode ajustar para aprovação manual)
            dados["membros"][user_id]["pago"] = True
            salvar_dados(dados)

            await message.add_reaction("✅")
            
            # Atualiza ou avisa no canal da lista se estiver configurado
            canal_lista_id = dados.get("canal_lista")
            if canal_lista_id:
                canal_lista = bot.get_channel(canal_lista_id)
                if canal_lista:
                    # Aqui você pode mandar uma mensagem avisando ou atualizar a lista
                    pass

    await bot.process_commands(message)

# Comando para ver o saldo ou status da galera
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

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
