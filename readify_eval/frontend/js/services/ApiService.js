/**
 * API 服务层
 * 封装所有后端API调用
 */

// 从配置文件读取 API 基础地址
const API_BASE_URL = AppConfig.API_BASE_URL;

const ApiService = {
    /**
     * 通用请求方法
     */
    request: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(`${API_BASE_URL}${url}`, config);
            
            // 处理204 No Content
            if (response.status === 204) {
                return { success: true };
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * AI模型相关API
     */
    aiModels: {
        // 获取AI模型列表
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/ai-models${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个AI模型
        getById: function(id) {
            return ApiService.request(`/ai-models/${id}`);
        },
        
        // 创建AI模型
        create: function(data) {
            return ApiService.request('/ai-models', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新AI模型
        update: function(id, data) {
            return ApiService.request(`/ai-models/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除AI模型
        delete: function(id) {
            return ApiService.request(`/ai-models/${id}`, {
                method: 'DELETE',
            });
        },
        
        // 调用大模型生成文本（通过后端中转，避免跨域问题）
        chatCompletion: function(modelId, data) {
            return ApiService.request(`/ai-models/${modelId}/chat`, {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
    },

    /**
     * 示例相关API
     */
    examples: {
        // 获取示例列表
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/examples${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个示例
        getById: function(id) {
            return ApiService.request(`/examples/${id}`);
        },
        
        // 创建示例
        create: function(data) {
            return ApiService.request('/examples', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新示例
        update: function(id, data) {
            return ApiService.request(`/examples/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除示例
        delete: function(id) {
            return ApiService.request(`/examples/${id}`, {
                method: 'DELETE',
            });
        },
    },

    /**
     * 提示词用例相关API
     */
    promptUseCases: {
        // 获取提示词用例列表（分页）
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/prompt-use-cases${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取所有提示词用例（不分页）
        getAllNoPagination: function() {
            return ApiService.request('/prompt-use-cases/all');
        },
        
        // 获取单个提示词用例
        getById: function(id) {
            return ApiService.request(`/prompt-use-cases/${id}`);
        },
        
        // 创建提示词用例
        create: function(data) {
            return ApiService.request('/prompt-use-cases', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新提示词用例
        update: function(id, data) {
            return ApiService.request(`/prompt-use-cases/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除提示词用例
        delete: function(id) {
            return ApiService.request(`/prompt-use-cases/${id}`, {
                method: 'DELETE',
            });
        },
    },

    /**
     * 提示词模板相关API
     */
    promptTemplates: {
        // 获取提示词模板列表（分页）
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/prompt-templates${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取所有提示词模板（不分页）
        getAllNoPagination: function() {
            return ApiService.request('/prompt-templates/all');
        },
        
        // 获取单个提示词模板
        getById: function(id) {
            return ApiService.request(`/prompt-templates/${id}`);
        },
        
        // 创建提示词模板
        create: function(data) {
            return ApiService.request('/prompt-templates', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新提示词模板
        update: function(id, data) {
            return ApiService.request(`/prompt-templates/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除提示词模板
        delete: function(id) {
            return ApiService.request(`/prompt-templates/${id}`, {
                method: 'DELETE',
            });
        },
    },

    /**
     * 系统配置相关API
     */
    systemConfigs: {
        // 获取系统配置列表
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/system-configs${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个系统配置
        getById: function(id) {
            return ApiService.request(`/system-configs/${id}`);
        },
        
        // 根据配置编码获取系统配置
        getByCode: function(code) {
            return ApiService.request(`/system-configs/by-code/${code}`);
        },
        
        // 批量根据配置编码获取系统配置
        getByCodes: function(codes) {
            return ApiService.request('/system-configs/batch', {
                method: 'POST',
                body: JSON.stringify({ config_codes: codes }),
            });
        },
        
        // 创建系统配置
        create: function(data) {
            return ApiService.request('/system-configs', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新系统配置
        update: function(id, data) {
            return ApiService.request(`/system-configs/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除系统配置
        delete: function(id) {
            return ApiService.request(`/system-configs/${id}`, {
                method: 'DELETE',
            });
        },
    },

    /**
     * 健康检查
     */
    health: {
        check: function() {
            return ApiService.request('/health');
        },
    },

    /**
     * 测试任务相关API
     */
    testTasks: {
        // 获取测试任务列表
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/test-tasks${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个测试任务
        getById: function(id) {
            return ApiService.request(`/test-tasks/${id}`);
        },
        
        // 创建测试任务
        create: function(data) {
            return ApiService.request('/test-tasks', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新测试任务
        update: function(id, data) {
            return ApiService.request(`/test-tasks/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除测试任务
        delete: function(id) {
            return ApiService.request(`/test-tasks/${id}`, {
                method: 'DELETE',
            });
        },
        
        // 启动任务执行
        start: function(id) {
            return ApiService.request(`/test-tasks/${id}/start`, {
                method: 'POST',
            });
        },
        
        // 取消任务执行
        cancel: function(id) {
            return ApiService.request(`/test-tasks/${id}/cancel`, {
                method: 'POST',
            });
        },
        
        // 获取任务执行状态
        getStatus: function(id) {
            return ApiService.request(`/test-tasks/${id}/status`);
        },
        
        // 重启任务执行
        restart: function(id, force = false) {
            const queryString = force ? '?force=true' : '';
            return ApiService.request(`/test-tasks/${id}/restart${queryString}`, {
                method: 'POST',
            });
        },
        
        // 检查并标记超时的测试任务
        checkTimeout: function() {
            return ApiService.request('/test-tasks/check-timeout', {
                method: 'POST',
            });
        },
        
        // 获取执行记录列表
        getExecutions: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/executions${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个执行记录
        getExecutionById: function(id) {
            return ApiService.request(`/executions/${id}`);
        },
        
        // 批量回填任务执行结果到参考答案
        backfillTaskResults: function(taskId) {
            return ApiService.request(`/executions/tasks/${taskId}/backfill`, {
                method: 'POST',
            });
        },
        
        // 单条回填执行结果到参考答案
        backfillSingleResult: function(executionId) {
            return ApiService.request(`/executions/${executionId}/backfill`, {
                method: 'POST',
            });
        },
    },

    /**
     * 评估对比相关API
     */
    evaluations: {
        // 获取评估对比列表
        getAll: function(params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/evaluations${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个评估对比
        getById: function(id) {
            return ApiService.request(`/evaluations/${id}`);
        },
        
        // 创建评估对比
        create: function(data) {
            return ApiService.request('/evaluations', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },
        
        // 更新评估对比
        update: function(id, data) {
            return ApiService.request(`/evaluations/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },
        
        // 删除评估对比
        delete: function(id) {
            return ApiService.request(`/evaluations/${id}`, {
                method: 'DELETE',
            });
        },
        
        // 启动评估对比
        start: function(id) {
            return ApiService.request(`/evaluations/${id}/start`, {
                method: 'POST',
            });
        },
        
        // 获取评估对比状态
        getStatus: function(id) {
            return ApiService.request(`/evaluations/${id}/status`);
        },
        
        // 重启评估对比
        restart: function(id, force = false) {
            const queryString = force ? '?force=true' : '';
            return ApiService.request(`/evaluations/${id}/restart${queryString}`, {
                method: 'POST',
            });
        },
        
        // 检查并标记超时的评估对比
        checkTimeout: function() {
            return ApiService.request('/evaluations/check-timeout', {
                method: 'POST',
            });
        },
        
        // 获取评估对比统计
        getStats: function(id) {
            return ApiService.request(`/evaluations/${id}/stats`);
        },
        
        // 获取评估对比综合统计（完整三层结构）
        getComprehensiveStats: function(id) {
            return ApiService.request(`/evaluations/${id}/comprehensive-stats`);
        },
        
        // 获取评估结果列表
        getResults: function(comparisonId, params = {}) {
            const queryString = new URLSearchParams(params).toString();
            return ApiService.request(`/evaluations/${comparisonId}/results${queryString ? '?' + queryString : ''}`);
        },
        
        // 获取单个评估结果详情
        getResultById: function(resultId) {
            return ApiService.request(`/evaluations/results/${resultId}`);
        },
    },
};

