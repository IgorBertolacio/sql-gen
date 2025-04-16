# --- Arquivo: llm_response_parser.py ---

import re
from typing import List, Dict, Tuple, Optional

# Função auxiliar interna para parsear e validar a string bruta
def _parse_raw_response(llm_response: str) -> Tuple[str, str, str]:
    """
    Valida o formato 'SCHEMA','TABELA','COLUNA' e extrai as strings brutas.
    Lança ValueError se o formato for inválido.
    """
    match = re.match(r"\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*", llm_response.strip())
    if not match:
        raise ValueError(f"Resposta do LLM fora do formato esperado: {llm_response}")
    # Retorna as strings brutas para schema, tabela e coluna
    return match.groups()

# Função auxiliar interna para converter uma string de campo em lista
def _parse_field_to_list(field_str: str) -> List[str]:
    """
    Converte uma string (potencialmente vazia ou com itens separados por ';')
    em uma lista de strings limpas.
    """
    field_str = field_str.strip()
    if field_str == '' or field_str == ' ':
        return []
    return [item.strip() for item in field_str.split(';') if item.strip()]

# --- Novas Funções Específicas ---

def extract_schemas(llm_response: str) -> List[str]:
    """
    Extrai apenas a lista de schemas da resposta estruturada do LLM.

    Args:
        llm_response (str): Resposta do LLM no formato "'SCHEMA','TABELA','COLUNA'".

    Returns:
        List[str]: Lista de nomes de schemas extraídos. Lança ValueError se o formato for inválido.
    """
    schema_str, _, _ = _parse_raw_response(llm_response)
    return _parse_field_to_list(schema_str)

def extract_tables(llm_response: str) -> List[str]:
    """
    Extrai apenas a lista de tabelas da resposta estruturada do LLM.

    Args:
        llm_response (str): Resposta do LLM no formato "'SCHEMA','TABELA','COLUNA'".

    Returns:
        List[str]: Lista de nomes de tabelas extraídos. Lança ValueError se o formato for inválido.
    """
    _, table_str, _ = _parse_raw_response(llm_response)
    return _parse_field_to_list(table_str)

def extract_columns(llm_response: str) -> List[str]:
    """
    Extrai apenas a lista de colunas da resposta estruturada do LLM.

    Args:
        llm_response (str): Resposta do LLM no formato "'SCHEMA','TABELA','COLUNA'".

    Returns:
        List[str]: Lista de nomes de colunas extraídos. Lança ValueError se o formato for inválido.
    """
    _, _, column_str = _parse_raw_response(llm_response)
    return _parse_field_to_list(column_str)

# --- Função Original (mantida para compatibilidade) ---

def parse_llm_structured_response(llm_response: str) -> Dict[str, List[str]]:
    """
    Faz o parsing da resposta estruturada do LLM no formato:
    'SCHEMA','TABELA','COLUNA'

    Retorna um dicionário com listas de schemas, tabelas e colunas.
    Caso algum campo esteja vazio (' '), retorna uma lista vazia para ele.

    Args:
        llm_response (str): Resposta do LLM, ex: "'SCHEMA','TABELA1;TABELA2','COL1;COL2'"

    Returns:
        dict: {'schemas': [...], 'tabelas': [...], 'colunas': [...]}
              Lança ValueError se o formato for inválido.
    """
    # Reutiliza as funções internas/novas para manter a consistência
    schema_str, table_str, column_str = _parse_raw_response(llm_response)
    return {
        'schemas': _parse_field_to_list(schema_str),
        'tabelas': _parse_field_to_list(table_str),
        'colunas': _parse_field_to_list(column_str)
    }
