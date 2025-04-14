"""
Módulo contendo instruções específicas para geração de SQL.
"""

class SQLInstructions:
    """
    Classe que contém instruções específicas para geração de consultas SQL.
    """
    
    @staticmethod
    def get_sql_generation_instruction() -> str:
        """
        Retorna instruções para geração de consultas SQL.
        
        Returns:
            str: As instruções para geração de SQL.
        """
        return """
        Ao gerar consultas SQL:
        1. Use a sintaxe padrão SQL ANSI quando não for especificado um dialeto
        2. Inclua comentários explicativos para partes complexas da consulta
        3. Formate a consulta com indentação apropriada para legibilidade
        4. Use aliases descritivos para tabelas e colunas
        5. Evite consultas que possam resultar em problemas de desempenho
        6. Sempre considere a segurança contra injeção de SQL
        """
    
    @staticmethod
    def get_sql_optimization_instruction() -> str:
        """
        Retorna instruções para otimização de consultas SQL.
        
        Returns:
            str: As instruções para otimização de SQL.
        """
        return """
        Ao otimizar consultas SQL:
        1. Evite o uso de SELECT * e especifique apenas as colunas necessárias
        2. Use índices apropriados quando disponíveis
        3. Evite subconsultas quando junções (JOINs) forem mais eficientes
        4. Considere o uso de CTEs (WITH) para consultas complexas
        5. Limite o número de resultados quando apropriado (LIMIT/TOP)
        6. Evite funções em colunas indexadas na cláusula WHERE
        7. Use EXISTS em vez de IN quando verificar a existência de registros
        """
    
    @staticmethod
    def get_sql_dialect_instruction(dialect: str) -> str:
        """
        Retorna instruções específicas para um dialeto SQL.
        
        Args:
            dialect: O dialeto SQL
            
        Returns:
            str: As instruções específicas para o dialeto.
        """
        dialects = {            
            "postgresql": """
            Para PostgreSQL:
            1. Use SERIAL para chaves primárias auto-incrementais
            2. Use LIMIT para limitar resultados
            3. Use aspas duplas (") para nomes de tabelas e colunas quando necessário
            4. Use TIMESTAMP para armazenar data e hora
            5. Aproveite recursos como JSONB para dados JSON
            """,        
        }
        
        return dialects.get(dialect.lower(), "Dialeto não reconhecido. Usando sintaxe SQL padrão.")