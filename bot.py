import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Configuração do Flask para o Render não derrubar
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot está online!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# Configuração do Bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
  print(f"Bot conectado como {bot.user}")


# Inicia o Flask em uma thread separada para não bloquear o bot
if __name__ == "__main__":
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # Token puxado direto das variáveis de ambiente do Render
  TOKEN = os.environ.get("DISCORD_TOKEN")
  if TOKEN:
    bot.run(TOKEN, reconnect=True)
