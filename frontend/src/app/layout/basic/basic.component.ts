import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SettingsService, User } from '@delon/theme';
import { LayoutDefaultModule, LayoutDefaultOptions } from '@delon/theme/layout-default';
import { SettingDrawerModule } from '@delon/theme/setting-drawer';
import { ThemeBtnComponent } from '@delon/theme/theme-btn';
import { environment } from '@env/environment';

import { NzDropDownModule } from 'ng-zorro-antd/dropdown';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMenuModule } from 'ng-zorro-antd/menu';

import { HeaderClearStorageComponent } from './widgets/clear-storage.component';
import { HeaderFullScreenComponent } from './widgets/fullscreen.component';
import { HeaderNotifyComponent } from './widgets/notify.component';
import { HeaderSearchComponent } from './widgets/search.component';
import { HeaderUserComponent } from './widgets/user.component';

@Component({
  selector: 'layout-basic',
  template: `
    <layout-default [options]="options" [content]="contentTpl" [customError]="null">
      <layout-default-header-item direction="left" hidden="pc">
        <div layout-default-header-item-trigger (click)="searchToggleStatus = !searchToggleStatus">
          <nz-icon nzType="search" />
        </div>
      </layout-default-header-item>
      <layout-default-header-item direction="middle">
        <header-search class="alain-default__search" [(toggleChange)]="searchToggleStatus" />
      </layout-default-header-item>
      <layout-default-header-item direction="right">
        <header-notify />
      </layout-default-header-item>
      <layout-default-header-item direction="right" hidden="mobile">
        <div layout-default-header-item-trigger nz-dropdown [nzDropdownMenu]="settingsMenu" nzTrigger="click" nzPlacement="bottomRight">
          <nz-icon nzType="setting" />
        </div>
        <nz-dropdown-menu #settingsMenu="nzDropdownMenu">
          <div nz-menu style="width: 200px;">
            <div nz-menu-item>
              <header-fullscreen />
            </div>
            <div nz-menu-item>
              <header-clear-storage />
            </div>
            <li nz-menu-divider></li>
            <div nz-menu-item>
              <span style="padding: 8px 12px; color: #666; font-size: 12px;">系统版本：{{ appVersion }}</span>
            </div>
          </div>
        </nz-dropdown-menu>
      </layout-default-header-item>
      <layout-default-header-item direction="right">
                <header-user />
      </layout-default-header-item>

      <ng-template #contentTpl>
        <router-outlet />
      </ng-template>
    </layout-default>

    @if (showSettingDrawer) {
      <setting-drawer />
    }

    <theme-btn />
  `,
  imports: [
    RouterOutlet,
    LayoutDefaultModule,
    SettingDrawerModule,
    ThemeBtnComponent,
    NzIconModule,
    NzMenuModule,
    NzDropDownModule,
    HeaderSearchComponent,
    HeaderNotifyComponent,
    HeaderClearStorageComponent,
    HeaderFullScreenComponent,
    HeaderUserComponent
  ]
})
export class LayoutBasicComponent {
  private readonly settings = inject(SettingsService);

  options: LayoutDefaultOptions = {
    logoExpanded: `./assets/logo-full.svg`,
    logoCollapsed: `./assets/logo.svg`
  };

  searchToggleStatus = false;
  showSettingDrawer = !environment.production;
  appVersion = '1.0.0';

  get user(): User {
    return this.settings.user;
  }

  constructor() {
    // 使用ng-alain推荐的布局配置
    this.settings.setLayout('collapsed', false);
    this.settings.setLayout('collapsedWidth', 64);
    this.settings.setLayout('siderWidth', 200);
    this.settings.setLayout('fixedHeader', true);
    this.settings.setLayout('fixedSidebar', true);
    this.settings.setLayout('colorWeak', false);
  }

  logout(): void {
    // 实现退出登录逻辑
    localStorage.removeItem('token');
    window.location.href = '/passport/login';
  }
}
