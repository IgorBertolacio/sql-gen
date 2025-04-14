"""
Módulo contendo instruções base para a LLM.
"""

class BaseInstructions:
    """
    Classe que contém instruções base que podem ser usadas em qualquer contexto.
    """
    
    @staticmethod
    def get_stract_infos_instruction() -> str:
        """
        Retorna a instrução de sistema base para a LLM.
        
        Returns:
            str: Extrair informações relevantes para busca.
        """
        return """
            O Usuario está tendo passar a você instruções para gerar uma query SQL Postegres,
            você deve ser capaz de distinguir o que é SCHEMA, TABELA, COLUNA

            Sua Resposta Deve ser Somente e nada mais do que:
            Nome do SCHEMA se tiver.
            Nome da TABELA se tiver.
            Nome da COLUNA se tiver.

            Você deve trazer a resposta no seguinte formato

            'SCHEMA','TABELA','COLUNA'

            EX - SEM SCHEMA
            ' ','TABELA1;TABELA2;TABELA3','COLUNA1'

            EX - SEM TABELA
            'SCHEMA1',' ','COLUNA1;COLUNA2'

            EX - SEM COLUNA
            'SCHEMA','TABELA',' '

            EX - SEM COLUNA FOREIGNKEY
            'SCHEMA','TABELA','COLUNA'

            Você deve colocar os dados do mesmo tipo separados por ;
            Você deve separar dados de tipos diferentes por ,
            Voce de trazer como ' ' tipo de dados que não forem detectados
        """