/**
 * 应用配置文件
 * 可根据不同环境修改配置
 */

const AppConfig = {
    /**
     * API 基础地址配置
     * 开发环境: http://localhost:8082/api/v1
     * 生产环境: 修改为实际的生产环境地址
     */
    API_BASE_URL: 'http://localhost:8082/api/v1',
    
    /**
     * 其他可配置项
     */
    // 请求超时时间（毫秒）
    REQUEST_TIMEOUT: 30000,
    
    // 分页默认每页条数
    DEFAULT_PAGE_SIZE: 10,
    
    // 是否启用调试模式
    DEBUG_MODE: true,
};
