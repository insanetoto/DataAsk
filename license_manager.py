#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
License授权管理系统
提供License生成、验证和管理功能
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Optional, Any
import argparse


class LicenseManager:
    """License管理器"""
    
    def __init__(self, secret_key: str = "DataAsk-Secret-Key-2024"):
        """
        初始化License管理器
        
        Args:
            secret_key: 用于加密的密钥
        """
        self.secret_key = secret_key.encode()
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """创建Fernet加密实例"""
        # 使用PBKDF2从密钥派生加密密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'dataask_salt_2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        return Fernet(key)
    
    def generate_license(
        self, 
        organization: str, 
        expire_date: str,
        features: Optional[Dict[str, Any]] = None,
        max_users: int = 100
    ) -> str:
        """
        生成License
        
        Args:
            organization: 机构名称
            expire_date: 过期时间 (格式: YYYY-MM-DD)
            features: 功能特性配置
            max_users: 最大用户数
            
        Returns:
            加密后的License字符串
        """
        if features is None:
            features = {
                "ai_query": True,
                "sql_generation": True,
                "data_visualization": True,
                "cache_enabled": True,
                "training_enabled": True
            }
        
        try:
            # 解析过期时间
            expire_datetime = datetime.strptime(expire_date, "%Y-%m-%d")
            
            # 创建License数据
            license_data = {
                "organization": organization,
                "issue_date": datetime.now().isoformat(),
                "expire_date": expire_datetime.isoformat(),
                "features": features,
                "max_users": max_users,
                "license_version": "1.0",
                "product": "百惟数问智能数据问答平台"
            }
            
            # 添加校验和
            license_json = json.dumps(license_data, sort_keys=True)
            checksum = hashlib.sha256(license_json.encode()).hexdigest()[:16]
            license_data["checksum"] = checksum
            
            # 加密License数据
            license_bytes = json.dumps(license_data).encode()
            encrypted_license = self.fernet.encrypt(license_bytes)
            
            # Base64编码便于传输
            return base64.b64encode(encrypted_license).decode()
            
        except ValueError as e:
            raise ValueError(f"日期格式错误: {e}")
        except Exception as e:
            raise Exception(f"License生成失败: {e}")
    
    def verify_license(self, license_str: str) -> Dict[str, Any]:
        """
        验证License
        
        Args:
            license_str: License字符串
            
        Returns:
            验证结果和License信息
        """
        try:
            # Base64解码
            encrypted_license = base64.b64decode(license_str.encode())
            
            # 解密License数据
            license_bytes = self.fernet.decrypt(encrypted_license)
            license_data = json.loads(license_bytes.decode())
            
            # 验证必要字段
            required_fields = ["organization", "expire_date", "checksum", "features"]
            for field in required_fields:
                if field not in license_data:
                    return {
                        "valid": False,
                        "error": f"License格式错误：缺少{field}字段",
                        "data": None
                    }
            
            # 验证校验和
            temp_data = license_data.copy()
            original_checksum = temp_data.pop("checksum")
            license_json = json.dumps(temp_data, sort_keys=True)
            calculated_checksum = hashlib.sha256(license_json.encode()).hexdigest()[:16]
            
            if original_checksum != calculated_checksum:
                return {
                    "valid": False,
                    "error": "License校验和验证失败",
                    "data": None
                }
            
            # 验证过期时间
            expire_date = datetime.fromisoformat(license_data["expire_date"])
            current_time = datetime.now()
            
            if current_time > expire_date:
                return {
                    "valid": False,
                    "error": f"License已过期 (过期时间: {expire_date.strftime('%Y-%m-%d')})",
                    "data": license_data
                }
            
            # 计算剩余天数
            days_remaining = (expire_date - current_time).days
            
            return {
                "valid": True,
                "error": None,
                "data": license_data,
                "days_remaining": days_remaining,
                "expire_date": expire_date.strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"License验证失败: {str(e)}",
                "data": None
            }
    
    def get_license_info(self, license_str: str) -> Optional[Dict[str, Any]]:
        """
        获取License信息（仅用于显示，不验证有效性）
        
        Args:
            license_str: License字符串
            
        Returns:
            License信息
        """
        try:
            encrypted_license = base64.b64decode(license_str.encode())
            license_bytes = self.fernet.decrypt(encrypted_license)
            return json.loads(license_bytes.decode())
        except:
            return None


class LicenseStorage:
    """License存储管理"""
    
    def __init__(self, license_file: str = "license.key"):
        """
        初始化License存储
        
        Args:
            license_file: License文件路径
        """
        self.license_file = license_file
    
    def save_license(self, license_str: str) -> bool:
        """
        保存License到文件
        
        Args:
            license_str: License字符串
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.license_file, 'w', encoding='utf-8') as f:
                f.write(license_str)
            return True
        except Exception as e:
            print(f"保存License失败: {e}")
            return False
    
    def load_license(self) -> Optional[str]:
        """
        从文件加载License
        
        Returns:
            License字符串，如果不存在则返回None
        """
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"加载License失败: {e}")
            return None
    
    def delete_license(self) -> bool:
        """
        删除License文件
        
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            return True
        except Exception as e:
            print(f"删除License失败: {e}")
            return False


def main():
    """命令行工具主函数"""
    parser = argparse.ArgumentParser(description="百惟数问 License管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 生成License命令
    generate_parser = subparsers.add_parser('generate', help='生成License')
    generate_parser.add_argument('organization', help='机构名称')
    generate_parser.add_argument('expire_date', help='过期时间 (YYYY-MM-DD)')
    generate_parser.add_argument('--max-users', type=int, default=100, help='最大用户数 (默认: 100)')
    generate_parser.add_argument('--output', '-o', help='输出文件路径 (默认: license.key)')
    
    # 验证License命令
    verify_parser = subparsers.add_parser('verify', help='验证License')
    verify_parser.add_argument('--license', '-l', help='License字符串或文件路径')
    
    # 查看License信息命令
    info_parser = subparsers.add_parser('info', help='查看License信息')
    info_parser.add_argument('--license', '-l', help='License字符串或文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = LicenseManager()
    storage = LicenseStorage()
    
    if args.command == 'generate':
        try:
            print(f"🔑 正在为机构 '{args.organization}' 生成License...")
            license_str = manager.generate_license(
                organization=args.organization,
                expire_date=args.expire_date,
                max_users=args.max_users
            )
            
            # 保存到文件
            output_file = args.output or 'license.key'
            storage_manager = LicenseStorage(output_file)
            if storage_manager.save_license(license_str):
                print(f"✅ License已生成并保存到: {output_file}")
                print(f"📅 过期时间: {args.expire_date}")
                print(f"👥 最大用户数: {args.max_users}")
                print(f"\n🔐 License内容:")
                print(license_str)
            else:
                print("❌ License保存失败")
                
        except Exception as e:
            print(f"❌ License生成失败: {e}")
    
    elif args.command == 'verify':
        license_str = None
        
        if args.license:
            if os.path.exists(args.license):
                # 从文件读取
                storage_manager = LicenseStorage(args.license)
                license_str = storage_manager.load_license()
            else:
                # 直接使用字符串
                license_str = args.license
        else:
            # 从默认文件读取
            license_str = storage.load_license()
        
        if not license_str:
            print("❌ 未找到License")
            return
        
        result = manager.verify_license(license_str)
        
        if result['valid']:
            data = result['data']
            print("✅ License验证通过")
            print(f"🏢 机构: {data['organization']}")
            print(f"📅 过期时间: {result['expire_date']}")
            print(f"⏰ 剩余天数: {result['days_remaining']} 天")
            print(f"👥 最大用户数: {data.get('max_users', 'N/A')}")
            print("🚀 功能特性:")
            for feature, enabled in data['features'].items():
                status = "✅" if enabled else "❌"
                print(f"   {status} {feature}")
        else:
            print(f"❌ License验证失败: {result['error']}")
    
    elif args.command == 'info':
        license_str = None
        
        if args.license:
            if os.path.exists(args.license):
                storage_manager = LicenseStorage(args.license)
                license_str = storage_manager.load_license()
            else:
                license_str = args.license
        else:
            license_str = storage.load_license()
        
        if not license_str:
            print("❌ 未找到License")
            return
        
        info = manager.get_license_info(license_str)
        if info:
            print("📋 License信息:")
            print(f"🏢 机构: {info['organization']}")
            print(f"📅 签发时间: {info['issue_date']}")
            print(f"📅 过期时间: {info['expire_date']}")
            print(f"👥 最大用户数: {info.get('max_users', 'N/A')}")
            print(f"📦 产品: {info['product']}")
            print("🚀 功能特性:")
            for feature, enabled in info['features'].items():
                status = "✅" if enabled else "❌"
                print(f"   {status} {feature}")
        else:
            print("❌ 无法解析License信息")


if __name__ == '__main__':
    main() 