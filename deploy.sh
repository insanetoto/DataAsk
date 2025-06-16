#!/bin/bash

# 百惟数问智能数据问答平台 - 一键部署脚本
# 支持 Ubuntu 20.04+ 和 CentOS 7+

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/redhat-release ]]; then
        OS="centos"
        VERSION=$(rpm -q --qf "%{VERSION}" $(rpm -q --whatprovides redhat-release))
    elif [[ -f /etc/lsb-release ]]; then
        OS="ubuntu"
        VERSION=$(lsb_release -sr)
    elif [[ -f /etc/debian_version ]]; then
        OS="ubuntu"
        VERSION=$(cat /etc/debian_version)
    else
        log_error "不支持的操作系统"
        exit 1
    fi
    log_info "检测到操作系统: $OS $VERSION"
}

# 安装基础依赖
install_dependencies() {
    log_step "安装基础依赖..."
    
    if [[ "$OS" == "centos" ]]; then
        # CentOS/RHEL
        yum update -y
        yum groupinstall -y "Development Tools"
        yum install -y epel-release
        yum install -y python3 python3-pip python3-devel \
                       mysql-devel gcc gcc-c++ make \
                       redis nginx supervisor \
                       git curl wget
    elif [[ "$OS" == "ubuntu" ]]; then
        # Ubuntu/Debian
        apt-get update -y
        apt-get install -y build-essential software-properties-common
        apt-get install -y python3 python3-pip python3-dev python3-venv \
                           libmysqlclient-dev pkg-config \
                           redis-server nginx supervisor \
                           git curl wget
    fi
    
    log_info "基础依赖安装完成"
}

# 安装MySQL
install_mysql() {
    log_step "安装MySQL..."
    
    if [[ "$OS" == "centos" ]]; then
        yum install -y mysql-server mysql
        systemctl start mysqld
        systemctl enable mysqld
        
        # 获取临时密码
        TEMP_PASSWORD=$(grep 'temporary password' /var/log/mysqld.log | tail -1 | awk '{print $NF}')
        log_info "MySQL临时密码: $TEMP_PASSWORD"
        
    elif [[ "$OS" == "ubuntu" ]]; then
        apt-get install -y mysql-server
        systemctl start mysql
        systemctl enable mysql
    fi
    
    log_info "MySQL安装完成"
}

# 创建应用用户
create_app_user() {
    log_step "创建应用用户..."
    
    useradd -m -s /bin/bash dataask || true
    usermod -aG sudo dataask 2>/dev/null || usermod -aG wheel dataask 2>/dev/null || true
    
    log_info "应用用户创建完成"
}

# 设置应用目录
setup_app_directory() {
    log_step "设置应用目录..."
    
    APP_DIR="/opt/dataask"
    mkdir -p $APP_DIR
    chown dataask:dataask $APP_DIR
    
    log_info "应用目录设置完成: $APP_DIR"
}

# 安装Python虚拟环境
setup_python_env() {
    log_step "设置Python虚拟环境..."
    
    cd $APP_DIR
    sudo -u dataask python3 -m venv venv
    sudo -u dataask $APP_DIR/venv/bin/pip install --upgrade pip
    
    log_info "Python虚拟环境设置完成"
}

# 下载应用代码 (如果从GitHub部署)
download_app() {
    log_step "下载应用代码..."
    
    if [[ -n "$GITHUB_REPO" ]]; then
        cd /tmp
        git clone $GITHUB_REPO dataask-code
        cp -r dataask-code/* $APP_DIR/
        chown -R dataask:dataask $APP_DIR
        rm -rf dataask-code
    else
        log_warn "未指定GitHub仓库，请手动上传代码到 $APP_DIR"
    fi
    
    log_info "应用代码准备完成"
}

# 安装Python依赖
install_python_deps() {
    log_step "安装Python依赖..."
    
    cd $APP_DIR
    if [[ -f requirements.txt ]]; then
        sudo -u dataask $APP_DIR/venv/bin/pip install -r requirements.txt
        log_info "Python依赖安装完成"
    else
        log_warn "未找到requirements.txt文件"
    fi
}

# 创建配置文件
create_config() {
    log_step "创建配置文件..."
    
    cd $APP_DIR
    
    if [[ ! -f .env ]]; then
        sudo -u dataask cp env.example .env
        
        # 生成随机密钥
        SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
        
        sudo -u dataask sed -i "s/your-secret-key/$SECRET_KEY/g" .env
        sudo -u dataask sed -i "s/your-mysql-password/DataAsk@2024/g" .env
        sudo -u dataask sed -i "s/your-openai-api-key/your-actual-key/g" .env
        
        log_info "配置文件创建完成，请编辑 $APP_DIR/.env 文件"
    fi
}

# 配置MySQL数据库
setup_database() {
    log_step "配置MySQL数据库..."
    
    mysql -e "CREATE DATABASE IF NOT EXISTS llmstudy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -e "CREATE USER IF NOT EXISTS 'dataask'@'localhost' IDENTIFIED BY 'DataAsk@2024';"
    mysql -e "GRANT ALL PRIVILEGES ON llmstudy.* TO 'dataask'@'localhost';"
    mysql -e "FLUSH PRIVILEGES;"
    
    log_info "数据库配置完成"
}

# 配置Redis
setup_redis() {
    log_step "配置Redis..."
    
    systemctl start redis
    systemctl enable redis
    
    # 配置Redis
    if [[ "$OS" == "centos" ]]; then
        REDIS_CONF="/etc/redis.conf"
    else
        REDIS_CONF="/etc/redis/redis.conf"
    fi
    
    sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' $REDIS_CONF
    sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' $REDIS_CONF
    
    systemctl restart redis
    
    log_info "Redis配置完成"
}

# 配置Nginx
setup_nginx() {
    log_step "配置Nginx..."
    
    cat > /etc/nginx/sites-available/dataask << 'EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static {
        alias /opt/dataask/static;
        expires 1y;
        access_log off;
    }
}
EOF
    
    # 启用站点
    if [[ "$OS" == "ubuntu" ]]; then
        ln -sf /etc/nginx/sites-available/dataask /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
    elif [[ "$OS" == "centos" ]]; then
        cp /etc/nginx/sites-available/dataask /etc/nginx/conf.d/dataask.conf
    fi
    
    nginx -t
    systemctl start nginx
    systemctl enable nginx
    
    log_info "Nginx配置完成"
}

# 配置Supervisor
setup_supervisor() {
    log_step "配置Supervisor..."
    
    cat > /etc/supervisor/conf.d/dataask.conf << EOF
[program:dataask]
command=$APP_DIR/venv/bin/python app.py
directory=$APP_DIR
user=dataask
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dataask.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="$APP_DIR/venv/bin"
EOF
    
    systemctl start supervisor
    systemctl enable supervisor
    supervisorctl reread
    supervisorctl update
    
    log_info "Supervisor配置完成"
}

# 配置防火墙
setup_firewall() {
    log_step "配置防火墙..."
    
    if [[ "$OS" == "centos" ]]; then
        systemctl start firewalld
        systemctl enable firewalld
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    elif [[ "$OS" == "ubuntu" ]]; then
        ufw --force reset
        ufw allow ssh
        ufw allow http
        ufw allow https
        ufw --force enable
    fi
    
    log_info "防火墙配置完成"
}

# 生成License工具
create_license_tool() {
    log_step "创建License管理工具..."
    
    cat > /usr/local/bin/dataask-license << 'EOF'
#!/bin/bash
cd /opt/dataask
sudo -u dataask /opt/dataask/venv/bin/python license_manager.py "$@"
EOF
    
    chmod +x /usr/local/bin/dataask-license
    
    log_info "License管理工具创建完成"
    log_info "使用方法: dataask-license generate '机构名称' '2025-12-31'"
}

# 启动服务
start_services() {
    log_step "启动服务..."
    
    supervisorctl start dataask
    systemctl restart nginx
    
    log_info "服务启动完成"
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"
    
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  百惟数问智能数据问答平台部署完成  ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo -e "${BLUE}应用信息:${NC}"
    echo "  应用目录: $APP_DIR"
    echo "  配置文件: $APP_DIR/.env"
    echo "  日志文件: /var/log/dataask.log"
    echo
    echo -e "${BLUE}访问地址:${NC}"
    echo "  HTTP: http://$(hostname -I | awk '{print $1}')"
    echo "  本机: http://localhost"
    echo
    echo -e "${BLUE}管理命令:${NC}"
    echo "  查看状态: supervisorctl status dataask"
    echo "  重启应用: supervisorctl restart dataask"
    echo "  查看日志: tail -f /var/log/dataask.log"
    echo "  生成License: dataask-license generate '机构名称' '2025-12-31'"
    echo
    echo -e "${YELLOW}重要提醒:${NC}"
    echo "  1. 请编辑配置文件 $APP_DIR/.env"
    echo "  2. 设置正确的OpenAI API Key"
    echo "  3. 生成应用License后才能正常使用"
    echo "  4. 建议配置SSL证书保证安全"
    echo
}

# 主函数
main() {
    log_info "开始部署百惟数问智能数据问答平台..."
    
    check_root
    detect_os
    install_dependencies
    install_mysql
    create_app_user
    setup_app_directory
    setup_python_env
    download_app
    install_python_deps
    create_config
    setup_database
    setup_redis
    setup_nginx
    setup_supervisor
    setup_firewall
    create_license_tool
    start_services
    show_deployment_info
}

# 设置默认仓库地址
GITHUB_REPO="${GITHUB_REPO:-https://github.com/insanetoto/DataAsk.git}"

# 处理命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --repo URL    指定GitHub仓库地址 (默认: https://github.com/insanetoto/DataAsk.git)"
            echo "  --help        显示帮助信息"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 执行部署
main 