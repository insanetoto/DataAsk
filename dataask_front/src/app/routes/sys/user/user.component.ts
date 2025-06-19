import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzBadgeModule } from 'ng-zorro-antd/badge';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { NzSwitchModule } from 'ng-zorro-antd/switch';
import { map, tap } from 'rxjs';

@Component({
  selector: 'app-sys-user',
  templateUrl: './user.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [...SHARED_IMPORTS, NzBadgeModule, NzSwitchModule, FormsModule],
  standalone: true
})
export class SysUserComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);

  @ViewChild('modalContent')
  modalContent!: TemplateRef<unknown>;

  @ViewChild('st', { static: false })
  st!: STComponent;

  q = {
    page: 1,
    page_size: 10,
    status: null as number | null,
    org_code: '',
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
    { title: '用户名', index: 'username' },
    { title: '姓名', index: 'real_name' },
    { title: '所属机构', index: 'org_name' },
    { title: '手机号', index: 'phone' },
    { title: '邮箱', index: 'email' },
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
          text: '删除',
          click: (item: any) => this.deleteUser(item)
        }
      ]
    }
  ];

  selectedRows: STData[] = [];
  formData = {
    username: '',
    password: '',
    real_name: '',
    org_code: '',
    phone: '',
    email: '',
    status: 1
  };
  expandForm = false;

  ngOnInit(): void {
    this.getData();
  }

  getData(): void {
    this.loading = true;
    this.http
      .get('/api/users', {
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
      username: '',
      password: '',
      real_name: '',
      org_code: '',
      phone: '',
      email: '',
      status: 1
    };
    this.modalSrv.create({
      nzTitle: '新建用户',
      nzContent: tpl,
      nzOnOk: () => {
        this.loading = true;
        this.http.post('/api/users', this.formData).subscribe({
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
      nzTitle: '编辑用户',
      nzContent: tpl,
      nzOnOk: () => {
        this.loading = true;
        this.http.put(`/api/users/${item.id}`, this.formData).subscribe({
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

  deleteUser(item: any): void {
    this.modalSrv.confirm({
      nzTitle: '确定要删除此用户吗？',
      nzContent: '删除后不可恢复',
      nzOkText: '确定',
      nzCancelText: '取消',
      nzOnOk: () => {
        this.http.delete(`/api/users/${item.id}`).subscribe({
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
      org_code: '',
      keyword: ''
    };
    this.getData();
  }
} 