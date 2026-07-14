"""
Módulo de Leitura da Planilha de Consumo
Lê a planilha .xls hierárquica (aba "containers") e transforma
em registros flat para processamento pelo RPA.
"""

import calendar
import logging
from datetime import datetime
from pathlib import Path

import xlrd
import pandas as pd

from config import (
    CAMINHO_PLANILHA, ABA_PLANILHA, COLUNA_DATA,
    MAPEAMENTO_COLUNAS, EMPRESAS, LINHA_INICIO_DADOS
)

logger = logging.getLogger(__name__)


def _coluna_para_indice(coluna_letra):
    """Converte letra da coluna (A, B, C...) para índice 0-based."""
    resultado = 0
    for char in coluna_letra.upper():
        resultado = resultado * 26 + (ord(char) - ord('A') + 1)
    return resultado - 1


def _ler_valor_data(workbook, sheet, row, col_idx):
    """Lê uma célula de data, tratando formatos mistos (texto e data)."""
    cell = sheet.cell(row, col_idx)
    cell_type = cell.ctype

    if cell_type == xlrd.XL_CELL_DATE:
        date_tuple = xlrd.xldate_as_tuple(cell.value, workbook.datemode)
        return datetime(date_tuple[0], date_tuple[1], date_tuple[2])

    if cell_type == xlrd.XL_CELL_TEXT:
        texto = cell.value.strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, fmt)
            except ValueError:
                continue
        logger.warning(f"Não foi possível converter texto '{texto}' como data (linha {row + 1})")
        return None

    if cell_type == xlrd.XL_CELL_NUMBER:
        try:
            date_tuple = xlrd.xldate_as_tuple(cell.value, workbook.datemode)
            return datetime(date_tuple[0], date_tuple[1], date_tuple[2])
        except Exception:
            return None

    return None


def _ler_valor_numero(sheet, row, col_idx):
    """Lê uma célula numérica, tratando vírgulas e textos."""
    cell = sheet.cell(row, col_idx)
    cell_type = cell.ctype

    if cell_type == xlrd.XL_CELL_NUMBER:
        return cell.value

    if cell_type == xlrd.XL_CELL_TEXT:
        texto = cell.value.strip().replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return None

    return None


def _formatar_consumo(valor):
    """
    Formata o valor de consumo para coincidir exatamente com o que é exibido no Excel.
    - Arredonda para remover artefatos de ponto flutuante (ex: 0.33000000000000185 → 0.33)
    - Inteiros ficam sem decimais (ex: 152.0 → '152')
    - Decimais usam vírgula como separador (ex: 0.23 → '0,23')
    """
    # Arredondar para 6 casas para eliminar ruído de ponto flutuante
    valor_limpo = round(valor, 6)
    if valor_limpo == int(valor_limpo):
        return str(int(valor_limpo))
    else:
        # Formatar com precisão e remover zeros à direita desnecessários
        formatado = f"{valor_limpo:.6f}".rstrip("0")
        return formatado.replace(".", ",")


def _encontrar_ultima_linha_dados(workbook, sheet, col_data_idx):
    """Encontra o índice da última linha que contém dados válidos na planilha."""
    ultima_linha = None
    for row_idx in range(LINHA_INICIO_DADOS - 1, sheet.nrows):
        data_ref = _ler_valor_data(workbook, sheet, row_idx, col_data_idx)
        if data_ref is not None:
            ultima_linha = row_idx
    return ultima_linha


def ler_planilha(caminho=None, aba=None):
    """
    Lê a planilha hierárquica e retorna uma lista de registros flat.
    Processa APENAS a última linha de dados válida na planilha,
    pois as linhas anteriores já foram cobradas em meses passados.

    Returns:
        list[dict]: Lista de dicionários, cada um representando uma RSP a criar.
            Cada dict tem: data, empresa, cnpj, tipo_servico, consumo,
                           consumo_formatado, data_inicio, data_fim
    """
    caminho = caminho or CAMINHO_PLANILHA
    aba = aba or ABA_PLANILHA

    if not Path(caminho).exists():
        raise FileNotFoundError(f"Planilha não encontrada: {caminho}")

    logger.info(f"Abrindo planilha: {caminho}")
    workbook = xlrd.open_workbook(caminho)
    sheet = workbook.sheet_by_name(aba)

    logger.info(f"Aba '{aba}' selecionada: {sheet.nrows} linhas, {sheet.ncols} colunas")

    col_data_idx = _coluna_para_indice(COLUNA_DATA)

    # Encontrar a última linha com dados válidos
    ultima_linha = _encontrar_ultima_linha_dados(workbook, sheet, col_data_idx)

    if ultima_linha is None:
        logger.warning("Nenhuma linha de dados válida encontrada na planilha.")
        return []

    logger.info(f"Última linha de dados encontrada: {ultima_linha + 1}")

    registros = []
    row_idx = ultima_linha
    data_ref = _ler_valor_data(workbook, sheet, row_idx, col_data_idx)

    # Calcular datas mensais: dia 01 até último dia do mês
    primeiro_dia = data_ref.replace(day=1, hour=0, minute=0, second=0)
    ultimo_dia_mes = calendar.monthrange(data_ref.year, data_ref.month)[1]
    ultimo_dia = data_ref.replace(day=ultimo_dia_mes, hour=23, minute=59, second=59)

    logger.info(
        f"Período de cobrança: {primeiro_dia.strftime('%d/%m/%Y')} "
        f"até {ultimo_dia.strftime('%d/%m/%Y')}"
    )

    for col_inicio, col_fim, col_consumo, empresa, tipo_servico in MAPEAMENTO_COLUNAS:
        idx_consumo = _coluna_para_indice(col_consumo)
        consumo = _ler_valor_numero(sheet, row_idx, idx_consumo)

        if consumo is None or consumo <= 0:
            continue

        cnpj = EMPRESAS.get(empresa)
        if not cnpj:
            logger.warning(f"Empresa '{empresa}' não encontrada no mapeamento de CNPJs")
            continue

        consumo_formatado = _formatar_consumo(consumo)

        registros.append({
            "linha_planilha": row_idx + 1,
            "data": data_ref,
            "empresa": empresa,
            "cnpj": cnpj,
            "tipo_servico": tipo_servico,
            "consumo": consumo,
            "consumo_formatado": consumo_formatado,
            "data_inicio": primeiro_dia,
            "data_fim": ultimo_dia,
        })

        logger.debug(
            f"  {empresa} | {tipo_servico} | consumo={consumo_formatado} | "
            f"{primeiro_dia.strftime('%d/%m/%Y %H:%M')} - {ultimo_dia.strftime('%d/%m/%Y %H:%M')}"
        )

    logger.info(f"Total de registros processáveis: {len(registros)}")
    return registros


def gerar_resumo(registros):
    """Gera um resumo dos registros para log."""
    if not registros:
        return "Nenhum registro encontrado."

    empresas_count = {}
    for reg in registros:
        chave = f"{reg['empresa']} - {reg['tipo_servico']}"
        empresas_count[chave] = empresas_count.get(chave, 0) + 1

    linhas = [f"Total: {len(registros)} RSPs a criar"]
    for chave, count in empresas_count.items():
        linhas.append(f"  - {chave}: {count}")

    return "\n".join(linhas)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    try:
        registros = ler_planilha()
        print(gerar_resumo(registros))

        print("\n--- Detalhes ---")
        for i, reg in enumerate(registros, 1):
            print(
                f"{i}. [{reg['linha_planilha']}] {reg['empresa']} | "
                f"{reg['tipo_servico']} | {reg['consumo']} | "
                f"{reg['data_inicio'].strftime('%d/%m/%Y %H:%M')} - "
                f"{reg['data_fim'].strftime('%d/%m/%Y %H:%M')}"
            )
    except Exception as e:
        print(f"Erro: {e}")
