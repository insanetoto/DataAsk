import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzToolTipModule } from 'ng-zorro-antd/tooltip';

@Component({
  selector: 'header-clear-storage',
  template: `<i nz-icon nzType="tool" nz-tooltip nzTooltipTitle="清除本地缓存" (click)="clear()"></i>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NzIconModule, NzToolTipModule]
})
export class HeaderClearStorageComponent {
  constructor(private msg: NzMessageService) {}

  clear(): void {
    localStorage.clear();
    this.msg.success('清除本地缓存成功');
  }
}
