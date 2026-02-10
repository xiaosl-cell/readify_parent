/**
 * 主应用程序入口
 * 负责初始化整个应用
 */

const App = {
    router: null,

    /**
     * 初始化应用
     */
    init: async function() {
        console.log('Readify Eval Flow - 应用启动');
        
        // 预加载模态框模板
        await this.preloadModals();
        
        // 初始化路由
        this.router = new Router();
        this.router.init();
        
        // 可以在这里添加其他全局初始化逻辑
        this.setupGlobalErrorHandler();
        this.checkAPIHealth();
    },

    /**
     * 预加载模态框模板
     */
    preloadModals: async function() {
        try {
            // 清除缓存（开发时使用，生产环境可以移除）
            // TemplateLoader.clearCache();
            
            // 加载所有模态框到页面中
            await TemplateLoader.appendTo('modals/ai-model-modal.html', 'modal-container');
            await TemplateLoader.appendTo('modals/ai-model-test-modal.html', 'modal-container');
            await TemplateLoader.appendTo('modals/prompt-template-modal.html', 'modal-container');
            await TemplateLoader.appendTo('modals/prompt-use-case-modal.html', 'modal-container');
            await TemplateLoader.appendTo('modals/system-config-modal.html', 'modal-container');
            await TemplateLoader.appendTo('modals/example-modal.html', 'modal-container');
            // 测试任务模态框不在这里预加载，因为它包含动态内容，会在需要时加载
            console.log('模态框模板加载完成');
        } catch (error) {
            console.error('模态框模板加载失败:', error);
        }
    },

    /**
     * 设置全局错误处理
     */
    setupGlobalErrorHandler: function() {
        window.addEventListener('error', function(event) {
            console.error('全局错误:', event.error);
        });

        window.addEventListener('unhandledrejection', function(event) {
            console.error('未处理的Promise拒绝:', event.reason);
        });
    },

    /**
     * 检查API健康状态
     */
    checkAPIHealth: async function() {
        try {
            await ApiService.health.check();
            console.log('API健康检查通过');
        } catch (error) {
            console.warn('API健康检查失败:', error.message);
            console.warn('请确保后端服务正在运行');
        }
    }
};

// 文档加载完成后初始化应用
$(document).ready(function() {
    App.init();
});
