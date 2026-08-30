import os
from datetime import datetime
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

# Memória global do bot
CONFIG_CANAIS = {
    "canal_comprovantes": None,
    "canal_lista": None,
    "mensagem_lista_id": None
}
PAGAMENTOS = {}

def gerar_embed_pagamentos():
    hoje = datetime.now().strftime("%d/%m/%Y")
    embed = discord.Embed(
        title=f"📊 Status de Pagamentos da Gangue ({hoje})",
        description="Controle financeiro diário em tempo real.",
        color=discord.Color.blue()
    )
    
    # Filtra pagamentos do dia atual
    pagamentos_hoje = {}
    for user_id, info in PAGAMENTOS.items():
        if isinstance(info, dict) and info.get("data") == hoje:
            pagamentos_hoje[user_id] = info

    if not pagamentos_hoje:
        embed.add_field(name="Registros", value="Nenhum pagamento registrado hoje.", inline=False)
    else:
        texto = ""
        for user_id, info in pagamentos_hoje.items():
            nome_usuario = info.get("nome", "Membro")
            valor = info.get("valor", "Pago")
            texto += f"<@{user_id}> ({nome_usuario}): **{valor}**\n"
        embed.add_field(name="Membros", value=texto, inline=False)
        
    return embed

async def atualizar_painel_lista(bot_instance, guild):
    canal_lista_id = CONFIG_CANAIS.get("canal_lista")
    msg_id = CONFIG_CANAIS.get("mensagem_lista_id")
    
    if not canal_lista_id:
        return
        
    canal = guild.get_channel(canal_lista_id)
    if not canal:
        try:
            canal = await bot_instance.fetch_channel(canal_lista_id)
        except Exception:
            return

    embed = gerar_embed_pagamentos()

    if msg_id:
        try:
            msg = await canal.fetch_message(msg_id)
            await msg.edit(embed=embed)
            return
        except Exception:
            pass # Se a mensagem foi apagada, cria uma nova abaixo
            
    # Cria uma nova mensagem fixa se não existir
    nova_msg = await canal.send(embed=embed)
    CONFIG_CANAIS["mensagem_lista_id"] = nova_msg.id

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

@bot.tree.command(name="set-lista", description="Define o canal onde o painel de pagamentos ao vivo será exibido")
@commands.has_permissions(administrator=True)
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    CONFIG_CANAIS["canal_lista"] = canal.id
    
    # Envia o painel inicial no canal escolhido
    embed = gerar_embed_pagamentos()
    nova_msg = await canal.send(embed=embed)
    CONFIG_CANAIS["mensagem_lista_id"] = nova_msg.id
    
    await interaction.followup.send(f"Painel da lista configurado com sucesso em {canal.mention}!", ephemeral=True)

@bot.tree.command(name="lista-pagamentos", description="Atualiza ou mostra o status atual")
async def lista_pagamentos(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await atualizar_painel_lista(bot, interaction.guild)
    await interaction.followup.send("Painel atualizado com sucesso!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    canal_comprovantes_id = CONFIG_CANAIS.get("canal_comprovantes")

    if canal_comprovantes_id and message.channel.id == canal_comprovantes_id:
        if message.attachments:
            user_id = str(message.author.id)
            texto_enviado = message.content if message.content else "Pago"
            hoje = datetime.now().strftime("%d/%m/%Y")
            
            # Salva o pagamento do dia
            PAGAMENTOS[user_id] = {
                "nome": message.author.display_name,
                "valor": texto_enviado,
                "data": hoje
            }

            try:
                await message.add_reaction("✅")
            except Exception:
                pass

            # Atualiza automaticamente o painel no canal da lista em tempo real
            if message.guild:
                await atualizar_painel_lista(bot, message.guild)

    await bot.process_commands(message)

if __name__ == "__main__":
    manter_online()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Erro: A variável de ambiente DISCORD_TOKEN não foi configurada no Render!")
