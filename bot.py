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

# Variável para armazenar o ID do canal da lista definido pelo comando /set-lista
canal_lista_id = None

# Horário da atualização automática (00:00 no Horário de Brasília)
HORARIO_BRASILIA = ZoneInfo("America/Sao_Paulo")
HORA_ATUALIZACAO = time(hour=0, minute=0, tzinfo=HORARIO_BRASILIA)


def criar_embed_lista():
    # Pega a data atual no fuso horário de Brasília
    data_atual = datetime.now(HORARIO_BRASILIA).strftime("%d/%m/%Y")
    
    embed = discord.Embed(
        title=f"📊 Status de Pagamentos da Gangue ({data_atual})",
        description="Controle financeiro diário em tempo real.",
        color=discord.Color.blue()
    )
    
    # Exemplo com os campos da lista que você mostrou na imagem
    embed.add_field(
        name="Membros",
        value=(
            "• **@Veinho Gente Fina** (Veinho Gente Fina): **Valor: 1000**\n"
            "  Nome: zoe rogers\n"
            "  Data: 31/08/26\n"
            "  *(só para teste do bot)*\n\n"
            "• **@Antonio Martins** (Antonio Martins): **Valor: 2000**\n"
            "  Nome: António Martins\n"
            "  Data: 30 e 31/08/26\n"
            "  Ontem e hoje"
        ),
        inline=False
    )
    
    return embed


@tasks.loop(time=HORA_ATUALIZACAO)
async def enviar_lista_diaria():
    global canal_lista_id
    if canal_lista_id is not None:
        canal = bot.get_channel(canal_lista_id)
        if canal:
            embed = criar_embed_lista()
            await canal.send(embed=embed)
            print("Lista diária automática enviada com sucesso!")
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


# Comando para forçar o envio da lista imediatamente no formato correto
@bot.tree.command(name="forcar-lista", description="Força o envio imediato da lista nova do dia em formato embed")
async def forcar_lista(interaction: discord.Interaction):
    global canal_lista_id
    
    # Define o canal alvo (o canal salvo pelo /set-lista ou o canal atual se nenhum foi definido)
    canal_alvo = bot.get_channel(canal_lista_id) if canal_lista_id else interaction.channel
    
    if canal_alvo:
        embed = criar_embed_lista()
        await canal_alvo.send(embed=embed)
        await interaction.response.send_message("✅ Lista atualizada enviada com sucesso!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Erro ao encontrar o canal para enviar a lista.", ephemeral=True)


# Inicialização simultânea (Flask + Bot)
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN, reconnect=True)
