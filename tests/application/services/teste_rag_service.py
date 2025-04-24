"""
Teste detalhado do RAGService que mostra o resultado de cada etapa do processo.
Este teste permite visualizar o fluxo completo de geração de SQL a partir de um prompt.
"""

import os
import sys
import json
import unittest
import logging
from unittest.mock import patch, MagicMock
from pprint import pprint
import numpy as np

# Adiciona o diretório raiz do projeto ao PYTHONPATH para permitir importações relativas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.application.services.rag_service import RAGService
from src.infrastructure.external_services.llm_service import LLMService
from src.infrastructure.external_services.embedding_service import EmbeddingService
from src.application.services.search_service import SearchService
from src.infrastructure.config.api.api_config import GeminiConfig

# Configuração de logging para mostrar os resultados de cada etapa
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cores para formatação do terminal
class Cores:
    HEADER = '\033[95m'
    AZUL = '\033[94m'
    CIANO = '\033[96m'
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    NEGRITO = '\033[1m'
    SUBLINHADO = '\033[4m'
    FIM = '\033[0m'

def formatar_json(obj, indent=2):
    """Formata um objeto como JSON com indentação para melhor visualização."""
    if isinstance(obj, np.ndarray):
        return f"<np.ndarray shape={obj.shape}>"
    return json.dumps(obj, indent=indent, ensure_ascii=False)

class TesteRAGService(unittest.TestCase):
    """Teste detalhado do RAGService que mostra o resultado de cada etapa do processo."""
    
    def setUp(self):
        """Configuração executada antes de cada teste."""
        # Verifica se a API key está configurada
        if not os.getenv("LLM_API_KEY"):
            self.skipTest("LLM_API_KEY não está configurada no ambiente de testes")
    
    def _imprimir_secao(self, titulo, conteudo=None, cor=Cores.AZUL):
        """Imprime uma seção formatada no console."""
        borda = "=" * 80
        print(f"\n{cor}{Cores.NEGRITO}{borda}")
        print(f"{titulo.center(80)}")
        print(f"{borda}{Cores.FIM}\n")
        
        if conteudo is not None:
            if isinstance(conteudo, dict) or isinstance(conteudo, list):
                print(formatar_json(conteudo))
            elif isinstance(conteudo, np.ndarray):
                print(f"<np.ndarray shape={conteudo.shape}>")
            else:
                print(conteudo)
            print()
    
    def _imprimir_etapa(self, numero, titulo, conteudo=None):
        """Imprime uma etapa do processo RAG."""
        titulo_completo = f"ETAPA {numero}: {titulo}"
        self._imprimir_secao(titulo_completo, conteudo, Cores.VERDE)
    
    def _imprimir_resultado(self, resultado):
        """Imprime o resultado final de forma organizada."""
        self._imprimir_secao("RESULTADO FINAL", cor=Cores.AMARELO)
        
        # Imprime cada seção do resultado separadamente para melhor visualização
        print(f"{Cores.NEGRITO}Prompt do Usuário:{Cores.FIM}")
        print(resultado["prompt_usuario"])
        print()
        
        print(f"{Cores.NEGRITO}Dialeto SQL:{Cores.FIM}")
        print(resultado["dialeto_sql"])
        print()
        
        print(f"{Cores.NEGRITO}Tabelas Extraídas do Prompt:{Cores.FIM}")
        print(formatar_json(resultado["tabelas_extraidas_prompt"]))
        print()
        
        print(f"{Cores.NEGRITO}Busca Vetorial - Resultados:{Cores.FIM}")
        # Simplifica a exibição dos resultados da busca vetorial
        resultados_simplificados = []
        for item in resultado["busca_vetorial_resultados"]:
            item_simplificado = {
                "query_table": item["query_table"],
                "matches": []
            }
            for match in item["matches"]:
                # Trunca o conteúdo para não sobrecarregar a saída
                content_preview = match["content"][:100] + "..." if len(match["content"]) > 100 else match["content"]
                item_simplificado["matches"].append({
                    "table_name": match["table_name"],
                    "similarity_percentage": match["similarity_percentage"],
                    "content_preview": content_preview
                })
            resultados_simplificados.append(item_simplificado)
        print(formatar_json(resultados_simplificados))
        print()
        
        print(f"{Cores.NEGRITO}Tabelas Utilizadas como Fonte de Contexto:{Cores.FIM}")
        print(formatar_json(resultado["tabelas_contexto_fonte"]))
        print()
        
        print(f"{Cores.NEGRITO}Contexto Utilizado para LLM:{Cores.FIM}")
        # Trunca o contexto para não sobrecarregar a saída
        contexto_preview = resultado["contexto_utilizado_llm"][:500] + "..." if len(resultado["contexto_utilizado_llm"]) > 500 else resultado["contexto_utilizado_llm"]
        print(contexto_preview)
        print()
        
        print(f"{Cores.NEGRITO}Prompt Final para LLM:{Cores.FIM}")
        # Trunca o prompt final para não sobrecarregar a saída
        prompt_preview = resultado["prompt_final_llm"][:500] + "..." if len(resultado["prompt_final_llm"]) > 500 else resultado["prompt_final_llm"]
        print(prompt_preview)
        print()
        
        print(f"{Cores.NEGRITO}{Cores.CIANO}SQL Gerado:{Cores.FIM}")
        print(resultado["sql_gerado"])
        print()
        
        print(f"{Cores.NEGRITO}Dados de Uso da LLM:{Cores.FIM}")
        print(formatar_json(resultado["uso_llm_sql_gen"]))
        print()
    
    def test_rag_service_completo(self):
        """
        Teste completo do RAGService que mostra o resultado de cada etapa.
        """
        # Solicita o prompt do usuário
        print(f"\n{Cores.NEGRITO}Digite o prompt para gerar SQL (ou pressione Enter para usar o prompt padrão):{Cores.FIM}")
        prompt_usuario = input()
        
        # Usa um prompt padrão se o usuário não fornecer um
        if not prompt_usuario:
            prompt_usuario = "Quero uma consulta que mostre os clientes que fizeram mais de 3 pedidos no último mês"
            print(f"Usando prompt padrão: {prompt_usuario}")
        
        # Etapa 1: Inicialização e Extração Inicial
        self._imprimir_etapa(1, "Inicialização e Extração Inicial")
        
        # Patch para capturar a chamada à API e mostrar o resultado
        original_get_api_response = LLMService.get_api_response
        original_get_response_text = LLMService.get_response_text
        
        try:
            # Captura a chamada à API de extração
            resposta_extracao_bruta = None
            texto_resposta_extracao = None
            
            def mock_get_api_response(prompt, modelo='gemini-2.0-flash'):
                nonlocal resposta_extracao_bruta
                print(f"Enviando prompt para LLM ({modelo})...")
                resposta_extracao_bruta = original_get_api_response(prompt, modelo)
                return resposta_extracao_bruta
            
            def mock_get_response_text(resposta_api):
                nonlocal texto_resposta_extracao
                texto_resposta_extracao = original_get_response_text(resposta_api)
                return texto_resposta_extracao
            
            # Aplica os patches
            LLMService.get_api_response = mock_get_api_response
            LLMService.get_response_text = mock_get_response_text
            
            # Executa o RAGService
            resultado = RAGService.generate_sql_from_prompt(prompt_usuario)
            
            # Mostra o resultado da extração inicial
            self._imprimir_secao("Resposta da LLM (Extração Inicial)", texto_resposta_extracao)
            self._imprimir_secao("Tabelas Extraídas", resultado["tabelas_extraidas_prompt"])
            
            # Etapa 2: Geração de Embeddings
            self._imprimir_etapa(2, "Geração de Embeddings")
            if "tabelas_extraidas_prompt" in resultado and resultado["tabelas_extraidas_prompt"]:
                print(f"Embeddings gerados para as tabelas: {resultado['tabelas_extraidas_prompt']}")
                print("Os embeddings são vetores numéricos e não são exibidos por completo.")
            else:
                print("Nenhuma tabela extraída para gerar embeddings.")
            
            # Etapa 3: Busca Vetorial
            self._imprimir_etapa(3, "Busca Vetorial")
            if "busca_vetorial_resultados" in resultado:
                # Simplifica a exibição dos resultados da busca vetorial
                resultados_simplificados = []
                for item in resultado["busca_vetorial_resultados"]:
                    item_simplificado = {
                        "query_table": item["query_table"],
                        "matches": []
                    }
                    for match in item["matches"]:
                        # Trunca o conteúdo para não sobrecarregar a saída
                        content_preview = match["content"][:100] + "..." if len(match["content"]) > 100 else match["content"]
                        item_simplificado["matches"].append({
                            "table_name": match["table_name"],
                            "similarity_percentage": match["similarity_percentage"],
                            "content_preview": content_preview
                        })
                    resultados_simplificados.append(item_simplificado)
                self._imprimir_secao("Resultados da Busca Vetorial", resultados_simplificados)
            else:
                print("Nenhum resultado da busca vetorial disponível.")
            
            # Etapa 4: Recuperação de Contexto
            self._imprimir_etapa(4, "Recuperação de Contexto")
            if "tabelas_contexto_fonte" in resultado:
                self._imprimir_secao("Tabelas Utilizadas como Fonte de Contexto", resultado["tabelas_contexto_fonte"])
            else:
                print("Nenhuma tabela utilizada como fonte de contexto.")
            
            # Etapa 5: Construção do Prompt Final
            self._imprimir_etapa(5, "Construção do Prompt Final")
            if "contexto_utilizado_llm" in resultado:
                # Trunca o contexto para não sobrecarregar a saída
                contexto_preview = resultado["contexto_utilizado_llm"][:500] + "..." if len(resultado["contexto_utilizado_llm"]) > 500 else resultado["contexto_utilizado_llm"]
                self._imprimir_secao("Contexto Utilizado para LLM", contexto_preview)
            
            if "prompt_final_llm" in resultado:
                # Trunca o prompt final para não sobrecarregar a saída
                prompt_preview = resultado["prompt_final_llm"][:500] + "..." if len(resultado["prompt_final_llm"]) > 500 else resultado["prompt_final_llm"]
                self._imprimir_secao("Prompt Final para LLM", prompt_preview)
            
            # Etapa 6: Chamada Final ao LLM para Geração de SQL
            self._imprimir_etapa(6, "Chamada Final ao LLM para Geração de SQL")
            if "sql_gerado" in resultado:
                self._imprimir_secao("SQL Gerado", resultado["sql_gerado"], Cores.CIANO)
            
            if "uso_llm_sql_gen" in resultado:
                self._imprimir_secao("Dados de Uso da LLM", resultado["uso_llm_sql_gen"])
            
            # Etapa 7: Resultado Final
            self._imprimir_etapa(7, "Resultado Final")
            self._imprimir_resultado(resultado)
            
        finally:
            # Restaura os métodos originais
            LLMService.get_api_response = original_get_api_response
            LLMService.get_response_text = original_get_response_text


if __name__ == '__main__':
    unittest.main()
