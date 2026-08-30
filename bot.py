import os
import json
import discord
from discord.ext import commands
from discord import app_commands

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ARQUIVO_DADOS = "dados_gangue.json"

# IDs dos Canais e Cargos (ALTERE AQUI COM OS IDs DO SEU SERVIDOR)
CANAL_COMPROVANTES_ID = 000000000000000000  # Canal onde a galera manda print
CANAL_PAINEL_STAFF_ID = 000000000000000000  # Canal onde a staff aprova/reprova
CARGO_MEMBRO_ID = 000000000000000000       # Cargo de membro da gangue

# Função para carregar os dados salvos
def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return {"pagamentos": {}, "saldo_total": 0}
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"pagamentos": {}, "saldo_total": 0}

# Função para salvar os dados
def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot conectado como {bot.user} e {len(synced)} comandos sincronizados!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

# Monitor de mensagens no canal de comprovantes
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == CANAL_COMPROVANTES_ID:
        # Verifica se mandou imagem ou link de comprovante
        if message.attachments or "http" in message.content:
            canal_staff = bot.get_channel(CANAL_PAINEL_STAFF_ID)
            if canal_staff:
                embed = discord.Embed(
                    title="💳 Novo Comprovante Enviado",
                    description=f"**Membro:** {message.author.mention}\n**Nick:** {message.author.display_name}",
                    color=discord.Color.gold()
                )
                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)
                
                view = PainelStaffView(message.author.id, message.author.display_name)
                await canal_staff.send(embed=embed, view=view)
                await message.add_reaction("⏳")

    await bot.process_commands(message)

# Botões de Aprovação da Staff
class PainelStaffView(discord.ui.View):
    def __init__(self, membro_id, membro_nome):
        super().__init__(timeout=None)
        self.membro_id = membro_id
        self.membro_nome = membro_nome

    @discord.ui.button(label="Aprovar (50k)", style=discord.ButtonStyle.green, custom_id="aprovar_pagamento")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Valor padrão do pagamento da semana
        valor = 50000 
        
        dados = carregar_dados()
        membro_str = str(self.membro_id)
        
        dados["saldo_total"] += valor
        dados["pagamentos"][membro_str] = {
            "nome": self.membro_nome,
            "pago": True,
            "valor": valor
        }
        salvar_dados(dados)

        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(content=f"✅ Comprovante de **{self.membro_nome}** aprovado por {interaction.user.mention}!", view=self)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.red, custom_id="recusar_pagamento")
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"❌ Comprovante de **{self.membro_nome}** recusado por {interaction.user.mention}.", view=self)

# Comando: /saldo-total
@bot.tree.command(name="saldo-total", description="Mostra o saldo total do caixa da gangue.")
async def saldo_total(interaction: discord.Interaction):
    dados = carregar_dados()
    saldo = dados.get("saldo_total", 0)
    
    embed = discord.Embed(
        title="💰 Caixa da Gangue",
        description=f"O saldo total atual no cofre é de: **R$ {saldo:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# Comando: /lista-nao-pagou
@bot.tree.command(name="lista-nao-pagou", description="Lista os membros que ainda não enviaram o pagamento.")
async def lista_nao_pagou(interaction: discord.Interaction):
    guild = interaction.guild
    cargo = guild.get_role(CARGO_MEMBRO_ID)
    
    if not cargo:
        await interaction.response.send_message("❌ Cargo de membro não configurado corretamente no código.", ephemeral=True)
        return

    dados = carregar_dados()
    pagamentos = dados.get("pagamentos", {})

    inadimplentes = []
    for membro in cargo.members:
        membro_str = str(membro.id)
        if membro_str not in pagamentos or not pagamentos[membro_str].get("pago", False):
            inadimplentes.append(membro.mention)

    if not inadimplentes:
        descricao = "🎉 Todos os membros pagaram a taxa!"
    else:
        descricao = "\n".join(inadimplentes)

    embed = discord.Embed(
        title="⚠️ Lista de Inadimplentes",
        description=descricao,
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

# Pega o token de forma segura do ambiente configurado no Render
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERRO: Token do Discord não encontrado nas variáveis de ambiente!")
