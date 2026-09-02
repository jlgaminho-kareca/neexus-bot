import os
import threading
from datetime import datetime, time
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands, tasks
from flask import Flask

# Configuração do Flask para manter a porta aberta no Render
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot está online e operacional!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# Configuração do Bot com Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Variáveis para armazenar IDs dos canais e os dados da lista atual
canal_lista_id = None
canal_comprovantes_id = None

# Lista para armazenar os pagamentos recebidos no dia
registros_pagamentos = []

# Horário da atualização automática (00:00 no Horário de Brasília)
HORARIO_BRASILIA = ZoneInfo("America/Sao_Paulo")
HORA_ATUALIZACAO = time(hour=0, minute=0, tzinfo=HORARIO_BRASILIA)


def criar_embed_lista():
    data_atual = datetime.now(HORARIO_BRASILIA).strftime("%d/%m/%Y")
    
    embed = discord.Embed(
        title=f"📊 Status de Pagamentos da Gangue ({data_atual})",
        description="Controle financeiro diário em tempo real.",
        color=discord.Color.blue()
    )
    
    if registros_pagamentos:
        texto_membros = "\n\n".join(registros_pagamentos)
    else:
        texto_membros = "Nenhum comprovante registrado até o momento."
        
    embed.add_field(
        name="Membros",
        value=texto_membros,
        inline=False
    )
    
    return embed


@tasks.loop(time=HORA_ATUALIZACAO)
async def enviar_lista_diaria():
    global canal_lista_id, registros_pagamentos
    if canal_lista_id is not None:
        canal = bot.get_channel(canal_lista_id)
        if canal:
            embed = criar_embed_lista()
            await canal.send(embed=embed)
            registros_pagamentos.clear()
            print("Nova lista diária enviada e registros zerados.")
        else:
            print("Canal da lista não encontrado.")
    else:
        print("Nenhum canal de lista foi configurado ainda.")


@enviar_lista_diaria.before_loop
async def before_enviar_lista():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        await bot.tree.sync()
        print("Comandos sincronizados com sucesso!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

    if not enviar_lista_diaria.is_running():
        enviar_lista_diaria.start()


# Monitora as mensagens enviadas no servidor para capturar os comprovantes
@bot.event
async def on_message(message):
    global canal_comprovantes_id, canal_lista_id, registros_pagamentos
    
    if message.author.bot:
        return

    if canal_comprovantes_id and message.channel.id == canal_comprovantes_id:
        nome_membro = message.author.display_name
        mencao_membro = message.author.mention
        conteudo = message.content if message.content else "Comprovante enviado por imagem/arquivo"
        data_envio = datetime.now(HORARIO_BRASILIA).strftime("%d/%m/%Y %H:%M")
        
        novo_registro = (
            f"• **{mencao_membro}** ({nome_membro})\n"
            f"  Detalhes: {conteudo}\n"
            f"  Data: {data_envio}"
        )
        
        registros_pagamentos.append(novo_registro)
        await message.add_reaction("✅")
        
        if canal_lista_id:
            canal_lista = bot.get_channel(canal_lista_id)
            if canal_lista:
                embed = criar_embed_lista()
                await canal_lista.send("🔔 **Comprovante Novo Registrado! Lista Atualizada:**", embed=embed)

    await bot.process_commands(message)


@bot.tree.command(name="set-comprovantes", description="Define o canal de comprovantes da gangue")
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    global canal_comprovantes_id
    canal_comprovantes_id = canal.id
    await interaction.response.send_message(
        f"✅ Canal de comprovantes configurado para {canal.mention}!", 
        ephemeral=True
    )


@bot.tree.command(name="set-lista", description="Define o canal onde a nova lista diária será enviada")
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    global canal_lista_id
    canal_lista_id = canal.id
    await interaction.response.send_message(
        f"✅ Canal da lista configurado com sucesso para {canal.mention}!", 
        ephemeral=True
    )


@bot.tree.command(name="forcar-lista", description="Força o envio imediato da lista nova")
async def forcar_lista(interaction: discord.Interaction):
    global canal_lista_id
    
    # Tenta usar o canal salvo ou recorre ao canal atual onde o comando foi digitado
    canal_alvo = bot.get_channel(canal_lista_id) if canal_lista_id else interaction.channel
    
    if canal_alvo:
        embed = criar_embed_lista()
        await canal_alvo.send(embed=embed)
        await interaction.response.send_message("✅ Lista forçada enviada com sucesso!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Erro: Não foi possível identificar o canal.", ephemeral=True)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN, reconnect=True)
    
