"""
异常处理模块
定义系统中使用的自定义异常类和异常处理函数
"""
from typing import Dict, Any, Tuple, Optional
from flask import jsonify

class BaseException(Exception):
    """基础异常类"""
    def __init__(self, message: str, code: int = 400, data: Any = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)

class AuthenticationException(BaseException):
    """认证异常"""
    def __init__(self, message: str = "认证失败", code: int = 401, data: Any = None):
        super().__init__(message, code, data)

class AuthorizationException(BaseException):
    """授权异常"""
    def __init__(self, message: str = "权限不足", code: int = 403, data: Any = None):
        super().__init__(message, code, data)

class ValidationException(BaseException):
    """数据验证异常"""
    def __init__(self, message: str = "数据验证失败", code: int = 400, data: Any = None):
        super().__init__(message, code, data)

class ResourceNotFoundException(BaseException):
    """资源不存在异常"""
    def __init__(self, message: str = "请求的资源不存在", code: int = 404, data: Any = None):
        super().__init__(message, code, data)

class BusinessException(BaseException):
    """业务逻辑异常"""
    def __init__(self, message: str = "业务处理失败", code: int = 400, data: Any = None):
        super().__init__(message, code, data)

class DatabaseException(BaseException):
    """数据库操作异常"""
    def __init__(self, message: str = "数据库操作失败", code: int = 500, data: Any = None):
        super().__init__(message, code, data)

class ExternalServiceException(BaseException):
    """外部服务调用异常"""
    def __init__(self, message: str = "外部服务调用失败", code: int = 500, data: Any = None):
        super().__init__(message, code, data)

def create_error_response(
    error: Exception,
    status_code: Optional[int] = None,
    error_code: Optional[int] = None
) -> Tuple[Dict[str, Any], int]:
    """
    创建统一的错误响应
    
    Args:
        error: 异常对象
        status_code: HTTP状态码
        error_code: 业务错误码
    
    Returns:
        (response_dict, status_code)
    """
    if isinstance(error, BaseException):
        response = {
            'code': error_code or error.code,
            'message': str(error.message),
            'data': error.data
        }
        return response, status_code or error.code
    
    # 处理未知异常
    response = {
        'code': error_code or 500,
        'message': str(error),
        'data': None
    }
    return response, status_code or 500

def handle_exception(error: Exception) -> Tuple[Any, int]:
    """
    统一的异常处理函数
    
    Args:
        error: 异常对象
    
    Returns:
        (response, status_code)
    """
    response, status_code = create_error_response(error)
    return jsonify(response), status_code

def create_success_response(data: Any = None, message: str = "操作成功", code: int = 200) -> Dict[str, Any]:
    """
    创建统一的成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        code: 响应代码
    
    Returns:
        统一格式的响应字典
    """
    return {
        'code': code,
        'message': message,
        'data': data
    }

def success_response(data: Any = None, message: str = "操作成功", code: int = 200):
    """
    返回统一格式的成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        code: 响应代码
    
    Returns:
        Flask jsonify响应
    """
    return jsonify(create_success_response(data, message, code)) 