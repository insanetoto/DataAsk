#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
License授权中间件
提供API接口的License验证功能
"""

import os
import logging
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime
from typing import Dict, Any, Optional

# 导入License管理器
from license_manager import LicenseManager, LicenseStorage

logger = logging.getLogger(__name__)


class LicenseMiddleware:
    """License验证中间件"""
    
    def __init__(self, app=None, license_file: str = "license.key", enabled: bool = True):
        """
        初始化License中间件
        
        Args:
            app: Flask应用实例
            license_file: License文件路径
            enabled: 是否启用license校验
        """
        self.license_manager = LicenseManager()
        self.license_storage = LicenseStorage(license_file)
        self.current_license = None
        self.license_info = None
        self.enabled = enabled  # license校验开关
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
        
        # 在每个请求前验证License
        @app.before_request
        def check_license():
            # 如果license校验被禁用，直接通过
            if not self.enabled:
                g.license_info = {"status": "disabled", "message": "License校验已禁用"}
                g.license_valid = True
                return
            
            # 跳过静态文件和非API路径
            if (request.path.startswith('/static/') or 
                request.path == '/' or 
                request.path == '/favicon.ico' or
                request.path.startswith('/api/v1/license')):
                return
            
            # 验证License
            result = self.verify_current_license()
            if not result['valid']:
                return jsonify({
                    "error": "License验证失败",
                    "message": result['error'],
                    "code": "LICENSE_ERROR",
                    "timestamp": datetime.now().isoformat()
                }), 403
            
            # 将License信息存储到g对象中
            g.license_info = result['data']
            g.license_valid = True
    
    def verify_current_license(self) -> Dict[str, Any]:
        """验证当前License"""
        try:
            # 从文件加载License
            license_str = self.license_storage.load_license()
            if not license_str:
                return {
                    "valid": False,
                    "error": "未找到License文件，请联系管理员获取授权"
                }
            
            # 验证License
            result = self.license_manager.verify_license(license_str)
            
            # 缓存验证结果
            if result['valid']:
                self.current_license = license_str
                self.license_info = result['data']
                
                # 如果License即将过期（少于7天），记录警告
                if result.get('days_remaining', 0) <= 7:
                    logger.warning(f"License即将过期！剩余 {result['days_remaining']} 天")
            
            return result
            
        except Exception as e:
            logger.error(f"License验证异常: {e}")
            return {
                "valid": False,
                "error": f"License验证异常: {str(e)}"
            }
    
    def get_license_status(self) -> Dict[str, Any]:
        """获取License状态"""
        # 如果license校验被禁用
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "License校验已禁用（开发环境）",
                "enabled": False
            }
        
        result = self.verify_current_license()
        
        if result['valid']:
            return {
                "status": "valid",
                "organization": result['data']['organization'],
                "expire_date": result['expire_date'],
                "days_remaining": result['days_remaining'],
                "features": result['data']['features'],
                "max_users": result['data'].get('max_users', 'N/A'),
                "enabled": True
            }
        else:
            return {
                "status": "invalid",
                "error": result['error'],
                "enabled": True
            }


def require_license(feature: Optional[str] = None):
    """
    License验证装饰器
    
    Args:
        feature: 需要检查的特定功能
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果license校验被禁用，直接通过
            if hasattr(g, 'license_info') and g.license_info.get('status') == 'disabled':
                return f(*args, **kwargs)
            
            # 检查License是否有效
            if not hasattr(g, 'license_valid') or not g.license_valid:
                return jsonify({
                    "error": "无效的License",
                    "message": "请联系管理员获取有效的License授权",
                    "code": "LICENSE_INVALID",
                    "timestamp": datetime.now().isoformat()
                }), 403
            
            # 检查特定功能是否启用
            if feature and hasattr(g, 'license_info'):
                features = g.license_info.get('features', {})
                if not features.get(feature, False):
                    return jsonify({
                        "error": "功能未授权",
                        "message": f"当前License未授权使用 '{feature}' 功能",
                        "code": "FEATURE_NOT_AUTHORIZED",
                        "timestamp": datetime.now().isoformat()
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_feature_permission(feature: str) -> bool:
    """
    检查功能权限
    
    Args:
        feature: 功能名称
        
    Returns:
        是否有权限
    """
    # 如果license校验被禁用，所有功能都可用
    if hasattr(g, 'license_info') and g.license_info.get('status') == 'disabled':
        return True
    
    if not hasattr(g, 'license_info') or not g.license_info:
        return False
    
    features = g.license_info.get('features', {})
    return features.get(feature, False)


def get_current_license_info() -> Optional[Dict[str, Any]]:
    """获取当前License信息"""
    return getattr(g, 'license_info', None)


def create_license_routes(app, middleware: LicenseMiddleware):
    """创建License管理相关的路由"""
    
    @app.route('/api/v1/license/status', methods=['GET'])
    def license_status():
        """获取License状态"""
        status = middleware.get_license_status()
        return jsonify(status)
    
    @app.route('/api/v1/license/upload', methods=['POST'])
    def upload_license():
        """上传License"""
        try:
            data = request.get_json()
            if not data or 'license' not in data:
                return jsonify({
                    "error": "请求参数错误",
                    "message": "缺少license字段"
                }), 400
            
            license_str = data['license'].strip()
            
            # 验证License
            result = middleware.license_manager.verify_license(license_str)
            if not result['valid']:
                return jsonify({
                    "error": "License无效",
                    "message": result['error']
                }), 400
            
            # 保存License
            if middleware.license_storage.save_license(license_str):
                return jsonify({
                    "message": "License上传成功",
                    "organization": result['data']['organization'],
                    "expire_date": result['expire_date'],
                    "days_remaining": result['days_remaining']
                })
            else:
                return jsonify({
                    "error": "License保存失败",
                    "message": "无法保存License文件"
                }), 500
                
        except Exception as e:
            logger.error(f"License上传失败: {e}")
            return jsonify({
                "error": "License上传失败",
                "message": str(e)
            }), 500
    
    @app.route('/api/v1/license/info', methods=['GET'])
    def license_info():
        """获取License详细信息"""
        try:
            license_str = middleware.license_storage.load_license()
            if not license_str:
                return jsonify({
                    "error": "未找到License",
                    "message": "请先上传License文件"
                }), 404
            
            info = middleware.license_manager.get_license_info(license_str)
            if info:
                # 验证License状态
                result = middleware.license_manager.verify_license(license_str)
                
                return jsonify({
                    "organization": info['organization'],
                    "product": info['product'],
                    "issue_date": info['issue_date'],
                    "expire_date": info['expire_date'],
                    "max_users": info.get('max_users', 'N/A'),
                    "features": info['features'],
                    "license_version": info.get('license_version', '1.0'),
                    "valid": result['valid'],
                    "days_remaining": result.get('days_remaining', 0) if result['valid'] else 0,
                    "error": result.get('error')
                })
            else:
                return jsonify({
                    "error": "License解析失败",
                    "message": "无法解析License文件"
                }), 400
                
        except Exception as e:
            logger.error(f"获取License信息失败: {e}")
            return jsonify({
                "error": "获取License信息失败",
                "message": str(e)
            }), 500
    
    @app.route('/api/v1/license/delete', methods=['DELETE'])
    def delete_license():
        """删除License"""
        try:
            if middleware.license_storage.delete_license():
                return jsonify({
                    "message": "License删除成功"
                })
            else:
                return jsonify({
                    "error": "License删除失败"
                }), 500
        except Exception as e:
            logger.error(f"License删除失败: {e}")
            return jsonify({
                "error": "License删除失败",
                "message": str(e)
            }), 500 