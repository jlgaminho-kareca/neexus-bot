import os
import threading
from datetime import time
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

# Variável para armazenar o ID do canal da lista definido pelo comando /set-lista
canal_lista_id = None

# Horário da atualização (00:00 no Horário de Brasília)
HORARIO_BRASILIA = ZoneInfo("America/Sao_Paulo")
HORA_ATUALIZACAO = time(hour=0, minute=0, tzinfo=HORARIO_BRASILIA)


@tasks.loop(time=HORA_ATUALIZACAO)
async def enviar_lista_diaria():
    global canal_lista_id
    if canal_lista_id is not None:
        canal = bot.get_channel(canal_lista_id)
        if canal:
            # Mensagem da nova lista do dia
            await canal.send("📊 **Atualização Diária:** Nova lista do dia iniciada! Aqui estão os registros atualizados.")
            print("Nova lista diária enviada com sucesso!")
        else:
            print("Canal da lista não encontrado.")
    else:
        print("Nenhum canal de lista foi configurado ainda. Use o comando /set-lista.")


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

    # Inicia a tarefa diária
    if not enviar_lista_diaria.is_running():
        enviar_lista_diaria.start()


# Proteção vital contra loops e Rate Limit (Erro 429)
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


# Comando para definir o canal de comprovantes
@bot.tree.command(name="set-comprovantes", description="Define o canal de comprovantes da gangue")
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.send_message(
        f"✅ Canal de comprovantes configurado para {canal.mention}!", 
        ephemeral=True
    )


# Comando para definir o canal onde a lista nova será enviada
@bot.tree.command(name="set-lista", description="Define o canal onde a nova lista diária será enviada")
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    global canal_lista_id
    canal_lista_id = canal.id
    await interaction.response.send_message(
        f"✅ Canal da lista configurado com sucesso para {canal.mention}! A nova lista será enviada nele todos os dias.", 
        ephemeral=True
    )


# Inicialização simultânea (Flask + Bot)
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN, reconnect=True)
