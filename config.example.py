"""
Configurações do RPA - RSP OpenPort
Sistema CODEBA - Porto de Ilhéus

INSTRUÇÕES:
1. Copie este arquivo como "config.py"
2. Preencha as credenciais e o caminho da planilha abaixo
3. Nunca envie o config.py real para o GitHub (já está no .gitignore)
"""

from pathlib import Path

# ============================================================
# CREDENCIAIS DO PORTAL OPENPORT
# ============================================================
URL_BASE = "https://openportilheus.codeba.gov.br/openportcodeba/"
USUARIO = "SEU_CPF_AQUI"       # Ex: "12345678900"
SENHA = "SUA_SENHA_AQUI"       # Ex: "Senha@2025"

# ============================================================
# CÓDIGOS DAS TELAS
# ============================================================
TELA_CAPA = "6050"
TELA_APONTAMENTO = "6060"

# ============================================================
# PLANILHA DE ENTRADA
# ============================================================
CAMINHO_PLANILHA = r"CAMINHO_COMPLETO_DA_PLANILHA.xls"
# Ex: r"Y:\COBRANÇA MENSAL\PLANILHA 25 - 26 CONSUMO ÁGUA E ENERGIA.xls"
ABA_PLANILHA = "CONTAINERS"   # Nome exato da aba no Excel

# ============================================================
# EMPRESAS E SEUS CNPJs
# ============================================================
EMPRESAS = {
    "AIS":            "00000000000000",  # Substitua pelo CNPJ real
    "BASE LIBA":      "00000000000000",
    "INTERMARÍTIMA":  "00000000000000",
    "IRMÃOS BRITO":   "00000000000000",
}

# ============================================================
# MAPEAMENTO DAS COLUNAS DA PLANILHA (colunas B até V)
# Cada tupla: (coluna_inicial, coluna_final, coluna_consumo, empresa, tipo_servico)
# ============================================================
MAPEAMENTO_COLUNAS = [
    ("B", "C", "D", "AIS",           "agua"),
    ("E", "F", "G", "AIS",           "energia"),
    ("H", "I", "J", "INTERMARÍTIMA", "energia"),
    ("K", "L", "M", "BASE LIBA",     "energia"),
    ("N", "O", "P", "BASE LIBA",     "agua"),
    ("Q", "R", "S", "IRMÃOS BRITO",  "energia"),
    ("T", "U", "V", "IRMÃOS BRITO",  "agua"),
]

# Coluna da data (coluna A)
COLUNA_DATA = "A"

# Linha onde começam os dados (após cabeçalhos mesclados)
LINHA_INICIO_DADOS = 5

# ============================================================
# MAPEAMENTO DE SERVIÇOS (códigos do OpenPort)
# ============================================================
SERVICOS = {
    "agua": {
        "codigo": "75",
        "descricao": "ÁGUA PARA CONSUMIDOR/USUARIO M3",
        "unidade": "METRO CUBICO",
        "texto_obs": "consumo de água",
    },
    "energia": {
        "codigo": "76",
        "descricao": "SUPRIMENTO ENERGIA ELETRICA LIGAÇÃO OU DESLIGAÇÃO",
        "unidade": "KILLOWAT HORA",
        "texto_obs": "consumo de energia",
    },
    "container": {
        "codigo": "106",
        "descricao": "UTILIZAÇÃO DE ÁREA PÚBLICA",
        "unidade": "CONTEINER",
        "texto_obs": "utilização de container",
    },
    "area": {
        "codigo": "106",
        "descricao": "UTILIZAÇÃO DE ÁREA PÚBLICA",
        "unidade": "METRO QUADRADO",
        "texto_obs": "utilização de área",
    },
}

# ============================================================
# MAPEAMENTO DE MESES (em português)
# ============================================================
MESES = {
    1: "janeiro", 2: "fevereiro", 3: "março",    4: "abril",
    5: "maio",    6: "junho",     7: "julho",     8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}

# ============================================================
# TIMEOUTS E RETENTATIVAS
# ============================================================
TIMEOUT_PADRAO   = 10
TIMEOUT_LONGO    = 20
TIMEOUT_ULTRALONGO = 30

MAX_TENTATIVAS      = 3
INTERVALO_TENTATIVA = 2
