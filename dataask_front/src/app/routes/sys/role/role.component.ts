import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzBadgeModule } from 'ng-zorro-antd/badge';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { NzSwitchModule } from 'ng-zorro-antd/switch';
import { NzTreeModule } from 'ng-zorro-antd/tree';
import { map, tap } from 'rxjs';

@Component({
  selector: 'app-sys-role',
  templateUrl: './role.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [...SHARED_IMPORTS, NzBadgeModule, NzSwitchModule, NzTreeModule, FormsModule],
  standalone: true
})
export class SysRoleComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);

  @ViewChild('modalContent')
  modalContent!: TemplateRef<unknown>;

  @ViewChild('permissionModal')
  permissionModal!: TemplateRef<unknown>;

  @ViewChild('st', { static: false })
  st!: STComponent;

  q = {
    page: 1,
    page_size: 10,
    status: null as number | null,
    keyword: ''
  };

  data: STData[] = [];
  total = 0;
  loading = false;
  status = [
    { index: 1, text: '启用', value: true, type: 'success', checked: false },
    { index: 0, text: '禁用', value: false, type: 'default', checked: false }
  ];

  columns: STColumn[] = [
    { title: '', index: 'key', type: 'checkbox' },
    { title: '角色名称', index: 'role_name' },
    { title: '角色编码', index: 'role_code' },
    { title: '描述', index: 'description' },
    {
      title: '状态',
      index: 'status',
      render: 'status',
      filter: {
        menus: this.status,
        fn: (filter, record) => record.status === filter['index']
      }
    },
    {
      title: '操作',
      buttons: [
        {
          text: '编辑',
          click: (item: any) => this.edit(this.modalContent, item)
        },
        {
          text: '权限设置',
          click: (item: any) => this.setPermissions(item)
        },
        {
          text: '删除',
          click: (item: any) => this.deleteRole(item)
        }
      ]
    }
  ];

  selectedRows: STData[] = [];
  formData = {
    role_name: '',
    role_code: '',
    description: '',
    status: 1
  };
  expandForm = false;

  // 权限树相关
  permissionTreeData: any[] = [];
  checkedKeys: string[] = [];
  selectedRole: any = null;

  ngOnInit(): void {
    this.getData();
  }

  getData(): void {
    this.loading = true;
    this.http
      .get('/api/roles', {
        params: {
          ...this.q,
          type: 'list'
        }
      })
      .pipe(
        map((res: any) => {
          if (res.success) {
            this.total = res.data.pagination.total;
            return res.data.list || [];
          }
          throw new Error(res.error || '获取数据失败');
        }),
        tap(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          this.data = res;
          this.cdr.detectChanges();
        },
        error: err => {
          this.loading = false;
          this.msg.error(err.message || '获取数据失败');
          this.cdr.detectChanges();
        }
      });
  }

  stChange(e: STChange): void {
    switch (e.type) {
      case 'checkbox':
        this.selectedRows = e.checkbox!;
        this.cdr.detectChanges();
        break;
      case 'filter':
        this.getData();
        break;
      case 'pi':
        this.q.page = e.pi!;
        this.getData();
        break;
      case 'ps':
        this.q.page_size = e.ps!;
        this.getData();
        break;
    }
  }

  add(tpl: TemplateRef<unknown>): void {
    this.formData = {
      role_name: '',
      role_code: '',
      description: '',
      status: 1
    };
    this.modalSrv.create({
      nzTitle: '新建角色',
      nzContent: tpl,
      nzOnOk: () => {
        this.loading = true;
        this.http.post('/api/roles', this.formData).subscribe({
          next: () => {
            this.msg.success('创建成功');
            this.getData();
          },
          error: err => {
            this.loading = false;
            this.msg.error(err.message || '创建失败');
            this.cdr.detectChanges();
          }
        });
      }
    });
  }

  edit(tpl: TemplateRef<unknown>, item: any): void {
    this.formData = { ...item };
    this.modalSrv.create({
      nzTitle: '编辑角色',
      nzContent: tpl,
      nzOnOk: () => {
        this.loading = true;
        this.http.put(`/api/roles/${item.id}`, this.formData).subscribe({
          next: () => {
            this.msg.success('更新成功');
            this.getData();
          },
          error: err => {
            this.loading = false;
            this.msg.error(err.message || '更新失败');
            this.cdr.detectChanges();
          }
        });
      }
    });
  }

  deleteRole(item: any): void {
    this.modalSrv.confirm({
      nzTitle: '确定要删除此角色吗？',
      nzContent: '删除后不可恢复',
      nzOkText: '确定',
      nzCancelText: '取消',
      nzOnOk: () => {
        this.http.delete(`/api/roles/${item.id}`).subscribe({
          next: () => {
            this.msg.success('删除成功');
            this.getData();
          },
          error: err => {
            this.loading = false;
            this.msg.error(err.message || '删除失败');
            this.cdr.detectChanges();
          }
        });
      }
    });
  }

  reset(): void {
    this.q = {
      page: 1,
      page_size: 10,
      status: null,
      keyword: ''
    };
    this.getData();
  }

  setPermissions(role: any): void {
    this.selectedRole = role;
    this.loading = true;

    // 获取所有权限列表
    this.http.get('/api/permissions').subscribe({
      next: (res: any) => {
        if (res.success) {
          this.permissionTreeData = this.buildPermissionTree(res.data || []);
          // 获取角色已有权限
          this.http.get(`/api/roles/${role.id}/permissions`).subscribe({
            next: (permRes: any) => {
              if (permRes.success) {
                this.checkedKeys = permRes.data.map((p: any) => p.permission_code);
                this.modalSrv.create({
                  nzTitle: `设置权限 - ${role.role_name}`,
                  nzContent: this.permissionModal,
                  nzWidth: 800,
                  nzOnOk: () => {
                    this.savePermissions();
                  }
                });
              }
              this.loading = false;
              this.cdr.detectChanges();
            },
            error: err => {
              this.loading = false;
              this.msg.error(err.message || '获取角色权限失败');
              this.cdr.detectChanges();
            }
          });
        }
      },
      error: err => {
        this.loading = false;
        this.msg.error(err.message || '获取权限列表失败');
        this.cdr.detectChanges();
      }
    });
  }

  savePermissions(): void {
    if (!this.selectedRole) return;

    this.loading = true;
    this.http
      .post(`/api/roles/${this.selectedRole.id}/permissions`, {
        permission_codes: this.checkedKeys
      })
      .subscribe({
        next: () => {
          this.msg.success('权限设置成功');
          this.loading = false;
          this.cdr.detectChanges();
        },
        error: err => {
          this.loading = false;
          this.msg.error(err.message || '权限设置失败');
          this.cdr.detectChanges();
        }
      });
  }

  private buildPermissionTree(permissions: any[]): any[] {
    const tree: any[] = [];
    const map = new Map<string, any>();

    // 先创建所有节点的映射
    permissions.forEach(perm => {
      map.set(perm.permission_code, {
        title: perm.permission_name,
        key: perm.permission_code,
        children: []
      });
    });

    // 构建树形结构
    permissions.forEach(perm => {
      const node = map.get(perm.permission_code);
      if (perm.parent_code && map.has(perm.parent_code)) {
        const parent = map.get(perm.parent_code);
        parent.children.push(node);
      } else {
        tree.push(node);
      }
    });

    return tree;
  }
}
