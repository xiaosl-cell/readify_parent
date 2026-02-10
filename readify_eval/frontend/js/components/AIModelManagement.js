/**
 * AI模型管理组件
 * 负责AI模型的增删改查操作
 */

class AIModelManagement {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalItems = 0;
        this.currentFilters = {};
        this.models = []; // 缓存当前列表数据，便于测试时取值
    }

    /**
     * 初始化组件
     */
    async init() {
        await this.render();
        this.bindEvents();
        this.loadData();
    }

    /**
     * 渲染页面结构
     */
    async render() {
        await TemplateLoader.loadInto('ai-models.html', 'content-area');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 添加模型按钮
        $(document).off('click', '#addAIModel').on('click', '#addAIModel', function() {
            self.showModal();
        });
        
        // 应用过滤
        $(document).off('click', '#applyFilters').on('click', '#applyFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetFilters').on('click', '#resetFilters', function() {
            $('#searchModel').val('');
            $('#filterCategory').val('');
            $('#filterEnabled').val('');
            self.currentFilters = {};
            self.loadData();
        });
        
        // 搜索框回车
        $(document).off('keypress', '#searchModel').on('keypress', '#searchModel', function(e) {
            if (e.which === 13) {
                self.applyFilters();
            }
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-model').on('click', '.edit-model', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });

        // 测试按钮
        $(document).off('click', '.test-model').on('click', '.test-model', function() {
            const id = $(this).data('id');
            self.showTestModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-model').on('click', '.delete-model', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            self.deleteModel(id, name);
        });
        
        // 保存模型
        $(document).off('click', '#saveAIModel').on('click', '#saveAIModel', function() {
            self.saveModel();
        });
        
        // 切换API密钥显示/隐藏
        $(document).off('click', '#toggleApiKey').on('click', '#toggleApiKey', function() {
            const input = $('#apiKey');
            const icon = $('#toggleApiKeyIcon');
            
            if (input.attr('type') === 'password') {
                input.attr('type', 'text');
                icon.removeClass('fa-eye').addClass('fa-eye-slash');
            } else {
                input.attr('type', 'password');
                icon.removeClass('fa-eye-slash').addClass('fa-eye');
            }
        });
        
        // 分页按钮（仅限主列表的分页）
        $(document).off('click', '#aiModelsTableContent .page-link[data-page]').on('click', '#aiModelsTableContent .page-link[data-page]', function(e) {
            e.preventDefault();
            const page = $(this).data('page');
            self.currentPage = page;
            self.loadData();
        });

        // 运行模型测试
        $(document).off('click', '#runModelTest').on('click', '#runModelTest', function() {
            self.runModelTest();
        });
    }

    /**
     * 应用过滤条件
     */
    applyFilters() {
        this.currentFilters = {};
        
        const searchText = $('#searchModel').val().trim();
        if (searchText) {
            this.currentFilters.search = searchText;
        }
        
        const categoryFilter = $('#filterCategory').val();
        if (categoryFilter) {
            this.currentFilters.category = categoryFilter;
        }
        
        const enabledFilter = $('#filterEnabled').val();
        if (enabledFilter === 'true') {
            this.currentFilters.enabled_only = true;
        } else if (enabledFilter === 'false') {
            // 仅禁用：需要在前端过滤
            this.currentFilters.disabled_only = true;
        }
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#aiModelsTableContent').html(`
                <div class="loading">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-3">加载数据中...</p>
                </div>
            `);
            
            // 构建API参数
            const params = {};
            
            // 添加搜索参数
            if (this.currentFilters.search) {
                params.search = this.currentFilters.search;
            }
            
            // 添加类别筛选参数
            if (this.currentFilters.category) {
                params.category = this.currentFilters.category;
            }
            
            // 如果是"仅启用"，传递给后端API并使用分页
            if (this.currentFilters.enabled_only) {
                params.enabled_only = true;
                params.skip = this.currentPage * this.pageSize;
                params.limit = this.pageSize;
            } 
            // 如果是"仅禁用"，需要获取所有数据在前端过滤
            else if (this.currentFilters.disabled_only) {
                params.skip = 0;
                params.limit = 1000; // 获取最大数量
            }
            // 全部数据，使用分页
            else {
                params.skip = this.currentPage * this.pageSize;
                params.limit = this.pageSize;
            }
            
            const response = await ApiService.aiModels.getAll(params);
            
            let items = response.items;
            let total = response.total;
            
            // 如果是"仅禁用"，在前端过滤并分页
            if (this.currentFilters.disabled_only) {
                const allDisabledItems = items.filter(item => !item.is_enabled);
                total = allDisabledItems.length;
                
                // 前端分页
                const startIndex = this.currentPage * this.pageSize;
                const endIndex = startIndex + this.pageSize;
                items = allDisabledItems.slice(startIndex, endIndex);
            }
            
            this.models = items;
            this.totalItems = total;
            this.renderTable(items);
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#aiModelsTableContent').html(`
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>加载数据失败，请稍后重试</p>
                </div>
            `);
        }
    }

    /**
     * 渲染表格
     */
    renderTable(items) {
        if (items.length === 0) {
            $('#aiModelsTableContent').html(`
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>暂无数据</p>
                </div>
            `);
            return;
        }
        
        let tableHtml = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th style="width: 18%">模型名称</th>
                        <th style="width: 23%">模型ID</th>
                        <th style="width: 20%">BaseUrl</th>
                        <th style="width: 5%">类别</th>
                        <th style="width: 5%">状态</th>
                        <th style="width: 14%">创建时间</th>
                        <th style="width: 20%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            const statusBadge = item.is_enabled 
                ? '<span class="badge bg-success">启用</span>' 
                : '<span class="badge bg-secondary">禁用</span>';
            
            // 类别徽章
            const categoryBadge = item.category === 'Reasoning'
                ? '<span class="badge bg-info">推理</span>'
                : '<span class="badge bg-primary">指令</span>';
            
            tableHtml += `
                <tr>
                    <td><strong>${item.model_name}</strong></td>
                    <td><code>${item.model_id}</code></td>
                    <td><small>${item.api_endpoint}</small></td>
                    <td>${categoryBadge}</td>
                    <td>${statusBadge}</td>
                    <td>${UIHelper.formatDateTime(item.created_at)}</td>
                    <td class="action-buttons">
                        <button class="btn btn-sm btn-outline-success test-model" data-id="${item.id}">
                            <i class="fas fa-vial"></i> 测试
                        </button>
                        <button class="btn btn-sm btn-outline-primary edit-model" data-id="${item.id}">
                            <i class="fas fa-edit"></i> 编辑
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-model" data-id="${item.id}" data-name="${item.model_name}">
                            <i class="fas fa-trash"></i> 删除
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tableHtml += `
                </tbody>
            </table>
        `;
        
        // 添加分页
        tableHtml += this.renderPagination();
        
        $('#aiModelsTableContent').html(tableHtml);
    }

    /**
     * 渲染分页
     */
    renderPagination() {
        const totalPages = Math.ceil(this.totalItems / this.pageSize);
        
        if (totalPages <= 1) {
            return '';
        }
        
        let paginationHtml = `
            <div class="pagination-info">
                <div>
                    显示 ${this.currentPage * this.pageSize + 1} - ${Math.min((this.currentPage + 1) * this.pageSize, this.totalItems)} 
                    / 共 ${this.totalItems} 条
                </div>
                <nav>
                    <ul class="pagination mb-0">
        `;
        
        // 上一页
        paginationHtml += `
            <li class="page-item ${this.currentPage === 0 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}">上一页</a>
            </li>
        `;
        
        // 页码
        for (let i = 0; i < totalPages; i++) {
            if (i < 3 || i >= totalPages - 3 || Math.abs(i - this.currentPage) <= 1) {
                paginationHtml += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i + 1}</a>
                    </li>
                `;
            } else if (i === 3 || i === totalPages - 4) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        // 下一页
        paginationHtml += `
            <li class="page-item ${this.currentPage >= totalPages - 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}">下一页</a>
            </li>
        `;
        
        paginationHtml += `
                    </ul>
                </nav>
            </div>
        `;
        
        return paginationHtml;
    }

    /**
     * 显示模态框（创建或编辑）
     */
    async showModal(id = null) {
        if (id) {
            // 编辑模式
            $('#aiModelModalLabel').text('编辑AI模型');
            
            try {
                const model = await ApiService.aiModels.getById(id);
                
                $('#modelRowId').val(model.id);
                $('#modelName').val(model.model_name);
                $('#modelId').val(model.model_id);
                $('#apiEndpoint').val(model.api_endpoint);
                $('#apiKey').val(model.api_key || '');
                $('#modelCategory').val(model.category || 'Instruction');
                $('#isEnabled').prop('checked', model.is_enabled);
            } catch (error) {
                UIHelper.showToast('加载模型数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#aiModelModalLabel').text('添加AI模型');
            $('#aiModelForm')[0].reset();
            $('#modelRowId').val('');
            $('#apiKey').val('');
            $('#modelCategory').val('Instruction'); // 默认为指令模型
            $('#isEnabled').prop('checked', true);
        }
        
        // 重置密钥输入框为密码类型
        $('#apiKey').attr('type', 'password');
        $('#toggleApiKeyIcon').removeClass('fa-eye-slash').addClass('fa-eye');
        
        const modal = new bootstrap.Modal(document.getElementById('aiModelModal'));
        modal.show();
    }

    /**
     * 显示测试模态框
     */
    showTestModal(id) {
        const model = this.models.find(item => item.id === id);
        if (!model) {
            UIHelper.showToast('未找到模型信息，请刷新列表后重试', 'warning');
            return;
        }

        $('#testModelId').val(model.id);
        $('#testModelName').text(model.model_name || '-');
        $('#testModelCode').text(model.model_id || '-');
        $('#testModelCategory').text(model.category === 'Reasoning' ? '推理模型 (Reasoning)' : '指令模型 (Instruction)');
        $('#testModelEndpoint').text(model.api_endpoint || '-');
        $('#testModelMeta').text(`模型行ID：${model.id}`);
        $('#testPromptInput').val('你好，请简单介绍你自己。');
        $('#testResponseOutput').val('');
        $('#testModelResultStatus').text('');
        $('#testModelError').addClass('d-none').text('');
        $('#runModelTest').prop('disabled', false).html('<i class="fas fa-play"></i> 发送测试');

        const modal = new bootstrap.Modal(document.getElementById('aiModelTestModal'));
        modal.show();
    }

    /**
     * 保存模型
     */
    async saveModel() {
        const id = $('#modelRowId').val();
        const apiKeyValue = $('#apiKey').val().trim();
        
        const formData = {
            model_name: $('#modelName').val().trim(),
            model_id: $('#modelId').val().trim(),
            api_endpoint: $('#apiEndpoint').val().trim(),
            api_key: apiKeyValue || null, // 空值传null
            category: $('#modelCategory').val(),
            is_enabled: $('#isEnabled').is(':checked')
        };
        
        // 验证
        if (!formData.model_name || !formData.model_id || !formData.api_endpoint) {
            UIHelper.showToast('请填写所有必填字段', 'warning');
            return;
        }
        
        try {
            $('#saveAIModel').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                // 更新
                await ApiService.aiModels.update(id, formData);
                UIHelper.showToast('模型更新成功', 'success');
            } else {
                // 创建
                await ApiService.aiModels.create(formData);
                UIHelper.showToast('模型创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('aiModelModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveAIModel').prop('disabled', false).html('保存');
        }
    }

    /**
     * 删除模型
     */
    async deleteModel(id, name) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除模型 "${name}" 吗？\n\n此操作无法撤销。`,
            {
                title: '删除AI模型',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.aiModels.delete(id);
            UIHelper.showToast('模型删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 调用 chatCompletion 对当前模型进行测试
     */
    async runModelTest() {
        const modelId = $('#testModelId').val();
        const prompt = $('#testPromptInput').val().trim();

        if (!modelId) {
            UIHelper.showToast('未找到模型，请重新打开测试弹窗', 'warning');
            return;
        }

        if (!prompt) {
            UIHelper.showToast('请输入测试提示词', 'warning');
            return;
        }

        $('#testModelError').addClass('d-none').text('');
        $('#testModelResultStatus').text('调用中...');
        $('#runModelTest').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 测试中...');

        const requestData = {
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ]
        };

        try {
            const result = await ApiService.aiModels.chatCompletion(modelId, requestData);
            const reply =
                result?.content ||
                (result?.choices && result.choices[0]?.message?.content) ||
                '';

            $('#testResponseOutput').val(reply || JSON.stringify(result, null, 2));
            $('#testModelResultStatus').text('调用成功');
        } catch (error) {
            $('#testModelError').removeClass('d-none').text(error.message || '调用失败');
            $('#testModelResultStatus').text('调用失败');
        } finally {
            $('#runModelTest').prop('disabled', false).html('<i class="fas fa-play"></i> 发送测试');
        }
    }

    /**
     * 销毁组件（清理事件监听）
     */
    destroy() {
        $(document).off('click', '#addAIModel');
        $(document).off('click', '#applyFilters');
        $(document).off('click', '#resetFilters');
        $(document).off('keypress', '#searchModel');
        $(document).off('click', '.edit-model');
        $(document).off('click', '.test-model');
        $(document).off('click', '.delete-model');
        $(document).off('click', '#saveAIModel');
        $(document).off('click', '#toggleApiKey');
        $(document).off('click', '#aiModelsTableContent .page-link[data-page]');
        $(document).off('click', '#runModelTest');
    }
}

