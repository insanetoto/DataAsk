import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzToolTipModule } from 'ng-zorro-antd/tooltip';
import screenfull from 'screenfull';

@Component({
  selector: 'header-fullscreen',
  template: `
    <i
      nz-icon
      [nzType]="status ? 'fullscreen-exit' : 'fullscreen'"
      nz-tooltip
      [nzTooltipTitle]="status ? '退出全屏' : '全屏'"
      (click)="toggle()"
    ></i>
  `,
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NzIconModule, NzToolTipModule]
})
export class HeaderFullScreenComponent {
  status = false;

  toggle(): void {
    if (screenfull.isEnabled) {
      screenfull.toggle();
      this.status = !this.status;
    }
  }
}
