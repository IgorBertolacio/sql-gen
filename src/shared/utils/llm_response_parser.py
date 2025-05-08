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

def parse_verification_response(llm_response: str) -> Dict[str, any]:
    """
    Faz o parsing da resposta da LLM para verificação de suficiência de dados.
    
    A resposta pode ser de dois tipos:
    1. "2002" - Indica que os dados são suficientes
    2. "1001;tabelas_mantidas;tabelas_solicitadas;motivo" - Indica necessidade de mais dados
    
    Args:
        llm_response (str): Resposta da LLM
        
    Returns:
        Dict: {
            'codigo': '1001' ou '2002',
            'tabelas_mantidas': lista de tabelas a manter (vazia se código 2002),
            'tabelas_solicitadas': lista de tabelas solicitadas (vazia se código 2002),
            'motivo': motivo da solicitação (vazio se código 2002)
        }
    """
    # Limpa a resposta e remove marcadores de código Markdown
    resposta_limpa = llm_response.strip()
    
    # Remove marcadores de código Markdown (```) se presentes
    resposta_limpa = re.sub(r'^```[\w]*\n', '', resposta_limpa)
    resposta_limpa = re.sub(r'\n```$', '', resposta_limpa)
    
    # Remove "resultado_busca" se estiver presente no início
    resposta_limpa = re.sub(r'^resultado_busca\s*\n?', '', resposta_limpa)
    
    resposta_limpa = resposta_limpa.strip()
    
    # Verifica se é o código 2002 (dados suficientes)
    if resposta_limpa == "2002":
        return {
            'codigo': '2002',
            'tabelas_mantidas': [],
            'tabelas_solicitadas': [],
            'motivo': ''
        }
    
    # Verifica se começa com 1001 (necessidade de mais dados)
    if resposta_limpa.startswith("1001"):
        partes = resposta_limpa.split(';')
        
        # Verifica se tem todas as partes necessárias
        if len(partes) >= 4:
            # Extrai as tabelas mantidas
            tabelas_mantidas = [t.strip() for t in partes[1].split(',') if t.strip()]
            
            # Extrai as tabelas solicitadas
            tabelas_solicitadas = [t.strip() for t in partes[2].split(',') if t.strip()]
            
            # Extrai o motivo (pode ter ponto e vírgula no motivo, então juntamos o resto)
            motivo = ';'.join(partes[3:])
            
            return {
                'codigo': '1001',
                'tabelas_mantidas': tabelas_mantidas,
                'tabelas_solicitadas': tabelas_solicitadas,
                'motivo': motivo
            }
    
    # Se chegou aqui, a resposta não está em um formato reconhecido
    return {
        'codigo': 'erro',
        'tabelas_mantidas': [],
        'tabelas_solicitadas': [],
        'motivo': f'Formato de resposta não reconhecido: {resposta_limpa}'
    }