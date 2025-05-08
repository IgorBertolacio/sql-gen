from typing import List, Dict, Any
from config.core.logging_config import get_logger

logger = get_logger(__name__)

class FilterTables:
    @staticmethod
    def filtrar_tabelas_mantidas(tabelas_mantidas: List[str], resultados_similares: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra as tabelas que a LLM quer manter e seus metadados.
        
        Args:
            tabelas_mantidas: Lista de nomes de tabelas que a LLM quer manter.
            resultados_similares: Resultados da busca de tabelas similares.
            
        Returns:
            Lista de dicionários com os metadados das tabelas mantidas.
        """
        tabelas_filtradas = []
        
        # Se não há tabelas para manter, retorna lista vazia
        if not tabelas_mantidas:
            return tabelas_filtradas
        
        # Para cada resultado da busca
        for resultado in resultados_similares:
            matches = resultado.get("matches", [])
            
            # Para cada match encontrado
            for match in matches:
                table_name = match.get("table_name", "")
                
                # Verifica se a tabela está na lista de tabelas mantidas
                # Pode ser com schema (schema.table) ou apenas o nome da tabela
                nome_tabela_sem_schema = table_name.split(".")[-1] if "." in table_name else table_name
                
                if table_name in tabelas_mantidas or nome_tabela_sem_schema in tabelas_mantidas:
                    # Adiciona à lista de tabelas filtradas
                    tabelas_filtradas.append({
                        "table_name": table_name,
                        "similarity_percentage": match.get("similarity_percentage", 0),
                        "content": match.get("content", "")
                    })
        
        return tabelas_filtradas