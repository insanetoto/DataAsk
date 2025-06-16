# -*- coding: utf-8 -*-
"""
Redis缓存服务模块
提供缓存管理和会话存储
"""
import json
import logging
from typing import Optional, Any, Dict, List
import redis
from config import Config

logger = logging.getLogger(__name__)

class RedisService:
    """Redis缓存服务类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.redis_client = self._create_redis_client()
        
    def _create_redis_client(self):
        """创建Redis客户端"""
        try:
            client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                password=self.config.REDIS_PASSWORD if self.config.REDIS_PASSWORD else None,
                db=self.config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            client.ping()
            logger.info("Redis连接创建成功")
            return client
        except Exception as e:
            logger.error(f"Redis连接创建失败: {str(e)}")
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
                value = json.dumps(value, ensure_ascii=False)
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

# 全局Redis服务实例
redis_service = None

def init_redis_service(config: Config) -> RedisService:
    """初始化Redis服务"""
    global redis_service
    redis_service = RedisService(config)
    return redis_service

def get_redis_service() -> RedisService:
    """获取Redis服务实例"""
    if redis_service is None:
        raise RuntimeError("Redis服务未初始化")
    return redis_service 