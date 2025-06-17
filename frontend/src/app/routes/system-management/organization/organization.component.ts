import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzBadgeModule } from 'ng-zorro-antd/badge';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { NzTreeSelectModule } from 'ng-zorro-antd/tree-select';
import { map, tap } from 'rxjs';

@Component({
  selector: 'app-organization',
  template: `
    <page-header title="机构管理" [autoBreadcrumb]="true" />
    <nz-card [nzBordered]="false">
      <form nz-form [nzLayout]="'inline'" (ngSubmit)="getData()" class="search__form">
        <div nz-row [nzGutter]="{ xs: 8, sm: 8, md: 8, lg: 24, xl: 48, xxl: 48 }">
          <div nz-col nzMd="6" nzSm="24">
            <nz-form-item>
              <nz-form-label nzFor="search_orgCode">机构代码</nz-form-label>
              <nz-form-control>
                <input nz-input [(ngModel)]="q.orgCode" name="orgCode" placeholder="请输入" id="search_orgCode" />
              </nz-form-control>
            </nz-form-item>
          </div>
          <div nz-col nzMd="6" nzSm="24">
            <nz-form-item>
              <nz-form-label nzFor="search_orgName">机构名称</nz-form-label>
              <nz-form-control>
                <input nz-input [(ngModel)]="q.orgName" name="orgName" placeholder="请输入" id="search_orgName" />
              </nz-form-control>
            </nz-form-item>
          </div>
          <div nz-col nzMd="6" nzSm="24">
            <nz-form-item>
              <nz-form-label nzFor="search_status">状态</nz-form-label>
              <nz-form-control>
                <nz-select [(ngModel)]="q.status" name="status" id="search_status" [nzPlaceHolder]="'请选择'" [nzShowSearch]="true">
                  @for (i of status; track $index) {
                    <nz-option [nzLabel]="i.text" [nzValue]="i.value" />
                  }
                </nz-select>
              </nz-form-control>
            </nz-form-item>
          </div>
          <div nz-col nzMd="6" nzSm="24" class="text-right">
            <button nz-button (click)="add(modalContent)" [nzType]="'primary'" class="mr-sm">
              <i nz-icon nzType="plus"></i>
              <span>新建</span>
            </button>
            <button nz-button type="submit" [nzType]="'primary'" [nzLoading]="loading" class="mr-sm">查询</button>
            <button nz-button type="reset" (click)="reset()">重置</button>
          </div>
        </div>
      </form>
      @if (selectedRows.length > 0) {
        <div class="mb-md">
          <button nz-button nz-dropdown [nzDropdownMenu]="batchMenu" nzPlacement="bottomLeft" class="mx-sm">
            批量操作
            <i nz-icon nzType="down"></i>
          </button>
          <nz-dropdown-menu #batchMenu="nzDropdownMenu">
            <ul nz-menu>
              <li nz-menu-item (click)="remove()">删除</li>
              <li nz-menu-item (click)="disable()">禁用</li>
              <li nz-menu-item (click)="enable()">启用</li>
            </ul>
          </nz-dropdown-menu>
        </div>
      }
      @if (selectedRows.length > 0) {
        <div class="mb-md">
          <nz-alert [nzType]="'info'" [nzShowIcon]="true" [nzMessage]="message">
            <ng-template #message>
              已选择
              <strong class="text-primary">{{ selectedRows.length }}</strong> 项
              <a (click)="st.clearCheck()" class="ml-lg">清空</a>
            </ng-template>
          </nz-alert>
        </div>
      }
      <st #st [columns]="columns" [data]="data" [loading]="loading" (change)="stChange($event)">
        <ng-template st-row="status" let-i>
          <nz-badge [nzStatus]="i.statusType" [nzText]="i.statusText" />
        </ng-template>
      </st>
    </nz-card>
    <ng-template #modalContent>
      <form nz-form #f="ngForm">
        <nz-form-item>
          <nz-form-label nzRequired nzFor="form_orgCode">机构代码</nz-form-label>
          <nz-form-control>
            <input nz-input [(ngModel)]="form.orgCode" name="orgCode" required placeholder="请输入" id="form_orgCode" />
          </nz-form-control>
        </nz-form-item>
        <nz-form-item>
          <nz-form-label nzRequired nzFor="form_orgName">机构名称</nz-form-label>
          <nz-form-control>
            <input nz-input [(ngModel)]="form.orgName" name="orgName" required placeholder="请输入" id="form_orgName" />
          </nz-form-control>
        </nz-form-item>
        <nz-form-item>
          <nz-form-label nzFor="form_parentCode">上级机构</nz-form-label>
          <nz-form-control>
            <nz-tree-select
              [(ngModel)]="form.parentCode"
              name="parentCode"
              id="form_parentCode"
              [nzNodes]="orgTree"
              nzShowSearch
              nzPlaceHolder="请选择"
              nzAllowClear>
            </nz-tree-select>
          </nz-form-control>
        </nz-form-item>
      </form>
    </ng-template>
  `,
  styles: [
    `
      .search__form {
        margin-bottom: 24px;
      }
      .mr-sm {
        margin-right: 8px;
      }
      :host ::ng-deep {
        .ant-form-item {
          margin-bottom: 16px;
        }
      }
    `
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [...SHARED_IMPORTS, NzBadgeModule, NzTreeSelectModule, PageHeaderModule]
})
export class OrganizationComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);

  q: {
    pi: number;
    ps: number;
    orgCode: string;
    orgName: string;
    status: string | null;
  } = {
    pi: 1,
    ps: 10,
    orgCode: '',
    orgName: '',
    status: null
  };

  status = [
    { text: '启用', value: '1', type: 'success' },
    { text: '禁用', value: '0', type: 'error' }
  ];

  data: any[] = [];
  loading = false;
  selectedRows: STData[] = [];
  orgTree: any[] = [];

  form: any = {};

  @ViewChild('st', { static: true })
  st!: STComponent;

  @ViewChild('modalContent')
  modalContent!: TemplateRef<unknown>;

  columns: STColumn[] = [
    { title: '', index: 'id', type: 'checkbox' },
    { title: '机构代码', index: 'org_code' },
    { title: '机构名称', index: 'org_name' },
    { title: '上级机构', index: 'parent_org_code' },
    {
      title: '状态',
      index: 'status',
      render: 'status',
      filter: {
        menus: this.status,
        fn: (filter, record) => record.status === filter['value']
      }
    },
    {
      title: '创建时间',
      index: 'created_at',
      type: 'date'
    },
    {
      title: '操作',
      buttons: [
        {
          text: '编辑',
          click: (item: any) => this.edit(item)
        },
        {
          text: '删除',
          click: (item: any) => this.remove(item.id)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
  }

  getData(): void {
    this.loading = true;
    const params = {
      page: this.q.pi,
      page_size: this.q.ps,
      status: this.q.status ? parseInt(this.q.status) : null,
      keyword: this.q.orgCode || this.q.orgName || null
    };

    this.http
      .get('/api/organizations', params)
      .pipe(
        map((res: any) => {
          if (res.success && res.data) {
            return {
              ...res.data.pagination,
              list: res.data.list.map((item: any) => ({
                ...item,
                statusType: item.status === 1 ? 'success' : 'error',
                statusText: item.status === 1 ? '启用' : '禁用'
              }))
            };
          }
          return { list: [] };
        }),
        tap(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe(
        res => {
          this.data = res.list;
          this.st.total = res.total;
          this.cdr.detectChanges();
        },
        () => {
          this.loading = false;
          this.msg.error('获取数据失败');
          this.cdr.detectChanges();
        }
      );
  }

  stChange(e: STChange): void {
    switch (e.type) {
      case 'checkbox':
        this.selectedRows = e.checkbox || [];
        this.cdr.detectChanges();
        break;
      case 'pi':
        this.q.pi = e.pi || 1;
        this.getData();
        break;
      case 'ps':
        this.q.ps = e.ps || 10;
        this.getData();
        break;
    }
  }

  reset(): void {
    this.q = {
      pi: 1,
      ps: 10,
      orgCode: '',
      orgName: '',
      status: null
    };
    this.getData();
  }

  add(tpl: TemplateRef<unknown>): void {
    this.form = {};
    this.modalSrv.create({
      nzTitle: '新建机构',
      nzContent: tpl,
      nzOnOk: () => {
        this.http.post('/api/organizations', this.form).subscribe(
          (res: any) => {
            if (res.success) {
              this.msg.success('创建成功');
              this.getData();
            } else {
              this.msg.error(res.error || '创建失败');
            }
          },
          () => {
            this.msg.error('创建失败');
          }
        );
      }
    });
  }

  edit(item: any): void {
    this.form = { ...item };
    this.modalSrv.create({
      nzTitle: '编辑机构',
      nzContent: this.modalContent,
      nzOnOk: () => {
        this.http.put(`/api/organizations/${item['id']}`, this.form).subscribe(
          (res: any) => {
            if (res.success) {
              this.msg.success('更新成功');
              this.getData();
            } else {
              this.msg.error(res.error || '更新失败');
            }
          },
          () => {
            this.msg.error('更新失败');
          }
        );
      }
    });
  }

  remove(ids?: string): void {
    const id = ids || this.selectedRows.map(i => i['id']).join(',');
    if (!id) return;

    this.modalSrv.confirm({
      nzTitle: '确定要删除吗？',
      nzContent: '删除后无法恢复',
      nzOkText: '确定',
      nzCancelText: '取消',
      nzOnOk: () => {
        this.http.delete(`/api/organizations/${id}`).subscribe(
          (res: any) => {
            if (res.success) {
              this.msg.success('删除成功');
              this.getData();
            } else {
              this.msg.error(res.error || '删除失败');
            }
          },
          () => {
            this.msg.error('删除失败');
          }
        );
      }
    });
  }

  disable(): void {
    if (!this.selectedRows.length) return;

    const ids = this.selectedRows.map(i => i['id']);
    this.http.put(`/api/organizations/${ids.join(',')}/status`, { status: 0 }).subscribe(
      (res: any) => {
        if (res.success) {
          this.msg.success('禁用成功');
          this.getData();
        } else {
          this.msg.error(res.error || '禁用失败');
        }
      },
      () => {
        this.msg.error('禁用失败');
      }
    );
  }

  enable(): void {
    if (!this.selectedRows.length) return;

    const ids = this.selectedRows.map(i => i['id']);
    this.http.put(`/api/organizations/${ids.join(',')}/status`, { status: 1 }).subscribe(
      (res: any) => {
        if (res.success) {
          this.msg.success('启用成功');
          this.getData();
        } else {
          this.msg.error(res.error || '启用失败');
        }
      },
      () => {
        this.msg.error('启用失败');
      }
    );
  }
} 