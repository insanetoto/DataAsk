# -*- coding: utf-8 -*-
"""
Redis缓存服务模块
提供缓存管理和会话存储
"""
import json
import logging
from typing import Optional, Any, Dict, List
import redis
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """处理datetime对象的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

class RedisService:
    """Redis缓存服务类"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
            self.redis_client.ping()  # 测试连接
            logger.info("Redis连接成功")
        except redis.ConnectionError as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise
        
    def test_connection(self) -> bool:
        """测试Redis连接"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis连接测试失败: {str(e)}")
            return False
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, cls=DateTimeEncoder)
            return self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"设置缓存失败 key={key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"获取缓存失败 key={key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"删除缓存失败 key={key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在性失败 key={key}: {str(e)}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置key过期时间"""
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"设置过期时间失败 key={key}: {str(e)}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"递增计数器失败 key={key}: {str(e)}")
            return None
    
    def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """设置哈希表"""
        try:
            # 序列化复杂对象
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized_mapping[k] = json.dumps(v, ensure_ascii=False)
                else:
                    serialized_mapping[k] = v
            return bool(self.redis_client.hset(name, mapping=serialized_mapping))
        except Exception as e:
            logger.error(f"设置哈希表失败 name={name}: {str(e)}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希表字段值"""
        try:
            value = self.redis_client.hget(name, key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"获取哈希表字段失败 name={name}, key={key}: {str(e)}")
            return None
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希表所有字段"""
        try:
            data = self.redis_client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except Exception as e:
            logger.error(f"获取哈希表所有字段失败 name={name}: {str(e)}")
            return {}
    
    def cache_query_result(self, query_hash: str, result: List[Dict[str, Any]], ttl: int = 3600):
        """缓存查询结果"""
        cache_key = f"query_result:{query_hash}"
        self.set(cache_key, result, ex=ttl)
        logger.info(f"查询结果已缓存: {cache_key}")
    
    def get_cached_query_result(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的查询结果"""
        cache_key = f"query_result:{query_hash}"
        return self.get(cache_key)
    
    def cache_vanna_sql(self, question_hash: str, sql: str, ttl: int = 7200):
        """缓存Vanna生成的SQL"""
        cache_key = f"vanna_sql:{question_hash}"
        self.set(cache_key, sql, ex=ttl)
        logger.info(f"Vanna SQL已缓存: {cache_key}")
    
    def get_cached_vanna_sql(self, question_hash: str) -> Optional[str]:
        """获取缓存的Vanna SQL"""
        cache_key = f"vanna_sql:{question_hash}"
        return self.get(cache_key)
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """根据模式获取键列表"""
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"获取键列表失败 pattern={pattern}: {str(e)}")
            return []
    
    def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存（通用方法）"""
        return self.set(key, value, ex=ttl)
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存（通用方法）"""
        return self.get(key)
    
    def delete_cache(self, key: str) -> bool:
        """删除缓存（通用方法）"""
        return self.delete(key)
    
    def delete_pattern(self, pattern: str) -> bool:
        """根据模式删除缓存"""
        try:
            keys = self.get_keys_by_pattern(pattern)
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"按模式删除缓存失败 pattern={pattern}: {str(e)}")
            return False

    def set_token(self, key: str, token: str, expire_time: int = None):
        """
        存储token
        :param key: token的键
        :param token: token值
        :param expire_time: 过期时间(秒)
        """
        try:
            self.redis_client.set(key, token)
            if expire_time:
                self.redis_client.expire(key, expire_time)
            return True
        except Exception as e:
            logger.error(f"存储token失败: {str(e)}")
            return False

    def get_token(self, key: str) -> str:
        """
        获取token
        :param key: token的键
        :return: token值
        """
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"获取token失败: {str(e)}")
            return None

    def delete_token(self, key: str) -> bool:
        """
        删除token
        :param key: token的键
        :return: 是否成功
        """
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"删除token失败: {str(e)}")
            return False

    def check_token_exists(self, key: str) -> bool:
        """
        检查token是否存在
        :param key: token的键
        :return: 是否存在
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查token是否存在失败: {str(e)}")
            return False

# 单例模式
_redis_service = None

def get_redis_service() -> RedisService:
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service 