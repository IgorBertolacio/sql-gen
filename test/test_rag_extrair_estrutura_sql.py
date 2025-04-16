import requests

def test_extrair_estrutura_sql():
    url = "http://localhost:5000/sql-gen"
    prompt = "Quero saber o nome e o salário de todos os funcionários da tabela empregados do schema publico"
    response = requests.post(url, json={"prompt": prompt})
    assert response.status_code == 200

    data = response.json()
    print("Resposta completa:", data)
    print("Schemas:", data.get("schemas"))
    print("Tabelas:", data.get("tabelas"))
    print("Colunas:", data.get("colunas"))

    assert isinstance(data.get("schemas"), list)
    assert isinstance(data.get("tabelas"), list)
    assert isinstance(data.get("colunas"), list)