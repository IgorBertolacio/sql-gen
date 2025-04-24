"""
Script para executar o teste do RAGService e exibir os resultados em uma página HTML.
"""

import os
import sys
import json
import tempfile
import webbrowser
from datetime import datetime
import unittest
from io import StringIO
import contextlib
import html
import numpy as np

# Adiciona o diretório raiz do projeto ao PYTHONPATH para permitir importações relativas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Importa o teste do RAGService
from tests.application.services.teste_rag_service import TesteRAGService

class HTMLFormatter:
    """Classe para formatar os resultados do teste em HTML."""
    
    @staticmethod
    def formatar_json(obj, indent=2):
        """Formata um objeto como JSON com indentação para melhor visualização."""
        if isinstance(obj, np.ndarray):
            return f"&lt;np.ndarray shape={obj.shape}&gt;"
        return json.dumps(obj, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def gerar_html(prompt_usuario, resultado, output):
        """Gera o HTML para exibir os resultados do teste."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Teste RAGService - {timestamp}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                h1, h2, h3, h4 {{
                    color: #2c3e50;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .header {{
                    background-color: #3498db;
                    color: white;
                    padding: 20px;
                    border-radius: 8px 8px 0 0;
                    margin-bottom: 20px;
                }}
                .section {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                    background-color: #fff;
                }}
                .section-header {{
                    background-color: #f8f9fa;
                    padding: 10px;
                    margin: -15px -15px 15px -15px;
                    border-bottom: 1px solid #ddd;
                    border-radius: 8px 8px 0 0;
                    font-weight: bold;
                }}
                .etapa {{
                    border-left: 5px solid #3498db;
                    padding-left: 15px;
                    margin-bottom: 20px;
                }}
                .etapa-header {{
                    background-color: #3498db;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }}
                .sql-result {{
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                    font-family: 'Courier New', monospace;
                    white-space: pre-wrap;
                    margin: 10px 0;
                }}
                .json-data {{
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                    font-family: 'Courier New', monospace;
                    white-space: pre-wrap;
                    margin: 10px 0;
                }}
                .prompt-input {{
                    background-color: #f0f7ff;
                    border: 1px solid #b8daff;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 10px 0;
                }}
                .final-result {{
                    border-left: 5px solid #2ecc71;
                }}
                .table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10px 0;
                }}
                .table th, .table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                .table th {{
                    background-color: #f2f2f2;
                }}
                .table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .log-output {{
                    background-color: #2c3e50;
                    color: #ecf0f1;
                    padding: 15px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    white-space: pre-wrap;
                    max-height: 300px;
                    overflow-y: auto;
                    margin: 10px 0;
                }}
                .collapsible {{
                    background-color: #f1f1f1;
                    color: #444;
                    cursor: pointer;
                    padding: 18px;
                    width: 100%;
                    border: none;
                    text-align: left;
                    outline: none;
                    font-size: 15px;
                    border-radius: 4px;
                    margin-bottom: 5px;
                }}
                .active, .collapsible:hover {{
                    background-color: #ccc;
                }}
                .content {{
                    padding: 0 18px;
                    display: none;
                    overflow: hidden;
                    background-color: #f9f9f9;
                    border-radius: 0 0 4px 4px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Teste Detalhado do RAGService</h1>
                <p>Executado em: {timestamp}</p>
            </div>
            
            <div class="container">
                <h2>Prompt do Usuário</h2>
                <div class="prompt-input">
                    {html.escape(prompt_usuario)}
                </div>
                
                <h2>Etapas do Processo</h2>
                
                <button class="collapsible">Etapa 1: Inicialização e Extração Inicial</button>
                <div class="content">
                    <div class="etapa">
                        <h3>Resposta da LLM (Extração Inicial)</h3>
                        <div class="json-data">
                            {html.escape(resultado.get("texto_resposta_extracao", "Não disponível"))}
                        </div>
                        
                        <h3>Tabelas Extraídas</h3>
                        <div class="json-data">
                            {html.escape(HTMLFormatter.formatar_json(resultado.get("tabelas_extraidas_prompt", [])))}
                        </div>
                    </div>
                </div>
                
                <button class="collapsible">Etapa 2: Geração de Embeddings</button>
                <div class="content">
                    <div class="etapa">
                        <p>Embeddings gerados para as tabelas:</p>
                        <div class="json-data">
                            {html.escape(HTMLFormatter.formatar_json(resultado.get("tabelas_extraidas_prompt", [])))}
                        </div>
                        <p><em>Os embeddings são vetores numéricos e não são exibidos por completo.</em></p>
                    </div>
                </div>
                
                <button class="collapsible">Etapa 3: Busca Vetorial</button>
                <div class="content">
                    <div class="etapa">
                        <h3>Resultados da Busca Vetorial</h3>
                        <div class="json-data">
        """
        
        # Adiciona os resultados da busca vetorial
        if "busca_vetorial_resultados" in resultado:
            resultados_simplificados = []
            for item in resultado.get("busca_vetorial_resultados", []):
                item_simplificado = {
                    "query_table": item.get("query_table", ""),
                    "matches": []
                }
                for match in item.get("matches", []):
                    content = match.get("content", "")
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    item_simplificado["matches"].append({
                        "table_name": match.get("table_name", ""),
                        "similarity_percentage": match.get("similarity_percentage", 0),
                        "content_preview": content_preview
                    })
                resultados_simplificados.append(item_simplificado)
            html_content += html.escape(HTMLFormatter.formatar_json(resultados_simplificados))
        else:
            html_content += "Nenhum resultado da busca vetorial disponível."
        
        html_content += """
                        </div>
                    </div>
                </div>
                
                <button class="collapsible">Etapa 4: Recuperação de Contexto</button>
                <div class="content">
                    <div class="etapa">
                        <h3>Tabelas Utilizadas como Fonte de Contexto</h3>
                        <div class="json-data">
        """
        
        # Adiciona as tabelas utilizadas como fonte de contexto
        if "tabelas_contexto_fonte" in resultado:
            html_content += html.escape(HTMLFormatter.formatar_json(resultado.get("tabelas_contexto_fonte", [])))
        else:
            html_content += "Nenhuma tabela utilizada como fonte de contexto."
        
        html_content += """
                        </div>
                    </div>
                </div>
                
                <button class="collapsible">Etapa 5: Construção do Prompt Final</button>
                <div class="content">
                    <div class="etapa">
                        <h3>Contexto Utilizado para LLM</h3>
                        <div class="json-data">
        """
        
        # Adiciona o contexto utilizado para LLM
        if "contexto_utilizado_llm" in resultado:
            contexto = resultado.get("contexto_utilizado_llm", "")
            contexto_preview = contexto[:500] + "..." if len(contexto) > 500 else contexto
            html_content += html.escape(contexto_preview)
        else:
            html_content += "Contexto não disponível."
        
        html_content += """
                        </div>
                        
                        <h3>Prompt Final para LLM</h3>
                        <div class="json-data">
        """
        
        # Adiciona o prompt final para LLM
        if "prompt_final_llm" in resultado:
            prompt_final = resultado.get("prompt_final_llm", "")
            prompt_preview = prompt_final[:500] + "..." if len(prompt_final) > 500 else prompt_final
            html_content += html.escape(prompt_preview)
        else:
            html_content += "Prompt final não disponível."
        
        html_content += """
                        </div>
                    </div>
                </div>
                
                <button class="collapsible">Etapa 6: Chamada Final ao LLM para Geração de SQL</button>
                <div class="content">
                    <div class="etapa">
                        <h3>SQL Gerado</h3>
                        <div class="sql-result">
        """
        
        # Adiciona o SQL gerado
        if "sql_gerado" in resultado:
            html_content += html.escape(resultado.get("sql_gerado", ""))
        else:
            html_content += "SQL não disponível."
        
        html_content += """
                        </div>
                        
                        <h3>Dados de Uso da LLM</h3>
                        <div class="json-data">
        """
        
        # Adiciona os dados de uso da LLM
        if "uso_llm_sql_gen" in resultado:
            html_content += html.escape(HTMLFormatter.formatar_json(resultado.get("uso_llm_sql_gen", {})))
        else:
            html_content += "Dados de uso não disponíveis."
        
        html_content += """
                        </div>
                    </div>
                </div>
                
                <h2>Resultado Final</h2>
                <div class="section final-result">
                    <div class="section-header">Prompt do Usuário</div>
                    <div class="prompt-input">
                        {0}
                    </div>
                    
                    <div class="section-header">Dialeto SQL</div>
                    <div class="json-data">
                        {1}
                    </div>
                    
                    <div class="section-header">Tabelas Extraídas do Prompt</div>
                    <div class="json-data">
                        {2}
                    </div>
                    
                    <div class="section-header">SQL Gerado</div>
                    <div class="sql-result">
                        {3}
                    </div>
                    
                    <div class="section-header">Dados de Uso da LLM</div>
                    <div class="json-data">
                        {4}
                    </div>
                </div>
                
                <h2>Log de Saída</h2>
                <button class="collapsible">Ver Log Completo</button>
                <div class="content">
                    <div class="log-output">
                        {5}
                    </div>
                </div>
            </div>
            
            <script>
                var coll = document.getElementsByClassName("collapsible");
                var i;
                
                for (i = 0; i < coll.length; i++) {{
                    coll[i].addEventListener("click", function() {{
                        this.classList.toggle("active");
                        var content = this.nextElementSibling;
                        if (content.style.display === "block") {{
                            content.style.display = "none";
                        }} else {{
                            content.style.display = "block";
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """.format(
            html.escape(prompt_usuario),
            html.escape(resultado.get("dialeto_sql", "")),
            html.escape(HTMLFormatter.formatar_json(resultado.get("tabelas_extraidas_prompt", []))),
            html.escape(resultado.get("sql_gerado", "")),
            html.escape(HTMLFormatter.formatar_json(resultado.get("uso_llm_sql_gen", {}))),
            html.escape(output)
        )
        
        return html_content


def executar_teste_e_gerar_html():
    """Executa o teste do RAGService e gera uma página HTML com os resultados."""
    # Solicita o prompt do usuário
    print("\nDigite o prompt para gerar SQL (ou pressione Enter para usar o prompt padrão):")
    prompt_usuario = input()
    
    # Usa um prompt padrão se o usuário não fornecer um
    if not prompt_usuario:
        prompt_usuario = "Quero uma consulta que mostre os clientes que fizeram mais de 3 pedidos no último mês"
        print(f"Usando prompt padrão: {prompt_usuario}")
    
    # Captura a saída do teste
    output_buffer = StringIO()
    with contextlib.redirect_stdout(output_buffer):
        # Cria uma instância do teste
        teste = TesteRAGService()
        teste.setUp()
        
        # Executa o RAGService
        resultado = {}
        try:
            # Captura a chamada à API de extração
            from src.infrastructure.external_services.llm_service import LLMService
            original_get_api_response = LLMService.get_api_response
            original_get_response_text = LLMService.get_response_text
            
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
            from src.application.services.rag_service import RAGService
            resultado = RAGService.generate_sql_from_prompt(prompt_usuario)
            
            # Adiciona informações extras ao resultado
            resultado["texto_resposta_extracao"] = texto_resposta_extracao
            
        finally:
            # Restaura os métodos originais
            LLMService.get_api_response = original_get_api_response
            LLMService.get_response_text = original_get_response_text
    
    # Obtém a saída capturada
    output = output_buffer.getvalue()
    
    # Gera o HTML
    html_content = HTMLFormatter.gerar_html(prompt_usuario, resultado, output)
    
    # Salva o HTML em um arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        f.write(html_content)
        html_path = f.name
    
    # Abre o arquivo HTML no navegador
    print(f"\nAbrindo resultados no navegador: {html_path}")
    webbrowser.open('file://' + html_path)
    
    return html_path


if __name__ == '__main__':
    html_path = executar_teste_e_gerar_html()
    print(f"Resultados salvos em: {html_path}")
