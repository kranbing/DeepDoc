"""
转换器异常类
"""


class ConverterError(Exception):
    """转换器基础异常"""

    pass


class ConverterValidationError(ConverterError):
    """文件验证失败异常"""

    pass


class ConversionTimeoutError(ConverterError):
    """转换超时异常"""

    pass


class ConversionFailedError(ConverterError):
    """转换失败异常"""

    pass


class UnsupportedFormatError(ConverterError):
    """不支持的文件格式异常"""

    pass
