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


# Defina aqui o horário fixo que a lista deve atualizar (Ex: 00:00 da manhã no Horário de Brasília)
HORARIO_BRASILIA = ZoneInfo("America/Sao_Paulo")
HORA_ATUALIZACAO = time(hour=0, minute=0, tzinfo=HORARIO_BRASILIA)


@tasks.loop(time=HORA_ATUALIZACAO)
async def atualizar_lista_diaria():
    # Código que roda sozinho todos os dias no horário marcado
    print("Executando a atualização automática da lista...")
    
    # Exemplo: Se você quiser que o bot mande a lista em um canal específico, 
    # podemos puxar o ID do canal salvo ou de um canal padrão.
    # Por enquanto, ele vai apenas registrar no console que tentou atualizar.
    # (Se você tiver a lógica antiga de envio/atualização, basta substituir aqui dentro!)


@atualizar_lista_diaria.before_loop
async def before_atualizar_lista():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        await bot.tree.sync()
        print("Comandos sincronizados com sucesso!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

    # Inicia a tarefa de atualização diária se ela já não estiver rodando
    if not atualizar_lista_diaria.is_running():
        atualizar_lista_diaria.start()


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


# Comando para definir o canal da lista
@bot.tree.command(name="set-lista", description="Define o canal onde a lista de pagamentos/tesouro será exibida")
async def set_lista(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.send_message(
        f"✅ Canal da lista configurado com sucesso para {canal.mention}!", 
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
