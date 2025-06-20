# -*- coding: utf-8 -*-
"""
密码迁移工具
用于将数据库中的明文密码转换为bcrypt加密密码
"""
import logging
import bcrypt
from tools.database import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

def migrate_passwords():
    """将数据库中的明文密码迁移为bcrypt加密密码"""
    try:
        with get_db_session() as session:
            # 获取所有用户
            users = session.execute(text("SELECT id, password_hash FROM users")).fetchall()
            
            success_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    # 检查密码是否已经是bcrypt格式
                    if user.password_hash and not user.password_hash.startswith('$2b$'):
                        # 加密明文密码
                        password_hash = bcrypt.hashpw(user.password_hash.encode('utf-8'), bcrypt.gensalt())
                        
                        # 更新数据库
                        session.execute(
                            text("UPDATE users SET password_hash = :password_hash WHERE id = :id"),
                            {"password_hash": password_hash.decode('utf-8'), "id": user.id}
                        )
                        success_count += 1
                        logger.info(f"成功加密用户ID {user.id} 的密码")
                    else:
                        logger.info(f"用户ID {user.id} 的密码已经是加密格式或为空，跳过")
                        
                except Exception as e:
                    logger.error(f"加密用户ID {user.id} 的密码时出错: {str(e)}")
                    failed_count += 1
            
            session.commit()
            logger.info(f"密码迁移完成。成功: {success_count}, 跳过/失败: {failed_count}")
            
            return {
                'success': True,
                'message': f'密码迁移完成。成功: {success_count}, 跳过/失败: {failed_count}'
            }
            
    except Exception as e:
        error_msg = f"密码迁移失败: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # 执行迁移
    result = migrate_passwords()
    if result['success']:
        print(result['message'])
    else:
        print(f"错误: {result['error']}") 