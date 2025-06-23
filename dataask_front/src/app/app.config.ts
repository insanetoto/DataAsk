import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, EnvironmentProviders, Provider } from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import {
  provideRouter,
  withComponentInputBinding,
  withViewTransitions,
  withInMemoryScrolling,
  withHashLocation,
  RouterFeatures
} from '@angular/router';
import { defaultInterceptor, provideStartup } from '@core';
import { provideCellWidgets } from '@delon/abc/cell';
import { provideSTWidgets } from '@delon/abc/st';
import { authSimpleInterceptor, provideAuth } from '@delon/auth';
import { provideSFConfig } from '@delon/form';
import { provideAlain } from '@delon/theme';
import { AlainConfig } from '@delon/util/config';
import { environment } from '@env/environment';
import { CELL_WIDGETS, ST_WIDGETS, SF_WIDGETS } from '@shared';
import { NzConfig, provideNzConfig } from 'ng-zorro-antd/core/config';

import { ICONS } from '../style-icons';
import { ICONS_AUTO } from '../style-icons-auto';
import { provideBindAuthRefresh } from './core/net';
import { routes } from './routes/routes';

const alainConfig: AlainConfig = {
  auth: {
    login_url: '/passport/login',
    ignores: [
      /\/assets\//, // 忽略静态资源
      /\/tmp\//, // 忽略临时资源
      /\.(png|jpg|ico|gif|svg|css|js|ttf|woff|woff2)$/ // 忽略静态文件格式
    ]
  }
};

const ngZorroConfig: NzConfig = {};

const routerFeatures: RouterFeatures[] = [
  withComponentInputBinding(),
  withViewTransitions(),
  withInMemoryScrolling({ scrollPositionRestoration: 'top' })
];
if (environment.useHash) routerFeatures.push(withHashLocation());

const providers: Array<Provider | EnvironmentProviders> = [
  provideHttpClient(withInterceptors([...(environment.interceptorFns ?? []), authSimpleInterceptor, defaultInterceptor])),
  provideAnimations(),
  provideRouter(routes, ...routerFeatures),
  provideAlain({ config: alainConfig, icons: [...ICONS_AUTO, ...ICONS] }),
  provideNzConfig(ngZorroConfig),
  provideAuth(),
  provideCellWidgets(...CELL_WIDGETS),
  provideSTWidgets(...ST_WIDGETS),
  provideSFConfig({
    widgets: [...SF_WIDGETS]
  }),
  provideStartup(),
  ...(environment.providers || [])
];

// If you use `@delon/auth` to refresh the token, additional registration `provideBindAuthRefresh` is required
if (environment.api?.refreshTokenEnabled && environment.api.refreshTokenType === 'auth-refresh') {
  providers.push(provideBindAuthRefresh());
}

export const appConfig: ApplicationConfig = {
  providers: providers
};
