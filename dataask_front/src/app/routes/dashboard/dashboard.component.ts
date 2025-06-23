import { Platform } from '@angular/cdk/platform';
import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import type { Chart } from '@antv/g2';
import { OnboardingModule, OnboardingService } from '@delon/abc/onboarding';
import { QuickMenuModule } from '@delon/abc/quick-menu';
import { G2BarModule } from '@delon/chart/bar';
import { G2MiniBarModule } from '@delon/chart/mini-bar';
import { G2TimelineModule } from '@delon/chart/timeline';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { timer } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [...SHARED_IMPORTS, G2TimelineModule, G2BarModule, G2MiniBarModule, QuickMenuModule, OnboardingModule]
})
export class DashboardComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly obSrv = inject(OnboardingService);
  private readonly platform = inject(Platform);
  private readonly doc = inject(DOCUMENT);
  todoData = [
    {
      completed: true,
      avatar: '1',
      name: '苏先生',
      content: `请告诉我，我应该说点什么好？`
    },
    {
      completed: false,
      avatar: '2',
      name: 'はなさき',
      content: `ハルカソラトキヘダツヒカリ`
    },
    {
      completed: false,
      avatar: '3',
      name: 'cipchk',
      content: `this world was never meant for one as beautiful as you.`
    },
    {
      completed: false,
      avatar: '4',
      name: 'Kent',
      content: `my heart is beating with hers`
    },
    {
      completed: false,
      avatar: '5',
      name: 'Are you',
      content: `They always said that I love beautiful girl than my friends`
    },
    {
      completed: false,
      avatar: '6',
      name: 'Forever',
      content: `Walking through green fields ，sunshine in my eyes.`
    }
  ];

  webSite!: any[];
  salesData!: any[];
  offlineChartData!: any[];

  constructor() {
    timer(1000)
      .pipe(takeUntilDestroyed())
      .subscribe(() => this.genOnboarding());
  }

  fixDark(chart: Chart): void {
    if (!this.platform.isBrowser || (this.doc.body as HTMLBodyElement).getAttribute('data-theme') !== 'dark') return;

    chart.theme({
      styleSheet: {
        backgroundColor: 'transparent'
      }
    });
  }

  ngOnInit(): void {
    this.http.get('/api/chart', { responseType: 'json' }).subscribe({
      next: res => {
        const chartData = res.data || res;
        this.webSite = chartData.visitData?.slice(0, 10) || [];
        this.salesData = chartData.salesData || [];
        this.offlineChartData = chartData.offlineChartData || [];

        this.cdr.detectChanges();
      },
      error: error => {
        if (error.status === 200 && error.ok && error.body) {
          const chartData = error.body.data || error.body;
          this.webSite = chartData.visitData?.slice(0, 10) || [];
          this.salesData = chartData.salesData || [];
          this.offlineChartData = chartData.offlineChartData || [];
          this.cdr.detectChanges();
          return;
        }

        this.webSite = [];
        this.salesData = [];
        this.offlineChartData = [];
        this.cdr.detectChanges();
      }
    });
  }

  private genOnboarding(): void {
    const KEY = 'on-boarding';
    if (!this.platform.isBrowser || localStorage.getItem(KEY) === '1') {
      return;
    }

    this.http.get('./assets/tmp/on-boarding.json').subscribe({
      next: res => {
        this.obSrv.start(res);
        localStorage.setItem(KEY, '1');
      },
      error: error => {
        if (error.status === 200 && error.ok && error.body) {
          this.obSrv.start(error.body);
          localStorage.setItem(KEY, '1');
          return;
        }

        // 如果加载失败，不影响主要功能，只是跳过引导
      }
    });
  }
}
