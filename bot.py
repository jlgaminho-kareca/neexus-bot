import discord
from discord.ext import commands
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Memória interna do bot para guardar os pagamentos do dia
registros_diarios = {}

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Formato aceito no chat: "Nick - Valor: 3000" junto com a foto do comprovante
    if message.attachments:
        conteudo = message.content
        if "-" in conteudo and "Valor:" in conteudo:
            try:
                partes = conteudo.split("-")
                nick = partes[0].strip()
                parte_valor = partes[1].replace("Valor:", "").strip()
                valor = float(parte_valor)
                
                hoje = datetime.now().strftime("%d/%m/%Y")
                if hoje not in registros_diarios:
                    registros_diarios[hoje] = []
                
                print_url = message.attachments[0].url

                registros_diarios[hoje].append({
                    "user": nick,
                    "value": valor,
                    "print": print_url
                })

                await message.add_reaction("✅")
            except Exception as e:
                print(f"Erro ao processar: {e}")

    await bot.process_commands(message)

@bot.command(name="saldo")
async def saldo(ctx):
    hoje = datetime.now().strftime("%d/%m/%Y")
    pagamentos = registros_diarios.get(hoje, [])
    total = sum(item["value"] for item in pagamentos)
    await ctx.send(f"💰 **Saldo Total da Gangue hoje ({hoje}):** R$ {total:,.2f}")

@bot.command(name="painel")
async def painel(ctx):
    hoje = datetime.now().strftime("%d/%m/%Y")
    pagamentos = registros_diarios.get(hoje, [])
    
    embed = discord.Embed(title=f"📋 Comprovantes - {hoje}", color=discord.Color.green())
    
    if not pagamentos:
        embed.description = "Nenhum pagamento registrado hoje ainda."
    else:
        for p in pagamentos:
            embed.add_field(
                name=f"Nick: {p['user']}", 
                value=f"Valor: R$ {p['value']:,.2f}\n[Ver Comprovante]({p['print']})", 
                inline=False
            )
            
    await ctx.send(embed=embed)

# Token configurado
bot.run(os.getenv('DISCORD_TOKEN'))
