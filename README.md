sql-generate/
│
├── src/                                                     # Código fonte
│   ├── domain/                                              # Regras de negócio do domínio
│   │   ├── entities/                                        # Objetos de negócio
│   │   │   └── __init__.py
│   │   ├── value_objects/                                   # Objetos de valor (imutáveis com igualdade)
│   │   │   └── __init__.py
│   │   ├── exceptions/                                      # Exceções específicas do domínio
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── application/                                         # Regras de negócio da aplicação
│   │   ├── interfaces/                                      # Interfaces abstratas
│   │   │   └── __init__.py
│   │   ├── use_cases/                                       # Regras de negócio específicas da aplicação (Casos de Uso)
│   │   │   └── __init__.py                                  # Serviços que orquestram casos de uso
│   │   ├── services/
│   │   │   ├─ rag_service.py                                # Maestro da RAG                            
│   │   │   └── __init__.py
│   │   ├── dto/                                             # Objetos de Transferência de Dados (Data Transfer Objects)
│   │   │   └── __init__.py
│   │   ├── utils
│   │   │   └── llm_response_parser.py                       # Parsear resposta da LLM
│   │   └── __init__.py
│   │
│   │
│   ├── infrastructure/                                      # Frameworks, drivers e ferramentas
│   │   ├── repositories/                                    # Implementações de acesso a dados (Repositórios)
│   │   │   └── __init__.py
│   │   ├── persistence/                                     # Código relacionado à persistência (ex: banco de dados)
│   │   │   ├── index_loader.py                              # Carregamento do banco de dados        
│   │   │   └── __init__.py
│   │   ├── external_services/                               # Clientes de serviços externos APIs
│   │   │   ├─ embedding_service.py                          # Serviço para fazer embedding do prompt       
│   │   │   ├─ llm_service.py                                # Serviço para interagir com a LLM
│   │   │   └── __init__.py
│   │   ├── config/                                          # Configuração
│   │   │   ├── api
│   │   │   │   ├─ api_config.py                             # Configuração da API
│   │   │   │   └─ __init__.py
│   │   │   ├── prompts
│   │   │   │    ├─ base_instructions.py                     # Instruções para a entrada             
│   │   │   │    ├─ sql_instructions.py                      # Instruções para a saida
│   │   │   │    └─ __init__.py
│   │   │   │  
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── interfaces/                                          # Adaptadores de interface (entrada/saída)
│   │   ├── api/                                             # Controladores/rotas da API
│   │   │   ├── llm_controller.py                            # Controle para API REST com o LLM
│   │   │   ├── run_api.py                                   # Iniciar o Servidor API     
│   │   │   └── __init__.py
│   │   ├── cli/                                             # Interfaces de linha de comando
│   │   │   └── __init__.py
│   │   ├── presenters/                                      # Formata dados para apresentação
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── docs/                                                    # Documentação
│   ├── architecture/                                        # Documentação da arquitetura
│   └── api/                                                 # Documentação da API
│
├── scripts/                                                 # Scripts utilitários (build, deploy, etc.)
│   └── __init__.py
│
├── .gitignore                                               # Arquivo para ignorar arquivos no Git
├── requirements.txt                                         # Dependências do projeto
├── requirements-dev.txt                                     # Dependências de desenvolvimento
├── setup.py                                                 # Arquivo de configuração do pacote (setuptools)
├── pyproject.toml                                           # Configuração do projeto Python (PEP 518)
└── README.md                                                # Documentação principal do projeto