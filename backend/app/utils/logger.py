import logging

def get_logger(name: str = "claims_copilot") -> logging.Logger:
    """
    Utility helper to retrieve named loggers across services and skills.
    """
    return logging.getLogger(name)
