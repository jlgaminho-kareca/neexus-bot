import os
import threading
import discord
from discord.ext import commands
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


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    try:
        await bot.tree.sync()
        print("Comandos sincronizados com sucesso!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


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


# Comando para definir ou atualizar a lista / painel
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
