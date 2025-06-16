import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { GlobalFooterModule } from '@delon/abc/global-footer';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { NzIconModule } from 'ng-zorro-antd/icon';

@Component({
  selector: 'layout-passport',
  template: `
    <div class="container">
      <div class="wrap">
        <div class="top">
          <div class="head">
            <img class="logo" src="./assets/logo-color.svg" />
            <span class="title">百惟智问</span>
          </div>
          <div class="desc">问数，洞见随心</div>
        </div>
        <router-outlet />
        <global-footer [links]="links">
          Copyright
          <i class="anticon anticon-copyright"></i> 2025
          <a href="//www.sinowaycn.com" target="_blank">中科百惟</a>
        </global-footer>
      </div>
    </div>
  `,
  styleUrls: ['./passport.component.less'],
  imports: [RouterOutlet, GlobalFooterModule, NzIconModule]
})
export class LayoutPassportComponent implements OnInit {
  private tokenService = inject(DA_SERVICE_TOKEN);

  links = [
    {
      title: '帮助',
      href: ''
    },
    {
      title: '隐私',
      href: ''
    },
    {
      title: '条款',
      href: ''
    }
  ];

  ngOnInit(): void {
    this.tokenService.clear();
  }
}
