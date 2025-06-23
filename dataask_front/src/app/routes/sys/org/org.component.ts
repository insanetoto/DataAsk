import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { NzTreeNodeOptions } from 'ng-zorro-antd/tree';
import { finalize } from 'rxjs';

import { SysOrgService, Organization, OrganizationQuery } from './org.service';

@Component({
  selector: 'app-sys-org',
  templateUrl: './org.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: SHARED_IMPORTS
})
export class SysOrgComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly orgService = inject(SysOrgService);

  // 查询参数
  q: OrganizationQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: undefined,
    parent_org_code: ''
  };

  // 数据和状态
  data: Organization[] = [];
  loading = false;
  selectedRows: STData[] = [];
  expandForm = false;

  // 不再需要stReq和stRes配置，因为使用数据模式

  // 树形数据
  treeData: NzTreeNodeOptions[] = [];
  treeLoading = false;
  showTree = false;

  // 表单数据
  editingOrg: Partial<Organization> = {};
  isEditMode = false;
  modalTitle = '';

  // 上级机构选择
  parentOrgOptions: Organization[] = [];

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
      title: '机构编码',
      index: 'org_code',
      width: 120,
      sort: true
    },
    {
      title: '机构名称',
      index: 'org_name',
      width: 220,
      sort: true
    },
    {
      title: '负责人',
      index: 'contact_person',
      width: 120
    },
    {
      title: '联系电话',
      index: 'contact_phone',
      width: 120
    },
    {
      title: '联系邮箱',
      index: 'contact_email',
      width: 160
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
      width: 200,
      fixed: 'right',
      buttons: [
        {
          text: '查看',
          icon: 'eye',
          click: (item: Organization) => this.viewOrg(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          click: (item: Organization) => this.editOrg(item)
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: Organization) => this.deleteOrg(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
    this.loadParentOrgOptions();
  }

  /**
   * 获取机构列表数据
   */
  getData(): void {
    this.loading = true;
    const params = {
      pi: 1,
      ps: 10,
      keyword: this.q.keyword || '',
      status: this.q.status
    };

    this.orgService.getOrganizations(params).subscribe({
      next: res => {
        if (res.code === 200) {
          this.data = res.data?.list || res.data?.items || [];
        } else {
          this.msg.error(res.message || '获取机构数据失败');
          this.data = [];
        }
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: error => {
        console.error('获取机构数据失败:', error);
        this.msg.error('获取机构数据失败');
        this.data = [];
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * 加载上级机构选项
   */
  loadParentOrgOptions(): void {
    this.orgService.getOrganizations({ pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.parentOrgOptions = res.data?.list || res.data?.items || res.data || [];
        }
      },
      error: error => {
        console.error('加载上级机构选项失败:', error);

        // 检查是否是被HTTP拦截器误判的成功响应
        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.parentOrgOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
          }
        }
      }
    });
  }

  /**
   * 获取机构树形数据
   */
  getTreeData(): void {
    this.treeLoading = true;

    // 使用service方法，但改进错误处理
    this.orgService
      .getOrganizationTree()
      .pipe(
        finalize(() => {
          this.treeLoading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res: any) => {
          // 处理标准格式响应：{code: 200, data: [...]} 或 {success: true, data: [...]}
          if (res && (res.success === true || res.code === 200)) {
            const treeData = res.data || [];
            this.treeData = this.convertToTreeData(treeData);
            this.showTree = true;
          } else {
            this.msg.error(`获取树形数据失败：${res?.message || '未知错误'}`);
          }
        },
        error: error => {
          // 检查是否是被HTTP拦截器误判的成功响应
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              const treeData = error.body.data || [];
              this.treeData = this.convertToTreeData(treeData);
              this.showTree = true;
              return;
            }
          }

          // 只有真正的错误才显示错误信息
          console.error('获取树形数据失败:', error);
          this.msg.error('获取树形数据失败');
        }
      });
  }

  /**
   * 转换为树形数据格式
   */
  convertToTreeData(orgList: Organization[]): NzTreeNodeOptions[] {
    return orgList.map(org => ({
      title: `${org.org_name} (${org.org_code})`,
      key: org.org_code,
      expanded: true,
      children: org.children ? this.convertToTreeData(org.children) : []
    }));
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
    }
  }

  /**
   * 新增机构
   */
  addOrg(tpl: TemplateRef<unknown>): void {
    this.editingOrg = {
      status: 1
    };
    this.isEditMode = false;
    this.modalTitle = '新增机构';
    this.showModal(tpl);
  }

  /**
   * 查看机构
   */
  viewOrg(item: Organization): void {
    this.editingOrg = { ...item };
    this.isEditMode = false;
    this.modalTitle = '查看机构';
    // 这里可以显示一个只读的模态框
    this.msg.info(`查看机构: ${item.org_name}`);
  }

  /**
   * 编辑机构
   */
  editOrg(item: Organization, tpl?: TemplateRef<unknown>): void {
    this.editingOrg = { ...item };
    this.isEditMode = true;
    this.modalTitle = '编辑机构';
    if (tpl) {
      this.showModal(tpl);
    }
  }

  /**
   * 删除机构
   */
  deleteOrg(item: Organization): void {
    this.modalSrv.confirm({
      nzTitle: '确认删除',
      nzContent: `确定要删除机构 "${item.org_name}" 吗？`,
      nzOnOk: () => {
        return this.orgService.deleteOrganization(item.id!).subscribe({
          next: res => {
            if (res.success) {
              this.msg.success('删除成功');
              this.getData();
            } else {
              this.msg.error(res.error || '删除失败');
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
   * 批量删除
   */
  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的机构');
      return;
    }

    this.modalSrv.confirm({
      nzTitle: '确认批量删除',
      nzContent: `确定要删除选中的 ${this.selectedRows.length} 个机构吗？`,
      nzOnOk: () => {
        const deletePromises = this.selectedRows.map(row => this.orgService.deleteOrganization(row['id']));

        // 这里简化处理，实际应该使用 forkJoin
        Promise.all(deletePromises.map(p => p.toPromise()))
          .then(() => {
            this.msg.success('批量删除成功');
            this.getData();
            this.st.clearCheck();
          })
          .catch(() => {
            this.msg.error('批量删除失败');
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
        return this.saveOrg();
      }
    });
  }

  /**
   * 保存机构
   */
  saveOrg(): Promise<boolean> {
    return new Promise(resolve => {
      // 表单验证
      if (
        !this.editingOrg.org_code ||
        !this.editingOrg.org_name ||
        !this.editingOrg.contact_person ||
        !this.editingOrg.contact_phone ||
        !this.editingOrg.contact_email
      ) {
        this.msg.error('请填写完整信息');
        resolve(false);
        return;
      }

      const request = this.isEditMode
        ? this.orgService.updateOrganization(this.editingOrg.id!, this.editingOrg)
        : this.orgService.createOrganization(this.editingOrg);

      request.subscribe({
        next: res => {
          if (res.success) {
            this.msg.success(this.isEditMode ? '更新成功' : '创建成功');
            this.getData();
            resolve(true);
          } else {
            this.msg.error(res.error || '保存失败');
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
      parent_org_code: ''
    };
    setTimeout(() => this.getData());
  }

  /**
   * 切换树形视图
   */
  toggleTreeView(): void {
    if (!this.showTree) {
      this.getTreeData();
    } else {
      this.showTree = false;
    }
  }
}
