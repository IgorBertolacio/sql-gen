# src/interfaces/api/llm_controller.py
# (Changes highlighted)

from flask import Flask, request, jsonify
from src.application.services.rag_service import RAGService 
from flask_cors import CORS
import os
import logging # Adicionado para log

# Configura logging básico para o app Flask se não configurado
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir requisições do frontend

@app.route('/sql-gen', methods=['POST']) 
def processar_rag_sql_gen(): # Renomeado para clareza 
    """
    Endpoint para processar um prompt de usuário usando o serviço RAG
    para gerar uma consulta SQL.

    Espera um JSON com o seguinte formato:
    {
        "prompt": "Seu prompt aqui"
        // "dialeto": "postgresql" (O dialeto agora está configurado no RAGService, mas poderia ser passado aqui)
    }

    Retorna a consulta SQL gerada e informações do processo RAG.
    """
    logger.info("Recebida requisição em /sql-gen")
    try:
        # Obtém os dados da requisição
        dados = request.json

        if not dados or 'prompt' not in dados:
            logger.warning("Requisição inválida: campo 'prompt' ausente.")
            return jsonify({"erro": "O campo 'prompt' é obrigatório"}), 400

        prompt = dados['prompt']
        # dialect = dados.get('dialeto', 'postgresql') # Opcional: obter dialeto da requisição

        logger.info(f"Processando prompt: '{prompt[:100]}...'")
        # *** CHANGE: Call the new RAGService method ***
        resultado = RAGService.generate_sql_from_prompt(prompt)
        # ********************************************

        # Verifica se houve erro retornado pelo RAGService
        if "erro" in resultado:
             logger.error(f"Erro retornado pelo RAGService: {resultado.get('erro')}")
             # Retornar um status 500 se for erro interno, ou talvez 400/422 se for falha de processamento esperado
             return jsonify(resultado), 500 # Ou outro status apropriado

        # Retorna o resultado completo do RAGService
        logger.info("Processamento concluído com sucesso. Retornando resultado.")
        return jsonify(resultado), 200

    except Exception as e:
        logger.critical(f"Erro inesperado no endpoint /sql-gen: {str(e)}", exc_info=True)
        return jsonify({"erro": f"Erro interno no servidor ao processar o prompt: {str(e)}"}), 500

# Função para iniciar o servidor (sem alterações)
def iniciar_servidor(host='0.0.0.0', porta=5000, modo_debug=False):
    """
    Inicia o servidor Flask.
    """
    logger.info(f"Iniciando servidor Flask em {host}:{porta} (Debug: {modo_debug})")
    app.run(host=host, port=porta, debug=modo_debug)

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    # Use logger.info em vez de print
    logger.info(f"Script principal iniciando servidor na porta {porta}")
    iniciar_servidor(porta=porta, modo_debug=True) # Mantenha debug=True para desenvolvimento