/**
 * 路由管理器
 * 负责页面导航和组件切换
 */

class Router {
    constructor() {
        this.currentPage = null;
        this.currentComponent = null;
        this.routes = {
            'ai-models': AIModelManagement,
            'prompt-templates': PromptTemplateManagement,
            'prompt-use-cases': PromptUseCaseManagement,
            'system-configs': SystemConfigManagement,
            'examples': ExampleManagement,
            'test-tasks': TestTaskManagement,
            'evaluations': EvaluationManagement,
        };
    }

    /**
     * 初始化路由
     */
    init() {
        this.bindEvents();
        this.navigate('ai-models'); // 默认页面
    }

    /**
     * 绑定导航事件
     */
    bindEvents() {
        const self = this;
        
        // 导航菜单点击
        $('.navbar-nav .nav-link').on('click', async function(e) {
            e.preventDefault();
            
            const page = $(this).data('page');
            
            // 更新导航菜单状态
            $('.navbar-nav .nav-link').removeClass('active');
            $(this).addClass('active');
            
            // 导航到新页面
            await self.navigate(page);
        });
    }

    /**
     * 导航到指定页面
     * @param {string} page - 页面标识
     */
    async navigate(page) {
        // 如果是当前页面，不重复加载
        if (this.currentPage === page && this.currentComponent) {
            return;
        }

        // 销毁当前组件
        if (this.currentComponent && typeof this.currentComponent.destroy === 'function') {
            this.currentComponent.destroy();
        }

        // 获取页面组件类
        const ComponentClass = this.routes[page];
        
        if (ComponentClass) {
            // 创建新组件实例
            this.currentComponent = new ComponentClass();
            await this.currentComponent.init();
            this.currentPage = page;
        } else {
            // 显示404页面
            this.show404();
        }
    }

    /**
     * 显示404页面
     */
    show404() {
        $('#content-area').html(`
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>页面未找到</h3>
                <p>您访问的页面不存在</p>
            </div>
        `);
        this.currentPage = null;
        this.currentComponent = null;
    }

    /**
     * 注册新路由
     * @param {string} path - 路由路径
     * @param {Class} component - 组件类
     */
    registerRoute(path, component) {
        this.routes[path] = component;
    }
}

