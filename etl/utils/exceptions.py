"""Exception classes for ETL pipeline"""


class ETLException(Exception):
    """Base exception for ETL pipeline"""
    pass


class ExtractionException(ETLException):
    """Exception raised during data extraction"""
    pass


class TransformationException(ETLException):
    """Exception raised during data transformation"""
    pass


class LoadException(ETLException):
    """Exception raised during data loading"""
    pass


class ConfigurationException(ETLException):
    """Exception raised for configuration errors"""
    pass


class ConnectionException(ETLException):
    """Exception raised for connection errors"""
    pass
