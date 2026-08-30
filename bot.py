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
        print("Aviso: canal_lista não está definido.")
        return
        
    canal = guild.get_channel(canal_lista_id)
    if not canal:
        try:
            canal = await bot_instance.fetch_channel(canal_lista_id)
        except Exception as e:
            print(f"Erro ao buscar canal da lista: {e}")
            return

    embed = gerar_embed_pagamentos()

    if msg_id:
        try:
            msg = await canal.fetch_message(msg_id)
            await msg.edit(embed=embed)
            return
        except Exception:
            pass # Se falhou ao editar, cria uma nova
            
    try:
        nova_msg = await canal.send(embed=embed)
        CONFIG_CANAIS["mensagem_lista_id"] = nova_msg.id
        print("Painel criado com sucesso!")
    except Exception as e:
        print(f"Erro crítico ao enviar mensagem no canal da lista: {e}")

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
    CONFIG_CANAIS["mensagem_lista_id"] = None # Reseta para forçar a criação de um novo
    
    try:
        embed = gerar_embed_pagamentos()
        nova_msg = await canal.send(embed=embed)
        CONFIG_CANAIS["mensagem_lista_id"] = nova_msg.id
        await interaction.followup.send(f"Painel criado com sucesso em {canal.mention}!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Erro ao criar o painel no canal {canal.mention}. Verifique se eu tenho permissão de 'Enviar Mensagens' e 'Ver Canal' nele. Erro: {e}", ephemeral=True)

@bot.tree.command(name="forcar-painel", description="Força a criação ou atualização do painel")
async def forcar_painel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await atualizar_painel_lista(bot, interaction.guild)
    await interaction.followup.send("Painel forçado com sucesso!", ephemeral=True)

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
            
            PAGAMENTOS[user_id] = {
                "nome": message.author.display_name,
                "valor": texto_enviado,
                "data": hoje
            }

            try:
                await message.add_reaction("✅")
            except Exception:
                pass

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
