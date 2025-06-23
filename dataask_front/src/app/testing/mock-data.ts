export const mockUser = {
  id: 1,
  username: 'testuser',
  user_code: 'TEST001',
  org_code: 'ORG001',
  role_id: 1,
  phone: '13800138000',
  email: 'test@example.com',
  status: 1,
  login_count: 10,
  last_login_at: '2024-01-01T10:00:00Z',
  created_at: '2024-01-01T10:00:00Z',
  organization: {
    org_name: '测试机构',
    org_code: 'ORG001'
  },
  role: {
    role_name: '测试角色',
    role_code: 'TEST_ROLE'
  }
};

export const mockUserList = {
  list: [mockUser],
  total: 1,
  page: 1,
  size: 10
};

export const mockOrganization = {
  id: 1,
  org_code: 'ORG001',
  org_name: '测试机构',
  contact_person: '张三',
  contact_phone: '13800138000',
  contact_email: 'org@example.com',
  status: 1,
  created_at: '2024-01-01T10:00:00Z'
};

export const mockRole = {
  id: 1,
  role_code: 'TEST_ROLE',
  role_name: '测试角色',
  role_level: 1,
  description: '测试角色描述',
  status: 1,
  created_at: '2024-01-01T10:00:00Z'
};

export const mockPermission = {
  id: 1,
  permission_code: 'TEST_PERM',
  permission_name: '测试权限',
  api_path: '/api/test',
  api_method: 'GET',
  resource_type: 'api',
  description: '测试权限描述',
  status: 1,
  created_at: '2024-01-01T10:00:00Z'
};

export const mockReportData = {
  total_users: 1234,
  total_organizations: 56,
  total_queries: 8901,
  system_availability: 99.9
};

export function createMockResponse<T>(data: T, success = true) {
  return {
    code: success ? 200 : 500,
    message: success ? '操作成功' : '操作失败',
    data: data,
    success: success
  };
} 