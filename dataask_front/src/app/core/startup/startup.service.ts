import { HttpClient } from '@angular/common/http';
import { APP_INITIALIZER, Injectable, Provider, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ACLService } from '@delon/acl';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { MenuService, SettingsService, TitleService } from '@delon/theme';
import { Observable, of, catchError, map } from 'rxjs';

/**
 * Used for application startup
 * Generally used to get the basic data of the application, like: Menu Data, User Data, etc.
 */
export function provideStartup(): Provider[] {
  return [
    StartupService,
    {
      provide: APP_INITIALIZER,
      useFactory: (startupService: StartupService) => () => startupService.load(),
      deps: [StartupService],
      multi: true
    }
  ];
}

@Injectable()
export class StartupService {
  private menuService = inject(MenuService);
  private settingService = inject(SettingsService);
  private tokenService = inject(DA_SERVICE_TOKEN);
  private aclService = inject(ACLService);
  private titleService = inject(TitleService);
  private httpClient = inject(HttpClient);
  private router = inject(Router);

  private viaHttp(): Observable<void> {
    const tokenData = this.tokenService.get();
    
    // 设置应用基础信息
    const app = {
      name: '百惟数问',
      description: '问数，洞见随心'
    };
    this.settingService.setApp(app);
    this.titleService.suffix = app.name;

    // 如果没有token，直接返回
    if (!tokenData?.token) {
      // 清空用户信息和菜单
      this.settingService.setUser(null);
      this.menuService.clear();
      this.aclService.setAbility([]);
      
      // 如果当前不在登录页，跳转到登录页
      if (!this.router.url.includes('/passport/login')) {
        this.router.navigateByUrl(this.tokenService.login_url!);
      }
      return of(void 0);
    }

    // 有token才获取用户信息
    return this.httpClient.get('/api/user/info').pipe(
      map((res: any) => {
        if (!res.success) {
          throw new Error(res.error || '获取用户信息失败');
        }
        
        // 设置用户信息
        const user = {
          id: res.data.user.id,
          name: res.data.user.username,
          avatar: res.data.user.avatar || './assets/tmp/img/avatar.jpg',
          email: res.data.user.email || '',
          token: tokenData?.token || ''
        };
        this.settingService.setUser(user);
        
        // 设置权限
        if (res.data.user.permissions) {
          this.aclService.setAbility(res.data.user.permissions);
        } else {
          this.aclService.setFull(true);
        }
        
        // 转换菜单数据格式
        const menus = this.transformMenuData(res.data.menus);
        
        // 设置菜单
        this.menuService.add([
          {
            text: '主导航',
            group: true,
            children: menus
          }
        ]);

        return void 0;
      }),
      catchError(error => {
        console.error('获取用户信息失败:', error);
        // 清空用户信息和菜单
        this.settingService.setUser(null);
        this.menuService.clear();
        this.aclService.setAbility([]);
        
        // 跳转到登录页
        this.router.navigateByUrl(this.tokenService.login_url!);
        return of(void 0);
      })
    );
  }

  private transformMenuData(menus: any[]): any[] {
    return menus.map(menu => {
      const result: any = {
        text: menu.name,
        icon: menu.icon ? { type: 'icon', value: menu.icon } : undefined
      };

      // 处理链接
      if (menu.type === 'M') {
        // 目录类型
        result.group = true;
      } else if (menu.type === 'C') {
        // 菜单类型
        result.link = menu.path;
      }

      // 处理子菜单
      if (menu.children && menu.children.length > 0) {
        result.children = this.transformMenuData(menu.children);
      }

      return result;
    });
  }

  load(): Observable<void> {
    return this.viaHttp();
  }
}
