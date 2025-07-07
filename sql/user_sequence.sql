-- 创建用户编码序列 (MySQL 8.0+ 使用AUTO_INCREMENT实现)
-- 用于生成6位用户编码

-- 删除可能存在的旧函数和表
DROP FUNCTION IF EXISTS generate_user_code;
DROP TABLE IF EXISTS user_code_seq;

-- 创建序列表（使用AUTO_INCREMENT模拟序列）
CREATE TABLE user_code_seq (
    id INT AUTO_INCREMENT PRIMARY KEY
) ENGINE=InnoDB AUTO_INCREMENT=1;

-- 创建函数用于生成完整的用户编码
DELIMITER $$
CREATE FUNCTION generate_user_code(org_code VARCHAR(20))
RETURNS VARCHAR(16)
READS SQL DATA
MODIFIES SQL DATA
DETERMINISTIC
BEGIN
    DECLARE next_id INT;
    DECLARE padded_org_code VARCHAR(10);
    DECLARE padded_user_code VARCHAR(6);
    
    -- 插入一条记录获取下一个序列值
    INSERT INTO user_code_seq () VALUES ();
    SET next_id = LAST_INSERT_ID();
    
    -- 机构编码处理：右侧补0到10位
    SET padded_org_code = RPAD(COALESCE(org_code, ''), 10, '0');
    
    -- 用户编码处理：左侧补0到6位
    SET padded_user_code = LPAD(next_id, 6, '0');
    
    -- 返回完整的用户编码
    RETURN CONCAT(padded_org_code, padded_user_code);
END$$
DELIMITER ; 