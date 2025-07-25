import { APP_INITIALIZER, Injectable, Provider, inject } from '@angular/core';
import { ACLService } from '@delon/acl';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { MenuService, SettingsService, TitleService, _HttpClient } from '@delon/theme';
import { NzSafeAny } from 'ng-zorro-antd/core/types';
import { Observable, catchError, map, of } from 'rxjs';

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
  private aclService = inject(ACLService);
  private titleService = inject(TitleService);
  private httpClient = inject(_HttpClient);
  private tokenService = inject(DA_SERVICE_TOKEN);

  load(): Observable<void> {
    const defaultData = {
      app: {
        name: '洞察魔方',
        description: '百惟数问 - 智能数据问答系统'
      },
      user: null,
      menus: [],
      permissions: []
    };

    // 获取token
    const token = this.tokenService.get()?.token;
    if (!token) {
      return of(undefined);
    }

    // 获取应用数据
    return this.httpClient
      .get('/api/app/init', null, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      .pipe(
        catchError(error => {
          console.error('Failed to load app init data:', error);
          return of({ code: 200, data: defaultData });
        }),
        map((appData: NzSafeAny) => {
          if (appData.code !== 200) {
            console.error('App init response error:', appData);
            return;
          }

          // 设置应用数据
          const res = appData.data;

          // Application information: including site name, description, year
          this.settingService.setApp(res.app);

          // User information: including name, avatar, email address
          this.settingService.setUser(res.user);

          // ACL: 根据用户角色和权限配置访问控制
          this.configureACL(res.user, res.permissions, res.acl);

          // Menu data, https://ng-alain.com/theme/menu
          this.menuService.add(res.menus);

          // Can be set page suffix title, https://ng-alain.com/theme/title
          this.titleService.suffix = res.app.name;
        })
      );
  }

  /**
   * 配置ACL权限控制
   */
  private configureACL(user: any, permissions: any[], acl?: any): void {
    if (!user) {
      // 未登录用户，清除所有权限
      this.aclService.set({});
      return;
    }

    // 优先使用后端返回的完整ACL配置
    if (acl && acl.role && acl.ability) {
      this.aclService.set({
        role: acl.role,
        ability: acl.ability,
        mode: acl.mode || 'oneOf'
      });
      return;
    }

    // 降级到原有的基于角色的权限配置
    const roleCode = user.roleCode || user.role_code || user.role?.role_code;
    const roles: string[] = roleCode ? [roleCode] : [];
    const abilities: string[] = [];

    // 如果后端直接返回了权限数组，优先使用
    if (permissions && Array.isArray(permissions) && permissions.length > 0) {
      // 如果permissions是字符串数组（新的权限系统）
      if (typeof permissions[0] === 'string') {
        abilities.push(...permissions);
      } else {
        // 如果permissions是对象数组（旧的权限系统）
        permissions.forEach(permission => {
          if (permission.permission_code) {
            abilities.push(permission.permission_code);
          }
        });
      }
    } else {
      // 基于角色添加基础权限（降级处理）
      if (roleCode === 'SUPER_ADMIN') {
        abilities.push(
          'user.reset.password',
          'user.manage.org',
          'user.create',
          'user.edit',
          'user.delete',
          'user.view',
          'role.manage',
          'permission.manage',
          'org.manage',
          'workflow.manage',
          'message.manage'
        );
      } else if (roleCode === 'ORG_ADMIN') {
        abilities.push(
          'user.reset.password',
          'user.manage.org',
          'user.create',
          'user.edit',
          'user.delete',
          'user.view',
          'role.manage',
          'permission.manage',
          'org.manage',
          'workflow.manage',
          'message.manage'
        );
      } else if (roleCode === 'NORMAL_USER') {
        abilities.push('user.view');
      }
    }

    // 设置ACL权限
    this.aclService.set({
      role: roles,
      ability: abilities,
      mode: 'oneOf' as const
    });
  }
}
