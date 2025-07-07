import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, ViewChild, inject } from '@angular/core';
import { Router } from '@angular/router';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient, SettingsService } from '@delon/theme';
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
  private readonly router = inject(Router);
  private readonly settings = inject(SettingsService);

  // 查询参数
  q: OrganizationQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: 1, // 默认只显示有效机构
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
  selectedTreeNode = ''; // 选中的树节点机构编码

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

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    return this.currentUser?.role_code || '';
  }

  get currentUserOrgCode() {
    return this.currentUser?.org_code || '';
  }

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
      width: 240,
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
   * 刷新数据（供子组件调用）
   */
  refreshData(): void {
    console.log('刷新机构数据');
    this.getData();
  }

  /**
   * 获取机构列表数据
   */
  getData(): void {
    this.loading = true;
    const params = {
      pi: this.q.pi || 1,
      ps: this.q.ps || 10,
      keyword: this.q.keyword || '',
      status: this.q.status
    };

    this.orgService.getOrganizations(params).subscribe({
      next: res => {
        if (res.code === 200) {
          const responseData = res.data || {};
          this.data = responseData.list || responseData.items || [];

          // 更新查询参数中的分页信息
          this.q.pi = responseData.page || params.pi;
          this.q.ps = responseData.pageSize || params.ps;

          console.log('机构数据加载成功:', {
            total: responseData.total,
            currentPage: this.q.pi,
            pageSize: this.q.ps,
            dataCount: this.data.length
          });
        } else {
          this.msg.error(res.message || '获取机构数据失败');
          this.data = [];
        }
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: error => {
        console.error('获取机构数据失败:', error);
        // 检查是否是被HTTP拦截器误判的成功响应
        if (error.status === 200 && error.ok && error.body) {
          if (error.body.code === 200 && error.body.data) {
            const responseData = error.body.data;
            this.data = responseData.list || responseData.items || [];
            this.q.pi = responseData.page || params.pi;
            this.q.ps = responseData.pageSize || params.ps;
            console.log('机构数据加载成功(拦截器处理):', this.data.length);
            this.loading = false;
            this.cdr.detectChanges();
            return;
          }
        }
        
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
    const currentRole = this.currentUserRoleCode;
    const currentOrgCode = this.currentUserOrgCode;

    if (currentRole === 'SUPER_ADMIN') {
      // 超级管理员可以看到所有机构
      this.orgService.getOrganizations({ pi: 1, ps: 1000, status: 1 }).subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.parentOrgOptions = res.data?.list || res.data?.items || res.data || [];
          }
        },
        error: error => {
          console.error('加载上级机构选项失败:', error);
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              this.parentOrgOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
            }
          }
        }
      });
    } else if (currentOrgCode && this.currentUser?.org_name) {
      // 机构管理员和其他角色只能看到自己所属机构
      this.parentOrgOptions = [
        {
          id: this.currentUser.id || 0,
          org_code: currentOrgCode,
          org_name: this.currentUser.org_name,
          parent_org_code: this.currentUser.parent_org_code || '',
          level_depth: this.currentUser.level_depth || 0,
          contact_person: this.currentUser.contact_person || '',
          contact_phone: this.currentUser.contact_phone || '',
          contact_email: this.currentUser.contact_email || '',
          status: 1
        }
      ];
    } else {
      // 如果没有完整的用户信息，设置为空数组
      this.parentOrgOptions = [];
    }
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
    // 过滤掉状态为0（已删除）的机构
    const validOrgs = orgList.filter(org => org.status === 1);
    
    return validOrgs.map(org => ({
      title: `${org.org_name} (${org.org_code})`,
      key: org.org_code,
      expanded: true,
      isLeaf: !org.children || org.children.length === 0,
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
   * 树节点选择事件
   */
  onTreeNodeSelect(keys: string[], _event?: any): void {
    if (keys.length > 0) {
      this.selectedTreeNode = keys[0];
      console.log('选中机构:', this.selectedTreeNode);
      // 根据选中的机构过滤表格数据
      this.filterBySelectedOrg();
    } else {
      this.selectedTreeNode = '';
      // 显示所有数据
      this.getData();
    }
  }

  /**
   * 根据选中的机构过滤表格数据
   */
  filterBySelectedOrg(): void {
    if (!this.selectedTreeNode) {
      this.getData();
      return;
    }
    
    this.loading = true;
    const params = {
      pi: 1,
      ps: 1000, // 加载更多数据以便过滤
      keyword: this.q.keyword || '',
      status: 1 // 只获取有效机构
    };

    this.orgService.getOrganizations(params).subscribe({
      next: res => {
        if (res.code === 200) {
          const responseData = res.data || {};
          let allData = responseData.list || responseData.items || [];
          
          // 只显示选中的机构（不包含子机构，根据需求调整）
          this.data = allData.filter((org: Organization) => org.org_code === this.selectedTreeNode);

          console.log('过滤后的机构数据:', {
            selectedOrgCode: this.selectedTreeNode,
            filteredCount: this.data.length,
            originalDataCount: allData.length
          });
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
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * 检查是否为子机构
   */
  private isChildOrganization(org: Organization, parentOrgCode: string): boolean {
    // 简单的子机构判断：机构编码以父机构编码开头
    return org.org_code.startsWith(parentOrgCode) && org.org_code !== parentOrgCode;
  }

  /**
   * 新增机构
   */
  addOrg(): void {
    this.router.navigate(['/sys/org/edit/new']);
  }

  /**
   * 查看机构
   */
  viewOrg(item: Organization): void {
    if (item.id) {
      this.router.navigate(['/sys/org/view', item.id]);
    } else {
      this.msg.error('机构ID不存在');
    }
  }

  /**
   * 编辑机构
   */
  editOrg(item: Organization): void {
    if (item.id) {
      this.router.navigate(['/sys/org/edit', item.id]);
    } else {
      this.msg.error('机构ID不存在');
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
            // 兼容两种响应格式：{success: true} 或 {code: 200}
            const isSuccess = res.success === true || res.code === 200;
            const errorMessage = res.error || res.message;
            
            if (isSuccess) {
              this.msg.success(res.message || '删除成功');
              this.getData();
            } else {
              this.msg.error(errorMessage || '删除失败');
            }
          },
          error: error => {
            console.error('删除机构失败:', error);
            // 检查是否是被HTTP拦截器误判的成功响应
            if (error.status === 200 && error.ok && error.body) {
              const isSuccess = error.body.success === true || error.body.code === 200;
              if (isSuccess) {
                this.msg.success(error.body.message || '删除成功');
                this.getData();
                return;
              }
            }
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

        // 使用 Promise.all 处理批量删除
        Promise.all(deletePromises.map(p => p.toPromise()))
          .then((results) => {
            // 检查所有删除结果
            const successCount = results.filter(res => 
              res.success === true || res.code === 200
            ).length;
            
            if (successCount === results.length) {
              this.msg.success('批量删除成功');
            } else {
              this.msg.warning(`成功删除 ${successCount}/${results.length} 个机构`);
            }
            
            this.getData();
            this.st.clearCheck();
          })
          .catch((error) => {
            console.error('批量删除失败:', error);
            this.msg.error('批量删除失败');
          });
      }
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
