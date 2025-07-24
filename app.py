# -*- coding: utf-8 -*-
"""
百惟数问 - 智能数据问答平台
基于Vanna AI框架、MySQL、Redis构建的企业级数据分析平台
"""
import os
import logging
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from config.base_config import config
from tools.database import init_database_service
from tools.redis_service import get_redis_service
from AIEngine.vanna_service import init_vanna_service
from service.organization_service import get_organization_service_instance
from service.user_service import get_user_service_instance
from api.routes import api_bp
from api.text2sql_routes import text2sql_bp

from datetime import datetime

# License授权系统导入
from tools.license_middleware import LicenseMiddleware, require_license, create_license_routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """创建Flask应用工厂函数"""
    app = Flask(__name__)
    
    # 启用CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 获取配置类并创建实例
    config_class = config[config_name]
    config_instance = config_class()
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 初始化License中间件（根据环境配置决定是否启用）
    license_enabled = config_instance.LICENSE_ENABLED
    license_middleware = LicenseMiddleware(
        license_file="license.key", 
        enabled=license_enabled
    )
    license_middleware.init_app(app)
    
    # 记录License状态
    if license_enabled:
        logger.info("License校验已启用（生产环境模式）")
    else:
        logger.info("License校验已禁用（开发环境模式）")
    
    # 创建License管理路由
    create_license_routes(app, license_middleware)
    
    # 初始化各项服务 - 传递配置实例
    init_services(config_instance)
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    app.register_blueprint(text2sql_bp)

    
    # 注册路由
    register_routes(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    logger.info("百惟数问应用初始化完成")
    return app

def init_services(config_obj):
    """初始化各项服务"""
    try:
        # 初始化数据库服务
        logger.info("正在初始化数据库服务...")
        init_database_service(config_obj)
        logger.info("数据库服务初始化成功")
        
        # 初始化Redis服务
        logger.info("正在初始化Redis服务...")
        redis_service = get_redis_service()
        if redis_service.test_connection():
            logger.info("Redis服务初始化成功")
        else:
            logger.error("Redis服务连接失败")
            raise Exception("Redis服务连接失败")
        
        # 初始化Vanna AI服务
        logger.info("正在初始化Vanna AI服务...")
        init_vanna_service(config_obj)
        logger.info("Vanna AI服务初始化成功")
        
        # 初始化机构管理服务
        logger.info("正在初始化机构管理服务...")
        get_organization_service_instance()
        logger.info("机构管理服务初始化成功")
        
        # 初始化用户服务
        logger.info("正在初始化用户服务...")
        get_user_service_instance()
        logger.info("用户服务初始化成功")
        
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        raise

def register_routes(app):
    """注册路由"""
    
    @app.route('/')
    def index():
        """API文档主页"""
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>百惟数问 API 文档</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f8f9fa;
                    color: #333;
                    line-height: 1.6;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 0;
                    text-align: center;
                    margin-bottom: 30px;
                    border-radius: 12px;
                }
                
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                
                .header p {
                    font-size: 1.2em;
                    opacity: 0.9;
                }
                
                .status-info {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .status-card {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    border-left: 4px solid #28a745;
                }
                
                .status-card.warning {
                    border-left-color: #ffc107;
                }
                
                .status-card.danger {
                    border-left-color: #dc3545;
                }
                
                .status-card h3 {
                    color: #2c3e50;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .status-badge {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                    font-weight: bold;
                    color: white;
                }
                
                .badge-success { background: #28a745; }
                .badge-warning { background: #ffc107; }
                .badge-danger { background: #dc3545; }
                
                .api-section {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                    margin-bottom: 30px;
                }
                
                .api-section-header {
                    background: #2c3e50;
                    color: white;
                    padding: 20px;
                    font-size: 1.3em;
                    font-weight: bold;
                }
                
                .api-endpoint {
                    border-bottom: 1px solid #eee;
                    padding: 20px;
                    transition: background-color 0.2s;
                }
                
                .api-endpoint:hover {
                    background-color: #f8f9fa;
                }
                
                .api-endpoint:last-child {
                    border-bottom: none;
                }
                
                .endpoint-header {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 10px;
                }
                
                .method-badge {
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-size: 0.8em;
                    font-weight: bold;
                    color: white;
                    min-width: 60px;
                    text-align: center;
                }
                
                .method-get { background: #28a745; }
                .method-post { background: #007bff; }
                .method-put { background: #ffc107; color: #333; }
                .method-delete { background: #dc3545; }
                
                .endpoint-path {
                    font-family: 'Monaco', 'Menlo', monospace;
                    font-size: 1.1em;
                    color: #2c3e50;
                    font-weight: 500;
                }
                
                .endpoint-description {
                    color: #666;
                    margin-bottom: 15px;
                }
                
                .endpoint-example {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 10px;
                }
                
                .endpoint-example h5 {
                    margin-bottom: 10px;
                    color: #495057;
                }
                
                .code-block {
                    background: #2d3748;
                    color: #e2e8f0;
                    padding: 15px;
                    border-radius: 6px;
                    font-family: 'Monaco', 'Menlo', monospace;
                    font-size: 0.9em;
                    overflow-x: auto;
                    white-space: pre;
                }
                
                .footer {
                    text-align: center;
                    color: #666;
                    margin-top: 40px;
                    padding: 20px;
                    border-top: 1px solid #dee2e6;
                }
                
                .try-button {
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9em;
                    margin-left: 10px;
                    transition: background-color 0.2s;
                }
                
                .try-button:hover {
                    background: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>百惟数问 API 文档</h1>
                    <p>基于AI的企业级智能数据问答平台</p>
                </div>
                
                <div class="status-info">
                    <div class="status-card">
                        <h3>🏥 服务状态 <span class="status-badge badge-success">运行中</span></h3>
                        <p>所有核心服务正常运行</p>
                    </div>
                    <div class="status-card">
                        <h3>🤖 AI模型 <span class="status-badge badge-success">qwen-turbo</span></h3>
                        <p>阿里云百炼平台</p>
                    </div>
                    <div class="status-card">
                        <h3>💾 数据库 <span class="status-badge badge-success">MySQL</span></h3>
                        <p>连接正常，支持多表查询</p>
                    </div>
                    <div class="status-card">
                        <h3>🚀 缓存 <span class="status-badge badge-success">Redis</span></h3>
                        <p>智能缓存，提升响应速度</p>
                    </div>
                </div>
                
                <div class="api-section">
                    <div class="api-section-header">📊 智能问答接口</div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-post">POST</span>
                            <span class="endpoint-path">/api/v1/ask</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/ask', 'POST')">试用</button>
                        </div>
                        <div class="endpoint-description">智能问答：输入自然语言问题，自动生成SQL并执行查询</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl -X POST http://localhost:8080/api/v1/ask \\
  -H "Content-Type: application/json" \\
  -d '{"question": "查询客户总数"}'</div>
                        </div>
                    </div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-post">POST</span>
                            <span class="endpoint-path">/api/v1/generate_sql</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/generate_sql', 'POST')">试用</button>
                        </div>
                        <div class="endpoint-description">生成SQL：根据自然语言问题生成对应的SQL语句</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl -X POST http://localhost:8080/api/v1/generate_sql \\
  -H "Content-Type: application/json" \\
  -d '{"question": "查询所有客户信息"}'</div>
                        </div>
                    </div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-post">POST</span>
                            <span class="endpoint-path">/api/v1/execute_sql</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/execute_sql', 'POST')">试用</button>
                        </div>
                        <div class="endpoint-description">执行SQL：直接执行提供的SQL语句</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl -X POST http://localhost:8080/api/v1/execute_sql \\
  -H "Content-Type: application/json" \\
  -d '{"sql": "SELECT COUNT(*) FROM customerinfo"}'</div>
                        </div>
                    </div>
                </div>
                
                <div class="api-section">
                    <div class="api-section-header">🎓 模型训练接口</div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-post">POST</span>
                            <span class="endpoint-path">/api/v1/train</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/train', 'POST')">试用</button>
                        </div>
                        <div class="endpoint-description">训练模型：使用问题-SQL对训练AI模型</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl -X POST http://localhost:8080/api/v1/train \\
  -H "Content-Type: application/json" \\
  -d '{"question": "查询用户总数", "sql": "SELECT COUNT(*) FROM users"}'</div>
                        </div>
                    </div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-post">POST</span>
                            <span class="endpoint-path">/api/v1/auto_train</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/auto_train', 'POST')">试用</button>
                        </div>
                        <div class="endpoint-description">自动训练：基于数据库表结构自动生成训练数据</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl -X POST http://localhost:8080/api/v1/auto_train \\
  -H "Content-Type: application/json" \\
  -d '{}'</div>
                        </div>
                    </div>
                </div>
                
                <div class="api-section">
                    <div class="api-section-header">🔧 系统管理接口</div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-get">GET</span>
                            <span class="endpoint-path">/api/v1/health</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/health', 'GET')">试用</button>
                        </div>
                        <div class="endpoint-description">健康检查：检查各项服务的运行状态</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl http://localhost:8080/api/v1/health</div>
                        </div>
                    </div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-get">GET</span>
                            <span class="endpoint-path">/api/v1/database/info</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/database/info', 'GET')">试用</button>
                        </div>
                        <div class="endpoint-description">数据库信息：获取数据库连接和概要信息</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl http://localhost:8080/api/v1/database/info</div>
                        </div>
                    </div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-get">GET</span>
                            <span class="endpoint-path">/api/v1/database/schema</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/database/schema', 'GET')">试用</button>
                        </div>
                        <div class="endpoint-description">数据库Schema：获取所有表的结构信息</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl http://localhost:8080/api/v1/database/schema</div>
                        </div>
                    </div>
                    
                    <div class="api-endpoint">
                        <div class="endpoint-header">
                            <span class="method-badge method-post">POST</span>
                            <span class="endpoint-path">/api/v1/cache/clear</span>
                            <button class="try-button" onclick="tryEndpoint('/api/v1/cache/clear', 'POST')">试用</button>
                        </div>
                        <div class="endpoint-description">清除缓存：清除所有Redis缓存数据</div>
                        <div class="endpoint-example">
                            <h5>请求示例：</h5>
                            <div class="code-block">curl -X POST http://localhost:8080/api/v1/cache/clear \\
  -H "Content-Type: application/json" \\
  -d '{}'</div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>💡 <strong>使用提示</strong>：点击"试用"按钮可以在新窗口中测试API接口</p>
                    <p>🔗 基于 Vanna AI • 阿里云百炼(Qwen) • MySQL • Redis • Flask 构建</p>
                    <p>📧 技术支持：admin@example.com</p>
                </div>
            </div>
            
            <script>
                function tryEndpoint(path, method) {
                    const baseUrl = window.location.origin;
                    const fullUrl = baseUrl + path;
                    
                    if (method === 'GET') {
                        window.open(fullUrl, '_blank');
                    } else {
                        // 为POST请求打开一个简单的测试页面
                        const testHtml = `
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>API测试 - ${path}</title>
                                <style>
                                    body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
                                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
                                    .form-group { margin-bottom: 15px; }
                                    label { display: block; margin-bottom: 5px; font-weight: bold; }
                                    textarea { width: 100%; height: 150px; border: 1px solid #ddd; border-radius: 4px; padding: 10px; }
                                    button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
                                    button:hover { background: #0056b3; }
                                    .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; white-space: pre-wrap; }
                                </style>
                            </head>
                            <body>
                                <div class="container">
                                    <h2>API测试：${method} ${path}</h2>
                                    <div class="form-group">
                                        <label>请求Body (JSON格式):</label>
                                        <textarea id="requestBody" placeholder='{"question": "查询示例"}'></textarea>
                                    </div>
                                    <button onclick="sendRequest()">发送请求</button>
                                    <div id="result" class="result" style="display: none;"></div>
                                </div>
                                
                                <script>
                                    function sendRequest() {
                                        const body = document.getElementById('requestBody').value;
                                        const resultDiv = document.getElementById('result');
                                        
                                        fetch('${fullUrl}', {
                                            method: '${method}',
                                            headers: {
                                                'Content-Type': 'application/json'
                                            },
                                            body: body || '{}'
                                        })
                                        .then(response => response.json())
                                        .then(data => {
                                            resultDiv.style.display = 'block';
                                            resultDiv.textContent = JSON.stringify(data, null, 2);
                                        })
                                        .catch(error => {
                                            resultDiv.style.display = 'block';
                                            resultDiv.textContent = '错误: ' + error.message;
                                        });
                                    }
                                </script>
                            </body>
                            </html>
                        `;
                        
                        const newWindow = window.open('', '_blank');
                        newWindow.document.write(testHtml);
                        newWindow.document.close();
                    }
                }
            </script>
        </body>
        </html>
        """)

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': '请求参数错误'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器内部错误'
        }), 500

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=9000, debug=True) 