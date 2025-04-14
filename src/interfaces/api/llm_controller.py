"""
Controlador para a API REST que gerencia interações com o serviço RAG para geração de SQL.
"""
from flask import Flask, request, jsonify
from src.infrastructure.config.prompts.sql_instructions import SQLInstructions
from src.application.services.rag_service import RAGService
from flask_cors import CORS
import os

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir requisições do frontend

@app.route('/sql-gen', methods=['POST'])
def processar_rag ():
    """
    Endpoint para processar um prompt usando o serviço RAG.
    
    Espera um JSON com o seguinte formato:
    {
        "prompt": "Seu prompt aqui",
        "dialeto": "postgresql"
    }
    
    Retorna a resposta processada pelo RAG.
    """
    try:
        # Obtém os dados da requisição
        dados = request.json
        
        if not dados or 'prompt' not in dados:
            return jsonify({"erro": "O campo 'prompt' é obrigatório"}), 400
        
        prompt = dados['prompt']

        # Processa o prompt usando o serviço RAG
        resultado = RAGService.extrair_estrutura_sql(prompt)
        
        # Retorna o resultado
        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar o prompt: {str(e)}"}), 500

# Função para iniciar o servidor
def iniciar_servidor(host='0.0.0.0', porta=5000, modo_debug=False):
    """
    Inicia o servidor Flask.
    
    Args:
        host: O host em que o servidor será executado. Padrão é '0.0.0.0' (todas as interfaces).
        porta: A porta em que o servidor será executado. Padrão é 5000.
        modo_debug: Se True, habilita o modo de depuração. Padrão é False.
    """
    app.run(host=host, port=porta, debug=modo_debug)

if __name__ == "__main__":
    # Obtém a porta do ambiente ou usa 5000 como padrão
    porta = int(os.environ.get("PORT", 5000))
    
    # Inicia o servidor
    iniciar_servidor(porta=porta, modo_debug=True)
    
    print(f"Servidor iniciado na porta {porta}")