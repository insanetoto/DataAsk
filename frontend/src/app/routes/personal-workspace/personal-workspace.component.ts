import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { G2RadarModule } from '@delon/chart/radar';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzAvatarModule } from 'ng-zorro-antd/avatar';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzGridModule } from 'ng-zorro-antd/grid';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzListModule } from 'ng-zorro-antd/list';
import { NzMessageService } from 'ng-zorro-antd/message';
import { zip } from 'rxjs';

@Component({
  selector: 'app-personal-workspace',
  templateUrl: './personal-workspace.component.html',
  styleUrls: ['./personal-workspace.component.less'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ...SHARED_IMPORTS,
    NzAvatarModule,
    NzBreadCrumbModule,
    NzButtonModule,
    NzCardModule,
    NzGridModule,
    NzIconModule,
    NzListModule,
    G2RadarModule
  ],
  standalone: true
})
export class PersonalWorkspaceComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);

  notice: any[] = [];
  activities: any[] = [];
  radarData!: any[];
  loading = true;

  links = [
    {
      title: '创建知识库',
      href: ''
    },
    {
      title: '训练模型',
      href: ''
    },
    {
      title: '数据导入',
      href: ''
    },
    {
      title: '系统设置',
      href: ''
    },
    {
      title: '用户管理',
      href: ''
    },
    {
      title: '权限配置',
      href: ''
    }
  ];

  members = [
    {
      id: 'members-1',
      title: 'AI研发组',
      logo: 'https://gw.alipayobjects.com/zos/rmsportal/WdGqmHpayyMjiEhcKoVE.png',
      link: ''
    },
    {
      id: 'members-2',
      title: '数据处理组',
      logo: 'https://gw.alipayobjects.com/zos/rmsportal/zOsKZmFRdUtvpqCImOVY.png',
      link: ''
    },
    {
      id: 'members-3',
      title: '产品设计组',
      logo: 'https://gw.alipayobjects.com/zos/rmsportal/dURIMkkrRFpPgTuzkwnB.png',
      link: ''
    },
    {
      id: 'members-4',
      title: '运维支持组',
      logo: 'https://gw.alipayobjects.com/zos/rmsportal/sfjbOqnsXXJgNCjCzDBL.png',
      link: ''
    },
    {
      id: 'members-5',
      title: '质量测试组',
      logo: 'https://gw.alipayobjects.com/zos/rmsportal/siCrBXXhmvTQGWPNLBow.png',
      link: ''
    }
  ];

  ngOnInit(): void {
    zip(this.http.get('/chart'), this.http.get('/notice'), this.http.get('/activities')).subscribe(
      ([chart, notice, activities]: [any, any, any]) => {
        this.radarData = chart.radarData;
        this.notice = notice;
        this.activities = activities.map((item: any) => {
          item.template = item.template.split(/@\{([^{}]*)\}/gi).map((key: string) => {
            if (item[key]) {
              return `<a>${item[key].name}</a>`;
            }
            return key;
          });
          return item;
        });
        this.loading = false;
        this.cdr.detectChanges();
      }
    );
  }
}
