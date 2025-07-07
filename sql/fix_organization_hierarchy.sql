-- 修复机构层级数据问题（不使用触发器，在service层实现层级计算）
-- 清理旧的触发器和函数，修复现有数据

USE dataask;

-- 1. 删除有问题的旧触发器
DROP TRIGGER IF EXISTS tr_organizations_level_update;
DROP TRIGGER IF EXISTS tr_organizations_insert_level;
DROP TRIGGER IF EXISTS tr_organizations_update_level;

-- 2. 删除有问题的旧函数
DROP FUNCTION IF EXISTS CalculateOrgDepth;
DROP FUNCTION IF EXISTS GetOrgLevelDepth;
DROP FUNCTION IF EXISTS GetOrgLevelPath;

-- 3. 修复现有数据的层级信息
-- 先处理顶级机构（没有上级机构的）
UPDATE organizations 
SET level_depth = 0, 
    level_path = CONCAT('/', org_code, '/') 
WHERE parent_org_code IS NULL OR parent_org_code = '';

-- 处理第一级子机构
UPDATE organizations o1
JOIN organizations o2 ON o1.parent_org_code = o2.org_code
SET o1.level_depth = 1,
    o1.level_path = CONCAT(o2.level_path, o1.org_code, '/')
WHERE o2.level_depth = 0;

-- 处理第二级子机构
UPDATE organizations o1
JOIN organizations o2 ON o1.parent_org_code = o2.org_code
SET o1.level_depth = 2,
    o1.level_path = CONCAT(o2.level_path, o1.org_code, '/')
WHERE o2.level_depth = 1;

-- 处理第三级子机构
UPDATE organizations o1
JOIN organizations o2 ON o1.parent_org_code = o2.org_code
SET o1.level_depth = 3,
    o1.level_path = CONCAT(o2.level_path, o1.org_code, '/')
WHERE o2.level_depth = 2;

-- 处理第四级子机构
UPDATE organizations o1
JOIN organizations o2 ON o1.parent_org_code = o2.org_code
SET o1.level_depth = 4,
    o1.level_path = CONCAT(o2.level_path, o1.org_code, '/')
WHERE o2.level_depth = 3;

-- 4. 验证修复结果
SELECT 
    org_code,
    parent_org_code,
    org_name,
    level_depth,
    level_path,
    CASE 
        WHEN parent_org_code IS NULL THEN '顶级机构'
        ELSE CONCAT('子机构(父:', parent_org_code, ')')
    END as hierarchy_info
FROM organizations 
ORDER BY level_path, org_code;

-- 完成修复
SELECT '机构层级数据修复完成！后续层级计算将在service层进行。' as status; 