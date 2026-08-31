import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Configuração do Flask
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot está online e operacional!"


def run_flask():
    # Usa a porta dinâmica do Render ou a porta padrão 10000
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
        print("Comandos de barra sincronizados!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


# Proteção vital contra loops e Rate Limit (Erro 429)
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


# Exemplo do comando de comprovantes (adicione seus outros comandos logo abaixo)
@bot.tree.command(name="set-comprovantes", description="Define o canal de comprovantes")
async def set_comprovantes(interaction: discord.Interaction, canal: discord.TextChannel):
    await interaction.response.send_message(
        f"✅ Canal de comprovantes configurado para {canal.mention}!", 
        ephemeral=True
    )


# Execução simultânea (Flask em background + Bot do Discord)
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN, reconnect=True)
