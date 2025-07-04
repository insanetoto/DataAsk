/**
 * For more configuration, please refer to https://angular.io/guide/build#proxying-to-a-backend-server
 *
 * 更多配置描述请参考 https://angular.cn/guide/build#proxying-to-a-backend-server
 *
 * Note: The proxy is only valid for real requests, Mock does not actually generate requests, so the priority of Mock will be higher than the proxy
 */
module.exports = {
  /**
   * The following means that all requests are directed to the backend `http://localhost:9000`
   */
  '/api': {
    target: 'http://localhost:9000',
    secure: false,
    changeOrigin: true
  },
  '/app': {
    target: 'http://localhost:9000',
    secure: false,
    changeOrigin: true
  },
  '/auth': {
    target: 'http://localhost:9000',
    secure: false,
    changeOrigin: true
  }
};
