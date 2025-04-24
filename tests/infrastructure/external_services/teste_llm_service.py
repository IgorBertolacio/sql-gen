"""
Testes para o serviço LLM da Google (Gemini).
Este módulo testa a conectividade e funcionalidades básicas do LLMService.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz do projeto ao PYTHONPATH para permitir importações relativas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.infrastructure.external_services.llm_service import LLMService
from src.infrastructure.config.api.api_config import GeminiConfig


class TesteLLMService(unittest.TestCase):
    """Testes para o LLMService que interage com a API Gemini da Google."""
    
    def setUp(self):
        """Configuração executada antes de cada teste."""
        # Verifica se a API key está configurada
        if not os.getenv("LLM_API_KEY"):
            self.skipTest("LLM_API_KEY não está configurada no ambiente de testes")
    
    def test_configuracao_api(self):
        """Testa se a configuração da API está correta."""
        self.assertTrue(GeminiConfig.is_configured(), 
                       "A API do Gemini não está configurada corretamente")
    
    def test_conexao_api(self):
        """Testa a conexão com a API do Gemini."""
        try:
            # Tenta obter uma resposta simples
            resposta = LLMService.get_api_response("Olá, como vai?")
            self.assertIsNotNone(resposta, "A resposta da API não deveria ser None")
        except Exception as e:
            self.fail(f"A conexão com a API falhou: {str(e)}")
    
    def test_processamento_prompt(self):
        """Testa o processamento completo de um prompt."""
        resultado = LLMService.processar_prompt("Qual é a capital do Brasil?")
        
        # Verifica se o resultado contém os campos esperados
        self.assertIn("resposta", resultado, "O resultado deve conter o campo 'resposta'")
        self.assertIn("uso", resultado, "O resultado deve conter o campo 'uso'")
        
        # Verifica se a resposta não está vazia
        self.assertTrue(resultado["resposta"], "A resposta não deveria estar vazia")
    
    @patch('src.infrastructure.external_services.llm_service.LLMService.get_api_response')
    def test_extracao_texto_resposta(self, mock_get_api_response):
        """Testa a extração de texto da resposta da API."""
        # Configura o mock
        mock_resposta = MagicMock()
        mock_resposta.text = "Texto de resposta simulado"
        mock_get_api_response.return_value = mock_resposta
        
        # Executa o método
        texto = LLMService.get_response_text(mock_resposta)
        
        # Verifica o resultado
        self.assertEqual(texto, "Texto de resposta simulado")
    
    @patch('src.infrastructure.external_services.llm_service.LLMService.get_api_response')
    def test_extracao_dados_uso(self, mock_get_api_response):
        """Testa a extração de dados de uso da resposta da API."""
        # Configura o mock
        mock_resposta = MagicMock()
        mock_result = MagicMock()
        mock_metadata = MagicMock()
        
        mock_metadata.prompt_token_count = 10
        mock_metadata.candidates_token_count = 20
        mock_metadata.total_token_count = 30
        
        mock_result.usage_metadata = mock_metadata
        mock_resposta._result = mock_result
        
        mock_get_api_response.return_value = mock_resposta
        
        # Executa o método
        dados_uso = LLMService.get_usage_data(mock_resposta)
        
        # Verifica o resultado
        self.assertEqual(dados_uso["tokens_entrada"], 10)
        self.assertEqual(dados_uso["tokens_saida"], 20)
        self.assertEqual(dados_uso["tokens_total"], 30)


if __name__ == '__main__':
    unittest.main()
