#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Logs Elegante
------------------------
Uma biblioteca de logging em Python com formatação colorida,
configuração simplificada e estrutura modular.

Autor: Claude
Data: 2025-05-06
"""

import logging
import sys
import os
from typing import Dict, Optional, Union, List, TextIO
from datetime import datetime


class AnsiColors:
    """Códigos ANSI para cores no terminal."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Cores de texto
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[90m"
    
    # Cores intensas
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    @staticmethod
    def is_terminal() -> bool:
        """Verifica se a saída está conectada a um terminal que suporta cores."""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


class ColoredFormatter(logging.Formatter):
    """
    Formatador sofisticado que aplica cores e estilos apropriados aos logs.
    
    Características:
        - Formatação colorida por nível de log
        - Opções de layout flexíveis
        - Destaque para componentes importantes
    """
    # Estilos de formatação por nível de log
    DEFAULT_STYLES = {
        logging.DEBUG: {
            "color": AnsiColors.BLUE,
            "level_prefix": "DEBUG",
            "bold_level": False
        },
        logging.INFO: {
            "color": AnsiColors.GREEN,
            "level_prefix": "INFO",
            "bold_level": False
        },
        logging.WARNING: {
            "color": AnsiColors.YELLOW,
            "level_prefix": "WARN",
            "bold_level": True
        },
        logging.ERROR: {
            "color": AnsiColors.RED,
            "level_prefix": "ERROR",
            "bold_level": True
        },
        logging.CRITICAL: {
            "color": AnsiColors.BRIGHT_RED,
            "level_prefix": "CRIT",
            "bold_level": True
        }
    }
    
    def __init__(self, 
                 fmt: Optional[str] = None,
                 datefmt: Optional[str] = None,
                 use_colors: bool = True,
                 styles: Optional[Dict] = None):
        """
        Inicializa o formatador colorido.
        
        Args:
            fmt: String de formatação personalizada (opcional)
            datefmt: Formato da data/hora (opcional)
            use_colors: Se deve usar cores ou não
            styles: Dicionário de estilos para sobrescrever os padrões
        """
        if fmt is None:
            fmt = "[%(asctime)s] %(levelname)-5s | %(name)s:%(lineno)d | %(message)s"
            
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"
            
        super().__init__(fmt=fmt, datefmt=datefmt)
        
        # Desativa cores se não estiver em um terminal
        self.use_colors = use_colors and AnsiColors.is_terminal()
        
        # Combina estilos padrão com personalizados
        self.styles = self.DEFAULT_STYLES.copy()
        if styles:
            for level, style in styles.items():
                if level in self.styles:
                    self.styles[level].update(style)
                else:
                    self.styles[level] = style

    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro com estilo apropriado.
        
        Args:
            record: O registro de log a ser formatado
        
        Returns:
            Mensagem de log formatada
        """
        # Cria uma cópia do registro para não modificar o original
        formatted_record = logging.makeLogRecord(record.__dict__)
        
        # Verificação de segurança para mensagens com formatação especial
        try:
            # Tenta verificar se há um problema de formatação
            original_message = formatted_record.getMessage()
        except TypeError:
            # Se falhar, é porque há um problema com a formatação
            # Verificamos se os args existem e são uma tupla
            if hasattr(formatted_record, 'args') and isinstance(formatted_record.args, tuple):
                # Corrige a mensagem pré-formatando
                if isinstance(formatted_record.msg, str) and '%' in formatted_record.msg:
                    try:
                        formatted_record.msg = formatted_record.msg % formatted_record.args
                        formatted_record.args = ()
                    except (TypeError, ValueError):
                        # Se a formatação falhar, concatenamos os argumentos à mensagem
                        formatted_record.msg = f"{formatted_record.msg} (args: {formatted_record.args})"
                        formatted_record.args = ()
        
        # Aplica estilos se habilitado
        if self.use_colors and record.levelno in self.styles:
            style = self.styles[record.levelno]
            color = style.get("color", "")
            
            # Personaliza o nome do nível
            if "level_prefix" in style:
                formatted_record.levelname = style["level_prefix"]
            
            # Aplica negrito ao nível se configurado
            if style.get("bold_level", False):
                formatted_record.levelname = f"{AnsiColors.BOLD}{formatted_record.levelname}{AnsiColors.RESET}{color}"
            
            # Formata a mensagem com cores
            try:
                original_message = formatted_record.getMessage()
                formatted_record.msg = f"{color}{original_message}{AnsiColors.RESET}"
                formatted_record.args = ()
            except (TypeError, ValueError):
                # Último recurso para garantir que não falhe
                formatted_record.msg = f"{color}{str(formatted_record.msg)}{AnsiColors.RESET}"
                formatted_record.args = ()
            
        return super().format(formatted_record)


class LogManager:
    """
    Gerenciador central de logs que configura e controla o sistema de logging.
    
    Permite configurar facilmente:
    - Saída para console
    - Saída para arquivos de log
    - Níveis de log diferentes por módulo
    - Rotação de arquivos de log
    - Perfis de configuração predefinidos
    """
    # Nível de log padrão para o sistema
    DEFAULT_LEVEL = logging.INFO
    
    # Correspondência de strings de nível para constantes do módulo logging
    LEVEL_MAP = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
        "crit": logging.CRITICAL
    }
    
    # Perfis de configuração predefinidos
    PROFILES = {
        "development": {
            "level": "debug",
            "console": True,
            "log_file": "logs/development.log",
            "use_colors": True,
            "format_string": "[%(asctime)s] %(levelname)-5s | %(name)s:%(lineno)d | %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S"
        },
        "production": {
            "level": "info",
            "console": True,
            "log_file": "logs/production.log",
            "use_colors": True,
            "format_string": "[%(asctime)s] %(levelname)-5s | %(name)s | %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S"
        },
        "minimal": {
            "level": "info",
            "console": True,
            "log_file": None,
            "use_colors": True,
            "format_string": "%(levelname)-5s | %(message)s",
            "date_format": None
        },
        "api_server": {
            "level": "info",
            "console": True,
            "log_file": "logs/api.log",
            "use_colors": True,
            "format_string": "[%(asctime)s] %(levelname)-5s | %(name)s | %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "module_levels": {
                "werkzeug": "warning",
                "urllib3": "warning",
                "sqlalchemy.engine": "warning"
            }
        }
    }
    
    def __init__(self):
        """Inicializa o gerenciador de logs."""
        # Flag para verificar se a configuração já foi aplicada
        self.configured = False
        
        # Armazena handlers configurados
        self.handlers = {}
        
        # Cache de loggers por módulo
        self._logger_cache = {}
        
        # Perfil atual
        self.current_profile = None

    def setup(self,
              level: Union[str, int] = DEFAULT_LEVEL,
              console: bool = True,
              log_file: Optional[str] = None,
              module_levels: Optional[Dict[str, Union[str, int]]] = None,
              format_string: Optional[str] = None,
              date_format: Optional[str] = None,
              use_colors: bool = True,
              profile: Optional[str] = None) -> None:
        """
        Configura o sistema de logging.
        
        Args:
            level: Nível de log global (pode ser string ou constante de logging)
            console: Se deve habilitar o log no console
            log_file: Caminho do arquivo de log (opcional)
            module_levels: Dicionário com níveis específicos por módulo
            format_string: String de formatação personalizada
            date_format: Formato da data/hora
            use_colors: Se deve usar cores nos logs
            profile: Nome de um perfil predefinido (sobrescreve outros parâmetros)
        """
        # Se um perfil foi especificado, usa suas configurações
        if profile:
            if profile in self.PROFILES:
                self.current_profile = profile
                profile_config = self.PROFILES[profile].copy()
                
                # Aplica configurações do perfil
                level = profile_config.pop("level", level)
                console = profile_config.pop("console", console)
                log_file = profile_config.pop("log_file", log_file)
                module_levels = profile_config.pop("module_levels", module_levels)
                format_string = profile_config.pop("format_string", format_string)
                date_format = profile_config.pop("date_format", date_format)
                use_colors = profile_config.pop("use_colors", use_colors)
                
                # Log de confirmação
                logging.getLogger(__name__).info(f"Usando perfil de log: {profile}")
            else:
                valid_profiles = ", ".join(self.PROFILES.keys())
                logging.getLogger(__name__).warning(
                    f"Perfil de log '{profile}' não encontrado. Perfis válidos: {valid_profiles}"
                )
        
        # Converte nível de string para constante, se necessário
        if isinstance(level, str):
            level = self._parse_level(level)
        
        # Configura o root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove handlers existentes para evitar duplicação
        self._clean_handlers(root_logger)
        
        # Adiciona handler para o console se solicitado
        if console:
            self._setup_console_handler(format_string, date_format, use_colors)
        
        # Adiciona handler para arquivo se especificado
        if log_file:
            self._setup_file_handler(log_file, format_string, date_format)
        
        # Configura níveis específicos por módulo
        if module_levels:
            for module_name, module_level in module_levels.items():
                self.set_module_level(module_name, module_level)
        
        # Marca como configurado
        self.configured = True
        
        # Log de confirmação
        logging.getLogger(__name__).info(f"Sistema de logs inicializado com nível global: {logging.getLevelName(level)}")

    def _parse_level(self, level_name: str) -> int:
        """
        Converte um nome de nível em um valor inteiro.
        
        Args:
            level_name: Nome do nível de log (case insensitive)
            
        Returns:
            Constante inteira do nível de log
            
        Raises:
            ValueError: Se o nível for inválido
        """
        level_name = level_name.lower()
        if level_name in self.LEVEL_MAP:
            return self.LEVEL_MAP[level_name]
        
        try:
            return int(level_name)
        except ValueError:
            valid_levels = ", ".join(self.LEVEL_MAP.keys())
            raise ValueError(f"Nível de log inválido: '{level_name}'. Níveis válidos: {valid_levels}")

    def _clean_handlers(self, logger: logging.Logger) -> None:
        """
        Remove handlers existentes de um logger.
        
        Args:
            logger: Logger a ser limpo
        """
        if logger.hasHandlers():
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

    def _setup_console_handler(self, 
                              format_string: Optional[str], 
                              date_format: Optional[str],
                              use_colors: bool) -> None:
        """
        Configura o handler para saída no console.
        
        Args:
            format_string: String de formatação personalizada
            date_format: Formato da data/hora
            use_colors: Se deve usar cores
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(fmt=format_string, 
                                                     datefmt=date_format,
                                                     use_colors=use_colors))
        
        logging.getLogger().addHandler(console_handler)
        self.handlers['console'] = console_handler

    def _setup_file_handler(self, 
                           log_file: str, 
                           format_string: Optional[str],
                           date_format: Optional[str]) -> None:
        """
        Configura o handler para saída em arquivo.
        
        Args:
            log_file: Caminho do arquivo de log
            format_string: String de formatação personalizada
            date_format: Formato da data/hora
        """
        # Garante que o diretório existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Cria handler para arquivo com formatador padrão (sem cores)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(ColoredFormatter(fmt=format_string, 
                                                  datefmt=date_format,
                                                  use_colors=False))
        
        logging.getLogger().addHandler(file_handler)
        self.handlers['file'] = file_handler

    def set_module_level(self, module_name: str, level: Union[str, int]) -> None:
        """
        Define o nível de log para um módulo específico.
        
        Args:
            module_name: Nome do módulo
            level: Nível de log (string ou constante)
        """
        if isinstance(level, str):
            level = self._parse_level(level)
            
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(level)
        
        # Atualiza cache
        self._logger_cache[module_name] = module_logger
        
        # Log de confirmação se o sistema já estiver configurado
        if self.configured:
            logging.getLogger(__name__).debug(
                f"Nível do módulo '{module_name}' definido para {logging.getLevelName(level)}"
            )

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Obtém um logger configurado.
        
        Args:
            name: Nome do logger (geralmente __name__ do módulo)
            
        Returns:
            Logger configurado
        """
        # Configura o sistema de log se ainda não estiver configurado
        if not self.configured:
            self.setup()
            
        # Usa o nome do módulo chamador se não for especificado
        if name is None:
            import inspect
            frame = inspect.currentframe().f_back
            name = frame.f_globals.get('__name__')
            
        # Retorna do cache se disponível
        if name in self._logger_cache:
            return self._logger_cache[name]
            
        # Obtém o logger e atualiza o cache
        logger = logging.getLogger(name)
        self._logger_cache[name] = logger
        return logger


# Instância global do gerenciador de logs
log_manager = LogManager()


# Funções de conveniência para API simples
def setup_logging(profile: str = "api_server", **kwargs):
    """
    Configura o sistema de logs com os parâmetros fornecidos.
    
    Args:
        profile: Nome do perfil predefinido a ser usado
        **kwargs: Parâmetros para sobrescrever configurações do perfil
    """
    log_manager.setup(profile=profile, **kwargs)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtém um logger configurado.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        
    Returns:
        Logger configurado
    """
    return log_manager.get_logger(name)


# Exemplo de uso
if __name__ == "__main__":
    # Configuração básica usando perfil
    setup_logging(profile="development")
    
    # Obtém loggers para diferentes módulos
    logger = get_logger(__name__)
    db_logger = get_logger("app.database")
    
    # Define níveis específicos
    log_manager.set_module_level("app.database", "debug")
    
    # Demonstração dos níveis de log
    logger.debug("Esta é uma mensagem de depuração")
    logger.info("Esta é uma mensagem informativa")
    logger.warning("Esta é uma mensagem de aviso")
    logger.error("Esta é uma mensagem de erro")
    logger.critical("Esta é uma mensagem crítica")
    
    # Log de outro módulo com nível diferente
    db_logger.debug("Mensagem de depuração do banco de dados - será exibida devido ao nível personalizado")