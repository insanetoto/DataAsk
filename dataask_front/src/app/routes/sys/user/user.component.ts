import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { finalize } from 'rxjs';

import { SysUserService, User, UserQuery } from './user.service';

@Component({
  selector: 'app-sys-user',
  templateUrl: './user.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: SHARED_IMPORTS
})
export class SysUserComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly userService = inject(SysUserService);

  // 查询参数
  q: UserQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: undefined,
    org_code: '',
    role_id: undefined
  };

  // 数据和状态
  data: User[] = [];
  loading = false;
  selectedRows: STData[] = [];
  expandForm = false;

  // 表单数据
  editingUser: Partial<User> = {};
  isEditMode = false;
  modalTitle = '';

  // 选项数据
  organizationOptions: any[] = [];
  roleOptions: any[] = [];

  // 状态选项
  statusOptions = [
    { label: '全部', value: undefined },
    { label: '启用', value: 1 },
    { label: '禁用', value: 0 }
  ];

  @ViewChild('st', { static: true })
  st!: STComponent;

  // 表格列配置
  columns: STColumn[] = [
    { title: '', index: 'key', type: 'checkbox' },
    {
      title: '用户编码',
      index: 'user_code',
      width: 120,
      sort: true
    },
    {
      title: '用户名称',
      index: 'username',
      width: 150,
      sort: true
    },
    {
      title: '所属机构',
      index: 'org_code',
      width: 150,
      format: (item: User) => (item as any).org_name || item.org_code || '-'
    },
    {
      title: '角色',
      index: 'role_id',
      width: 120,
      format: (item: User) => this.getRoleNameByCode((item as any).role_code) || '-'
    },
    {
      title: '联系电话',
      index: 'phone',
      width: 120
    },
    {
      title: '登录次数',
      index: 'login_count',
      width: 100,
      type: 'number'
    },
    {
      title: '最后登录',
      index: 'last_login_at',
      type: 'date',
      width: 150,
      sort: true
    },
    {
      title: '状态',
      index: 'status',
      render: 'status',
      width: 80,
      filter: {
        menus: [
          { text: '启用', value: 1 },
          { text: '禁用', value: 0 }
        ],
        fn: (filter, record) => record.status === filter.value
      }
    },
    {
      title: '创建时间',
      index: 'created_at',
      type: 'date',
      width: 150,
      sort: true
    },
    {
      title: '操作',
      width: 280,
      fixed: 'right',
      buttons: [
        {
          text: '查看',
          icon: 'eye',
          click: (item: User) => this.viewUser(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          click: (item: User) => this.editUser(item)
        },
        {
          text: '重置密码',
          icon: 'lock',
          click: (item: User) => this.resetPassword(item)
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: User) => this.deleteUser(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
    this.loadOrganizationOptions();
    this.loadRoleOptions();
  }

  /**
   * 根据角色编码获取角色名称
   */
  getRoleNameByCode(roleCode: string): string {
    const roleMap: Record<string, string> = {
      SUPER_ADMIN: '超级系统管理员',
      ORG_ADMIN: '机构管理员',
      NORMAL_USER: '普通用户'
    };
    return roleMap[roleCode] || roleCode || '-';
  }

  /**
   * 获取用户列表数据
   */
  getData(): void {
    this.loading = true;
    const params = {
      pi: this.q.pi,
      ps: this.q.ps,
      keyword: this.q.keyword || '',
      status: this.q.status,
      org_code: this.q.org_code || '',
      role_id: this.q.role_id
    };

    this.userService
      .getUsers(params)
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.data = res.data?.list || res.data?.items || res.data || [];
          } else {
            this.msg.error(res.message || '获取用户数据失败');
            this.data = [];
          }
        },
        error: error => {
          console.error('获取用户数据失败:', error);

          // 检查是否是被HTTP拦截器误判的成功响应
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              this.data = error.body.data?.list || error.body.data?.items || error.body.data || [];
              return;
            }
          }

          this.msg.error('获取用户数据失败');
          this.data = [];
        }
      });
  }

  /**
   * 加载机构选项
   */
  loadOrganizationOptions(): void {
    this.http.get('/organizations', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.organizationOptions = res.data?.list || res.data?.items || res.data || [];
        }
      },
      error: error => {
        console.error('加载机构选项失败:', error);

        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.organizationOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
          }
        }
      }
    });
  }

  /**
   * 加载角色选项
   */
  loadRoleOptions(): void {
    this.http.get('/roles', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.roleOptions = res.data?.list || res.data?.items || res.data || [];
        }
      },
      error: error => {
        console.error('加载角色选项失败:', error);

        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.roleOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
          }
        }
      }
    });
  }

  /**
   * 表格变化事件
   */
  stChange(e: STChange): void {
    switch (e.type) {
      case 'checkbox':
        this.selectedRows = e.checkbox!;
        this.cdr.detectChanges();
        break;
      case 'filter':
        this.getData();
        break;
      case 'sort':
        this.getData();
        break;
      case 'pi':
        this.q.pi = e.pi!;
        this.getData();
        break;
      case 'ps':
        this.q.ps = e.ps!;
        this.getData();
        break;
    }
  }

  /**
   * 新增用户
   */
  addUser(tpl: TemplateRef<unknown>): void {
    this.editingUser = {
      status: 1
    };
    this.isEditMode = false;
    this.modalTitle = '新增用户';
    this.showModal(tpl);
  }

  /**
   * 查看用户
   */
  viewUser(item: User): void {
    this.editingUser = { ...item };
    this.isEditMode = false;
    this.modalTitle = '查看用户';
    this.msg.info(`查看用户: ${item.username}`);
  }

  /**
   * 编辑用户
   */
  editUser(item: User, tpl?: TemplateRef<unknown>): void {
    this.editingUser = { ...item };
    this.isEditMode = true;
    this.modalTitle = '编辑用户';
    if (tpl) {
      this.showModal(tpl);
    }
  }

  /**
   * 删除用户
   */
  deleteUser(item: User): void {
    this.modalSrv.confirm({
      nzTitle: '确认删除',
      nzContent: `确定要删除用户 "${item.username}" 吗？`,
      nzOnOk: () => {
        return this.userService.deleteUser(item.id!).subscribe({
          next: res => {
            if (res.code === 200 || res.success === true) {
              this.msg.success('删除成功');
              this.getData();
            } else {
              this.msg.error(res.message || res.error || '删除失败');
            }
          },
          error: () => {
            this.msg.error('删除失败');
          }
        });
      }
    });
  }

  /**
   * 重置密码
   */
  resetPassword(item: User): void {
    this.modalSrv.confirm({
      nzTitle: '重置密码',
      nzContent: `确定要重置用户 "${item.username}" 的密码吗？密码将重置为默认密码。`,
      nzOnOk: () => {
        return this.userService.resetPassword(item.id!, '123456').subscribe({
          next: res => {
            if (res.code === 200 || res.success === true) {
              this.msg.success('密码重置成功，默认密码为：123456');
            } else {
              this.msg.error(res.message || res.error || '密码重置失败');
            }
          },
          error: () => {
            this.msg.error('密码重置失败');
          }
        });
      }
    });
  }

  /**
   * 批量删除
   */
  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的用户');
      return;
    }

    this.modalSrv.confirm({
      nzTitle: '确认批量删除',
      nzContent: `确定要删除选中的 ${this.selectedRows.length} 个用户吗？`,
      nzOnOk: () => {
        const userIds = this.selectedRows.map(row => row['id']);
        return this.userService.batchDeleteUsers(userIds).subscribe({
          next: res => {
            if (res.code === 200 || res.success === true) {
              this.msg.success('批量删除成功');
              this.getData();
              this.st.clearCheck();
            } else {
              this.msg.error(res.message || res.error || '批量删除失败');
            }
          },
          error: () => {
            this.msg.error('批量删除失败');
          }
        });
      }
    });
  }

  /**
   * 显示模态框
   */
  showModal(tpl: TemplateRef<unknown>): void {
    this.modalSrv.create({
      nzTitle: this.modalTitle,
      nzContent: tpl,
      nzWidth: 600,
      nzOnOk: () => {
        return this.saveUser();
      }
    });
  }

  /**
   * 保存用户
   */
  saveUser(): Promise<boolean> {
    return new Promise(resolve => {
      // 表单验证
      if (!this.editingUser.user_code || !this.editingUser.username || !this.editingUser.org_code || !this.editingUser.role_id) {
        this.msg.error('请填写完整信息');
        resolve(false);
        return;
      }

      const request = this.isEditMode
        ? this.userService.updateUser(this.editingUser.id!, this.editingUser)
        : this.userService.createUser(this.editingUser);

      request.subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.msg.success(this.isEditMode ? '更新成功' : '创建成功');
            this.getData();
            resolve(true);
          } else {
            this.msg.error(res.message || res.error || '保存失败');
            resolve(false);
          }
        },
        error: () => {
          this.msg.error('保存失败');
          resolve(false);
        }
      });
    });
  }

  /**
   * 重置搜索
   */
  reset(): void {
    this.q = {
      pi: 1,
      ps: 10,
      keyword: '',
      status: undefined,
      org_code: '',
      role_id: undefined
    };
    this.getData();
  }
}
