// This file can be replaced during build by using the `fileReplacements` array.
// `ng build ---prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

import { Environment } from '@delon/theme';

export const environment = {
  production: false,
  useHash: true,
  api: {
    baseUrl: 'http://localhost:9000',
    refreshTokenEnabled: true,
    refreshTokenType: 'auth-refresh'
  }
} as Environment;
