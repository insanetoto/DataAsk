import { ChangeDetectionStrategy, Component, HostListener, inject } from '@angular/core';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';

@Component({
  selector: 'header-clear-storage',
  template: `
    <i nz-icon nzType="tool"></i>
    清除缓存
  `,
  host: {
    '[class.flex-1]': 'true'
  },
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NzIconModule]
})
export class HeaderClearStorageComponent {
  private readonly modalSrv = inject(NzModalService);
  private readonly messageSrv = inject(NzMessageService);

  @HostListener('click')
  _click(): void {
    this.modalSrv.confirm({
      nzTitle: '确认清除所有本地存储吗？',
      nzOnOk: () => {
        localStorage.clear();
        this.messageSrv.success('清除完成！');
      }
    });
  }
}
