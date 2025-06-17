/**
 * For more configuration, please refer to https://angular.io/guide/build#proxying-to-a-backend-server
 *
 * 更多配置描述请参考 https://angular.cn/guide/build#proxying-to-a-backend-server
 *
 * Note: The proxy is only valid for real requests, Mock does not actually generate requests, so the priority of Mock will be higher than the proxy
 */
module.exports = {
  /**
   * 将所有API请求代理到后端Flask服务器
   */
  '/api/*': {
    target: 'http://localhost:9000',
    secure: false, // 忽略无效的SSL证书
    changeOrigin: true,
    logLevel: 'debug'
  },
  '/chart': {
    target: 'http://localhost:9000',
    secure: false,
    changeOrigin: true,
    logLevel: 'debug',
    pathRewrite: {
      '^/chart': '/api/chart'
    }
  },
  '/notice': {
    target: 'http://localhost:9000',
    secure: false,
    changeOrigin: true,
    logLevel: 'debug',
    pathRewrite: {
      '^/notice': '/api/notice'
    }
  },
  '/activities': {
    target: 'http://localhost:9000',
    secure: false,
    changeOrigin: true,
    logLevel: 'debug',
    pathRewrite: {
      '^/activities': '/api/activities'
    }
  },
  '/login/*': {
    target: 'http://localhost:9000/api/v1',
    secure: false,
    changeOrigin: true,
    logLevel: 'debug'
  }
};
