/**
 * 测试任务管理组件
 * 负责测试任务的增删改查操作
 */

class TestTaskManagement {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalItems = 0;
        this.currentFilters = {};
        this.statusPollingInterval = null;
    }

    /**
     * 初始化组件
     */
    async init() {
        await this.render();
        this.bindEvents();
        await this.loadData();
        
        // 检测并轮询运行中的任务
        this.startPollingForRunningTasks();
    }

    /**
     * 渲染页面结构
     */
    async render() {
        await TemplateLoader.loadInto('test-tasks.html', 'content-area');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 添加测试任务按钮
        $(document).off('click', '#addTestTask').on('click', '#addTestTask', function() {
            self.showModal();
        });
        
        // 应用过滤
        $(document).off('click', '#applyTestTaskFilters').on('click', '#applyTestTaskFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetTestTaskFilters').on('click', '#resetTestTaskFilters', function() {
            $('#searchKeyword').val('');
            $('#statusFilter').val('');
            $('#aiModelFilter').val('');
            self.currentFilters = {};
            self.loadData();
        });
        
        // 搜索框回车
        $(document).off('keypress', '#searchKeyword').on('keypress', '#searchKeyword', function(e) {
            if (e.which === 13) {
                self.applyFilters();
            }
        });
        
        // 查看详情按钮
        $(document).off('click', '.view-task').on('click', '.view-task', function() {
            const id = $(this).data('id');
            self.viewTask(id);
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-task').on('click', '.edit-task', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-task').on('click', '.delete-task', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            self.deleteTask(id, name);
        });
        
        // 启动任务按钮
        $(document).off('click', '.start-task').on('click', '.start-task', function() {
            const id = $(this).data('id');
            self.startTask(id);
        });
        
        // 取消任务按钮
        $(document).off('click', '.cancel-task').on('click', '.cancel-task', function() {
            const id = $(this).data('id');
            self.cancelTask(id);
        });
        
        // 重启任务按钮
        $(document).off('click', '.restart-task').on('click', '.restart-task', function() {
            const id = $(this).data('id');
            const status = $(this).data('status');
            self.restartTask(id, status);
        });
        
        // 批量回填按钮（主列表）
        $(document).off('click', '.batch-backfill-task').on('click', '.batch-backfill-task', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            const successCount = $(this).data('success-count');
            self.batchBackfillFromList(id, name, successCount);
        });
        
        // 分页按钮
        $(document).off('click', '#testTasksTableContent .page-link[data-page]').on('click', '#testTasksTableContent .page-link[data-page]', function(e) {
            e.preventDefault();
            const page = $(this).data('page');
            self.currentPage = page;
            self.loadData();
        });
    }

    /**
     * 应用过滤条件
     */
    applyFilters() {
        this.currentFilters = {};
        
        const keyword = $('#searchKeyword').val().trim();
        if (keyword) {
            this.currentFilters.keyword = keyword;
        }
        
        const status = $('#statusFilter').val();
        if (status) {
            this.currentFilters.status = status;
        }
        
        const aiModelId = $('#aiModelFilter').val();
        if (aiModelId) {
            this.currentFilters.ai_model_id = aiModelId;
        }
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#testTasksTableContent').html(`
                <div class="loading">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-3">加载数据中...</p>
                </div>
            `);
            
            const params = {
                skip: this.currentPage * this.pageSize,
                limit: this.pageSize,
                ...this.currentFilters
            };
            
            const response = await ApiService.testTasks.getAll(params);
            
            this.totalItems = response.total;
            this.renderTable(response.items);
            
            // 加载AI模型列表用于筛选
            await this.loadAIModels();
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#testTasksTableContent').html(`
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>加载数据失败，请稍后重试</p>
                </div>
            `);
        }
    }

    /**
     * 加载AI模型列表（用于筛选）
     */
    async loadAIModels() {
        try {
            const response = await ApiService.aiModels.getAll({ limit: 1000 });
            const select = $('#aiModelFilter');
            
            // 清空并重新填充
            select.find('option:not(:first)').remove();
            
            response.items.forEach(model => {
                select.append(`<option value="${model.id}">${model.model_name}</option>`);
            });
        } catch (error) {
            console.error('加载AI模型列表失败:', error);
        }
    }

    /**
     * 渲染表格
     */
    renderTable(items) {
        if (items.length === 0) {
            $('#testTasksTableContent').html(`
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
                        <th style="width: 15%">任务名称</th>
                        <th style="width: 23%">任务描述</th>
                        <th style="width: 10%">状态</th>
                        <th style="width: 20%">进度</th>
                        <th style="width: 10%">AI模型</th>
                        <th style="width: 10%">创建时间</th>
                        <th style="width: 12%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            const statusBadge = this.getStatusBadge(item.status);
            const progress = item.total_cases > 0 ? Math.round((item.completed_cases / item.total_cases) * 100) : 0;
            const description = this.truncateText(item.task_description || '<em class="text-muted">无</em>', 50);
            
            tableHtml += `
                <tr data-task-id="${item.id}">
                    <td><strong>${item.task_name}</strong></td>
                    <td>${description}</td>
                    <td class="task-status-cell">${statusBadge}</td>
                    <td class="task-progress-cell">
                        <div class="d-flex align-items-center gap-2">
                            <div class="progress flex-grow-1" style="height: 20px; min-width: 100px;">
                                <div class="progress-bar ${this.getProgressBarClass(item.status)}" 
                                     role="progressbar" 
                                     style="width: ${progress}%" 
                                     aria-valuenow="${progress}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                    ${progress}%
                                </div>
                            </div>
                            <small class="text-muted text-nowrap" style="min-width: 50px; text-align: right;">${item.completed_cases}/${item.total_cases}</small>
                        </div>
                    </td>
                    <td>${item.ai_model_name ? `<span class="badge bg-info">${item.ai_model_name}</span>` : '<em class="text-muted">未配置</em>'}</td>
                    <td>${UIHelper.formatDateTime(item.created_at)}</td>
                    <td class="action-buttons">
                        <button class="btn btn-sm btn-outline-info view-task" data-id="${item.id}" title="查看详情">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${this.renderActionButtons(item)}
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
        
        $('#testTasksTableContent').html(tableHtml);
    }

    /**
     * 获取状态徽章
     */
    getStatusBadge(status) {
        const statusMap = {
            'pending': '<span class="badge bg-secondary">待执行</span>',
            'running': '<span class="badge bg-primary">执行中</span>',
            'completed': '<span class="badge bg-success">已完成</span>',
            'cancelled': '<span class="badge bg-warning">已取消</span>',
            'partial': '<span class="badge bg-info">部分完成</span>'
        };
        return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    /**
     * 获取进度条颜色类
     */
    getProgressBarClass(status) {
        const classMap = {
            'pending': 'bg-secondary',
            'running': 'bg-primary',
            'completed': 'bg-success',
            'cancelled': 'bg-warning',
            'partial': 'bg-info'
        };
        return classMap[status] || 'bg-secondary';
    }

    /**
     * 渲染操作按钮
     */
    renderActionButtons(item) {
        let buttons = '';
        
        if (item.status === 'pending' || item.status === 'partial') {
            buttons += `
                <button class="btn btn-sm btn-outline-success start-task" data-id="${item.id}" title="启动任务">
                    <i class="fas fa-play"></i>
                </button>
            `;
        }
        
        if (item.status === 'running') {
            buttons += `
                <button class="btn btn-sm btn-outline-warning cancel-task" data-id="${item.id}" title="取消任务">
                    <i class="fas fa-stop"></i>
                </button>
                <button class="btn btn-sm btn-outline-info restart-task" data-id="${item.id}" data-status="${item.status}" title="重启任务">
                    <i class="fas fa-redo"></i>
                </button>
            `;
        }
        
        // 重启按钮 - 显示给 partial 和 cancelled 状态
        if (item.status === 'partial' || item.status === 'cancelled') {
            buttons += `
                <button class="btn btn-sm btn-outline-info restart-task" data-id="${item.id}" data-status="${item.status}" title="重启任务">
                    <i class="fas fa-redo"></i>
                </button>
            `;
        }
        
        // 批量回填按钮 - 仅在有成功记录时显示
        if ((item.status === 'completed' || item.status === 'partial') && item.success_cases > 0) {
            buttons += `
                <button class="btn btn-sm btn-outline-success batch-backfill-task" 
                        data-id="${item.id}" 
                        data-name="${item.task_name}"
                        data-success-count="${item.success_cases}"
                        title="批量回填参考答案">
                    <i class="fas fa-sync-alt"></i>
                </button>
            `;
        }
        
        if (item.status === 'pending' || item.status === 'cancelled') {
            buttons += `
                <button class="btn btn-sm btn-outline-primary edit-task" data-id="${item.id}" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger delete-task" data-id="${item.id}" data-name="${item.task_name}" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        }
        
        return buttons;
    }

    /**
     * 截断文本
     */
    truncateText(text, maxLength) {
        if (!text || text.startsWith('<em')) return text;
        
        const strippedText = text.replace(/<[^>]*>/g, '');
        if (strippedText.length <= maxLength) {
            return text;
        }
        return strippedText.substring(0, maxLength) + '...';
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
     * 显示创建/编辑模态框
     */
    async showModal(id = null) {
        // 移除旧的模态框（如果存在）
        $('#testTaskModal').remove();
        
        // 加载模态框模板
        await TemplateLoader.appendTo('modals/test-task-modal.html', 'modal-container');
        
        // 等待DOM完全渲染
        await new Promise(resolve => setTimeout(resolve, 50));
        
        let taskData = null;
        
        if (id) {
            // 编辑模式
            $('#testTaskModalLabel').text('编辑测试任务');
            
            try {
                taskData = await ApiService.testTasks.getById(id);
                
                $('#taskRowId').val(taskData.id);
                $('#taskName').val(taskData.task_name);
                $('#taskDescription').val(taskData.task_description || '');
                $('#taskRemarks').val(taskData.remarks || '');
                
                // 编辑模式下禁用用例选择
                $('#useCaseSelection').hide();
                $('#editModeNote').show();
            } catch (error) {
                UIHelper.showToast('加载任务数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#testTaskModalLabel').text('创建测试任务');
            $('#useCaseSelection').show();
            $('#editModeNote').hide();
            
            // 加载提示词模板树形结构
            await this.loadTemplateTree();
        }
        
        // 加载AI模型列表（在表单重置之前）
        await this.loadAIModelsForModal();
        
        // 如果是创建模式，重置其他表单字段（不重置整个表单，以保留AI模型选项）
        if (!id) {
            $('#taskRowId').val('');
            $('#taskName').val('');
            $('#taskDescription').val('');
            $('#taskRemarks').val('');
        }
        
        // 如果是编辑模式，在加载AI模型列表后设置选中的AI模型
        if (taskData && taskData.ai_model_id) {
            $('#taskAiModelSelect').val(taskData.ai_model_id);
        }
        
        // 绑定事件
        this.bindModalEvents();
        
        const modal = new bootstrap.Modal(document.getElementById('testTaskModal'));
        modal.show();
        
        // 模态框关闭后移除DOM元素
        $('#testTaskModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }

    /**
     * 绑定模态框事件
     */
    bindModalEvents() {
        const self = this;
        
        // 保存按钮
        $(document).off('click', '#saveTestTask').on('click', '#saveTestTask', function() {
            self.saveTask();
        });
        
        // 展开/收起模板节点
        $(document).off('click', '.template-node-toggle').on('click', '.template-node-toggle', function(e) {
            e.stopPropagation();
            const templateId = $(this).closest('.template-node').data('id');
            self.toggleTemplateNode(templateId);
        });
        
        // 用例复选框变化
        $(document).off('change', '.use-case-checkbox').on('change', '.use-case-checkbox', function() {
            self.updateSelectedCount();
        });
        
        // 全选模板下的所有用例
        $(document).off('click', '.select-all-use-cases').on('click', '.select-all-use-cases', function(e) {
            e.stopPropagation();
            const templateId = $(this).closest('.template-node').data('id');
            self.selectAllUseCases(templateId);
        });
        
        // 全选所有用例（全局）
        $(document).off('click', '#selectAllUseCasesGlobal').on('click', '#selectAllUseCasesGlobal', function() {
            self.selectAllUseCasesGlobal(true);
        });
        
        // 取消全选所有用例（全局）
        $(document).off('click', '#deselectAllUseCasesGlobal').on('click', '#deselectAllUseCasesGlobal', function() {
            self.selectAllUseCasesGlobal(false);
        });
    }

    /**
     * 加载AI模型列表（用于模态框）
     */
    async loadAIModelsForModal() {
        try {
            console.log('开始加载AI模型列表...');
            const response = await ApiService.aiModels.getAll({ limit: 1000 });
            console.log('AI模型API响应:', response);
            
            const select = $('#taskAiModelSelect');
            console.log('找到select元素:', select.length, select);
            console.log('select当前的options数量:', select.find('option').length);
            
            // 清空现有选项（保留第一个默认选项）
            select.find('option:not(:first)').remove();
            
            if (!response || !response.items || response.items.length === 0) {
                console.warn('没有可用的AI模型');
                UIHelper.showToast('没有可用的AI模型，请先添加AI模型', 'warning');
                return;
            }
            
            console.log(`找到 ${response.items.length} 个AI模型`);
            response.items.forEach(model => {
                console.log(`添加模型: ${model.model_name} (ID: ${model.id})`);
                const option = $(`<option value="${model.id}">${model.model_name}</option>`);
                select.append(option);
            });
            
            console.log('AI模型列表加载完成, 当前options数量:', select.find('option').length);
            console.log('Select HTML:', select.html());
        } catch (error) {
            console.error('加载AI模型列表失败:', error);
            UIHelper.showToast('加载AI模型列表失败: ' + error.message, 'error');
        }
    }

    /**
     * 加载提示词模板树形结构
     */
    async loadTemplateTree() {
        try {
            $('#templateTree').html(`
                <div class="loading">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <span class="ms-2">加载模板和用例...</span>
                </div>
            `);
            
            console.log('开始加载模板和用例树形结构...');
            
            // 使用新的不分页接口，并行获取所有模板和所有用例
            const [templatesResponse, allUseCasesResponse] = await Promise.all([
                ApiService.promptTemplates.getAllNoPagination(),
                ApiService.promptUseCases.getAllNoPagination()
            ]);
            
            console.log(`获取到 ${templatesResponse.total} 个模板，${allUseCasesResponse.total} 个用例`);
            
            if (templatesResponse.items.length === 0) {
                $('#templateTree').html('<p class="text-muted">暂无可用的提示词模板</p>');
                return;
            }
            
            // 将用例按模板ID分组
            const useCasesByTemplate = {};
            allUseCasesResponse.items.forEach(useCase => {
                if (!useCasesByTemplate[useCase.template_id]) {
                    useCasesByTemplate[useCase.template_id] = [];
                }
                useCasesByTemplate[useCase.template_id].push(useCase);
            });
            
            // 构建树形结构
            let treeHtml = '<div class="template-tree">';
            
            templatesResponse.items.forEach(template => {
                const templateUseCases = useCasesByTemplate[template.id] || [];
                const useCaseCount = templateUseCases.length;
                
                treeHtml += `
                    <div class="template-node" data-id="${template.id}">
                        <div class="template-node-header">
                            <button type="button" class="template-node-toggle btn btn-sm btn-link p-0" ${useCaseCount === 0 ? 'disabled' : ''}>
                                <i class="fas fa-chevron-right"></i>
                            </button>
                            <span class="template-node-name">
                                <i class="fas fa-file-alt text-primary"></i>
                                ${template.template_name}
                                <span class="badge bg-secondary">${useCaseCount} 个用例</span>
                            </span>
                            ${useCaseCount > 0 ? `
                                <button type="button" class="select-all-use-cases btn btn-sm btn-outline-primary">
                                    <i class="fas fa-check-double"></i> 全选
                                </button>
                            ` : ''}
                        </div>
                        <div class="template-node-content" style="display: none;">
                `;
                
                if (useCaseCount === 0) {
                    treeHtml += '<p class="text-muted ms-4">该模板暂无用例</p>';
                } else {
                    templateUseCases.forEach(useCase => {
                        treeHtml += `
                            <div class="use-case-item">
                                <div class="form-check">
                                    <input class="form-check-input use-case-checkbox" 
                                           type="checkbox" 
                                           value="${useCase.id}" 
                                           data-template-id="${template.id}"
                                           id="useCase_${useCase.id}">
                                    <label class="form-check-label" for="useCase_${useCase.id}">
                                        <i class="fas fa-tasks text-success"></i>
                                        ${useCase.use_case_name}
                                    </label>
                                </div>
                            </div>
                        `;
                    });
                }
                
                treeHtml += `
                        </div>
                    </div>
                `;
            });
            
            treeHtml += '</div>';
            
            $('#templateTree').html(treeHtml);
            this.updateSelectedCount();
            
            console.log('模板树形结构加载完成');
            
        } catch (error) {
            console.error('加载模板树失败:', error);
            $('#templateTree').html(`
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i>
                    加载失败，请稍后重试
                </div>
            `);
        }
    }

    /**
     * 展开/收起模板节点
     */
    toggleTemplateNode(templateId) {
        const node = $(`.template-node[data-id="${templateId}"]`);
        const content = node.find('.template-node-content');
        const toggle = node.find('.template-node-toggle i');
        
        if (content.is(':visible')) {
            content.slideUp(200);
            toggle.removeClass('fa-chevron-down').addClass('fa-chevron-right');
        } else {
            content.slideDown(200);
            toggle.removeClass('fa-chevron-right').addClass('fa-chevron-down');
        }
    }

    /**
     * 全选模板下的所有用例
     */
    selectAllUseCases(templateId) {
        const node = $(`.template-node[data-id="${templateId}"]`);
        const checkboxes = node.find('.use-case-checkbox');
        const allChecked = checkboxes.filter(':checked').length === checkboxes.length;
        
        checkboxes.prop('checked', !allChecked);
        this.updateSelectedCount();
    }

    /**
     * 全选或取消全选所有用例（全局）
     * @param {boolean} select - true为全选，false为取消全选
     */
    selectAllUseCasesGlobal(select) {
        // 首先展开所有折叠的模板节点
        if (select) {
            $('.template-node-content:hidden').each(function() {
                const $content = $(this);
                const $toggle = $content.closest('.template-node').find('.template-node-toggle');
                $content.show();
                $toggle.find('i').css('transform', 'rotate(90deg)');
            });
        }
        
        // 选择或取消选择所有复选框
        $('.use-case-checkbox').prop('checked', select);
        this.updateSelectedCount();
    }

    /**
     * 更新已选择用例数量
     */
    updateSelectedCount() {
        const count = $('.use-case-checkbox:checked').length;
        $('#selectedCount').text(count);
    }

    /**
     * 保存测试任务
     */
    async saveTask() {
        const id = $('#taskRowId').val();
        const taskName = $('#taskName').val().trim();
        const taskDescription = $('#taskDescription').val().trim() || null;
        const remarks = $('#taskRemarks').val().trim() || null;
        const aiModelId = $('#taskAiModelSelect').val();
        
        // 验证
        if (!taskName) {
            UIHelper.showToast('请填写任务名称', 'warning');
            return;
        }
        
        if (!aiModelId) {
            UIHelper.showToast('请选择AI模型', 'warning');
            return;
        }
        
        let formData;
        
        if (id) {
            // 编辑模式：只能更新基本信息
            formData = {
                task_name: taskName,
                task_description: taskDescription,
                remarks: remarks
            };
        } else {
            // 创建模式：需要选择用例
            const selectedUseCases = [];
            $('.use-case-checkbox:checked').each(function() {
                selectedUseCases.push($(this).val());
            });
            
            if (selectedUseCases.length === 0) {
                UIHelper.showToast('请至少选择一个用例', 'warning');
                return;
            }
            
            formData = {
                task_name: taskName,
                task_description: taskDescription,
                use_case_ids: selectedUseCases,
                ai_model_id: aiModelId,
                remarks: remarks
            };
        }
        
        try {
            $('#saveTestTask').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                await ApiService.testTasks.update(id, formData);
                UIHelper.showToast('任务更新成功', 'success');
            } else {
                await ApiService.testTasks.create(formData);
                UIHelper.showToast('任务创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('testTaskModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveTestTask').prop('disabled', false).html('保存');
        }
    }

    /**
     * 查看任务详情
     */
    async viewTask(id) {
        const self = this;
        
        try {
            // 分别获取任务基本信息
            const task = await ApiService.testTasks.getById(id);
            
            // 创建详情模态框（不包含执行记录，稍后动态加载）
            const modalHtml = `
                <div class="modal fade" id="taskDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">测试任务详情</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="task-detail">
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <strong>任务名称：</strong>${task.task_name}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>状态：</strong>${this.getStatusBadge(task.status)}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-12">
                                            <strong>任务描述：</strong>${task.task_description || '<em class="text-muted">无</em>'}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-3">
                                            <strong>总用例数：</strong>${task.total_cases}
                                        </div>
                                        <div class="col-md-3">
                                            <strong>已完成：</strong>${task.completed_cases}
                                        </div>
                                        <div class="col-md-3">
                                            <strong>成功：</strong><span class="text-success">${task.success_cases}</span>
                                        </div>
                                        <div class="col-md-3">
                                            <strong>失败：</strong><span class="text-danger">${task.failed_cases}</span>
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-12">
                                            <strong>AI模型：</strong>${task.ai_model_name ? `<span class="badge bg-info">${task.ai_model_name}</span>` : '<em class="text-muted">未配置</em>'}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-12">
                                            <strong>备注：</strong>${task.remarks || '<em class="text-muted">无</em>'}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <strong>创建时间：</strong>${UIHelper.formatDateTime(task.created_at)}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>更新时间：</strong>${UIHelper.formatDateTime(task.updated_at)}
                                        </div>
                                    </div>
                                    
                                    <hr>
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h6 class="mb-0">执行记录</h6>
                                    </div>
                                    <div id="executionRecordsContent">
                                        <div class="loading">
                                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                                                <span class="visually-hidden">加载中...</span>
                                            </div>
                                            <span class="ms-2">加载执行记录...</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            $('#taskDetailModal').remove();
            $('body').append(modalHtml);
            
            const modal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
            modal.show();
            
            // 初始化执行记录分页变量
            let executionPage = 0;
            const executionPageSize = 10;
            
            // 加载执行记录的函数
            const loadExecutions = async (page = 0) => {
                try {
                    $('#executionRecordsContent').html(`
                        <div class="loading">
                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <span class="ms-2">加载执行记录...</span>
                        </div>
                    `);
                    
                    const executionsResponse = await ApiService.testTasks.getExecutions({
                        task_id: id,
                        skip: page * executionPageSize,
                        limit: executionPageSize
                    });
                    
                    if (executionsResponse.items.length === 0) {
                        $('#executionRecordsContent').html('<p class="text-muted">暂无执行记录</p>');
                        return;
                    }
                    
                    // 渲染执行记录表格
                    let tableHtml = `
                        <table class="table table-sm table-hover execution-records-table">
                            <thead>
                                <tr>
                                    <th style="width: 3%"></th>
                                    <th style="width: 8%">状态</th>
                                    <th style="width: 28%">系统提示词</th>
                                    <th style="width: 28%">用户提示词</th>
                                    <th style="width: 23%">LLM调用参数</th>
                                    <th style="width: 10%">操作</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    executionsResponse.items.forEach((exec, index) => {
                        const statusBadge = self.getExecutionStatusBadge(exec.status);
                        const execRowId = `exec-row-${exec.id}`;
                        const execDetailId = `exec-detail-${exec.id}`;
                        
                        // 预览提示词和参数
                        const systemPromptPreview = exec.rendered_system_prompt ? self.truncateText(exec.rendered_system_prompt, 60) : '<em class="text-muted">无</em>';
                        const userPromptPreview = exec.rendered_user_prompt ? self.truncateText(exec.rendered_user_prompt, 60) : '<em class="text-muted">无</em>';
                        
                        // HTML转义全文（用于title属性）
                        const escapeHtml = (text) => {
                            if (!text) return '';
                            return text.replace(/&/g, '&amp;')
                                      .replace(/</g, '&lt;')
                                      .replace(/>/g, '&gt;')
                                      .replace(/"/g, '&quot;')
                                      .replace(/'/g, '&#039;');
                        };
                        
                        let llmParamsPreview = '<em class="text-muted">无</em>';
                        let llmParamsDetailDisplay = '<em class="text-muted">无参数</em>';
                        let llmParams = null;
                        try {
                            if (exec.llm_params_snapshot) {
                                llmParams = JSON.parse(exec.llm_params_snapshot);
                                // 预览显示关键参数
                                const keyParams = ['max_tokens', 'temperature', 'top_p', 'top_k'];
                                const previewParts = [];
                                keyParams.forEach(key => {
                                    if (llmParams[key] !== undefined) {
                                        previewParts.push(`${key}: ${llmParams[key]}`);
                                    }
                                });
                                llmParamsPreview = previewParts.length > 0 ? previewParts.join(', ') : '<em class="text-muted">无</em>';
                            }
                        } catch (e) {
                            llmParamsPreview = '<em class="text-warning">解析失败</em>';
                            llmParamsDetailDisplay = '<em class="text-warning">参数解析失败</em>';
                        }
                        
                        // 回填按钮（仅成功状态且有用例ID和输出结果）
                        let backfillButton = '';
                        
                        // 使用正确的字段名：prompt_use_case_id
                        if (exec.status === 'success' && exec.prompt_use_case_id && exec.output_result) {
                            backfillButton = `
                                <button class="btn btn-xs btn-outline-success backfill-single-btn" 
                                        data-exec-id="${exec.id}" 
                                        data-use-case-name="${escapeHtml(exec.prompt_use_case_name || '未知用例')}"
                                        title="回填到参考答案"
                                        onclick="event.stopPropagation();">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                            `;
                        } else {
                            // 显示为什么不能回填的提示
                            let reason = '';
                            if (exec.status !== 'success') {
                                reason = '非成功状态';
                            } else if (!exec.prompt_use_case_id) {
                                reason = '无用例ID';
                            } else if (!exec.output_result) {
                                reason = '无输出结果';
                            }
                            if (reason) {
                                backfillButton = `<small class="text-muted" title="${reason}">-</small>`;
                            }
                        }
                        
                        // 主行
                        tableHtml += `
                            <tr class="execution-row" data-exec-id="${exec.id}" style="cursor: pointer;">
                                <td>
                                    <i class="fas fa-chevron-right toggle-icon" id="toggle-${exec.id}"></i>
                                </td>
                                <td>${statusBadge}</td>
                                <td title="${escapeHtml(exec.rendered_system_prompt)}"><small class="text-muted">${systemPromptPreview}</small></td>
                                <td title="${escapeHtml(exec.rendered_user_prompt)}"><small class="text-muted">${userPromptPreview}</small></td>
                                <td><small class="text-muted">${llmParamsPreview}</small></td>
                                <td>${backfillButton}</td>
                            </tr>
                        `;
                        
                        // 格式化提示词和输出结果（保留换行和空格）
                        const formatText = (text) => {
                            if (!text) return '<em class="text-muted">无内容</em>';
                            return text.replace(/</g, '&lt;')
                                      .replace(/>/g, '&gt;')
                                      .replace(/\n/g, '<br>')
                                      .replace(/  /g, '&nbsp;&nbsp;');
                        };
                        
                        // LLM参数详细展示（分列美化）
                        let llmParamsDetailHtml = '<div class="text-muted text-center py-3">暂无参数</div>';
                        if (llmParams) {
                            llmParamsDetailHtml = `
                                <div class="row g-3">
                                    <div class="col-md-3">
                                        <div class="param-card">
                                            <div class="param-label"><i class="fas fa-hashtag"></i> max_tokens</div>
                                            <div class="param-value">${llmParams.max_tokens !== undefined ? llmParams.max_tokens : '-'}</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="param-card">
                                            <div class="param-label"><i class="fas fa-thermometer-half"></i> temperature</div>
                                            <div class="param-value">${llmParams.temperature !== undefined ? llmParams.temperature : '-'}</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="param-card">
                                            <div class="param-label"><i class="fas fa-percentage"></i> top_p</div>
                                            <div class="param-value">${llmParams.top_p !== undefined ? llmParams.top_p : '-'}</div>
                                        </div>
                                    </div>
                                    <div class="col-md-3">
                                        <div class="param-card">
                                            <div class="param-label"><i class="fas fa-sort-amount-down"></i> top_k</div>
                                            <div class="param-value">${llmParams.top_k !== undefined ? llmParams.top_k : '-'}</div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }
                        
                        tableHtml += `
                            <tr class="execution-detail" id="${execDetailId}" style="display: none;">
                                <td colspan="6">
                                    <div class="card border-0 bg-light">
                                        <div class="card-body p-3">
                                            <!-- 提示词 -->
                                            <div class="row mb-3">
                                                <div class="col-md-6">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-robot text-primary"></i> 系统提示词
                                                    </h6>
                                                    <div class="border rounded p-3 bg-white" style="height: 200px; overflow-y: auto; white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem;">${formatText(exec.rendered_system_prompt)}</div>
                                                </div>
                                                <div class="col-md-6">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-user text-success"></i> 用户提示词
                                                    </h6>
                                                    <div class="border rounded p-3 bg-white" style="height: 200px; overflow-y: auto; white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem;">${formatText(exec.rendered_user_prompt)}</div>
                                                </div>
                                            </div>
                                            
                                            <!-- LLM参数 -->
                                            <div class="row mb-3">
                                                <div class="col-12">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-cog text-secondary"></i> LLM调用参数
                                                    </h6>
                                                    <div class="border rounded p-3 bg-white">
                                                        ${llmParamsDetailHtml}
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- 输出结果 -->
                                            <div class="row mb-3">
                                                <div class="col-12">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-reply text-info"></i> 完整输出结果
                                                    </h6>
                                                    <div class="border rounded p-3 bg-white" style="max-height: 250px; overflow-y: auto; white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem;">${formatText(exec.output_result)}</div>
                                                </div>
                                            </div>
                                            
                                            <!-- 执行信息 -->
                                            <div class="row mb-3">
                                                <div class="col-12">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-info-circle text-warning"></i> 执行信息
                                                    </h6>
                                                    <div class="border rounded p-3 bg-white">
                                                        <div class="row g-3">
                                                            <div class="col-md-3">
                                                                <div class="exec-info-item">
                                                                    <i class="fas fa-clock text-primary"></i>
                                                                    <div class="exec-info-label">开始时间</div>
                                                                    <div class="exec-info-value">${exec.start_time ? UIHelper.formatDateTime(exec.start_time) : '-'}</div>
                                                                </div>
                                                            </div>
                                                            <div class="col-md-3">
                                                                <div class="exec-info-item">
                                                                    <i class="fas fa-flag-checkered text-success"></i>
                                                                    <div class="exec-info-label">结束时间</div>
                                                                    <div class="exec-info-value">${exec.end_time ? UIHelper.formatDateTime(exec.end_time) : '-'}</div>
                                                                </div>
                                                            </div>
                                                            <div class="col-md-3">
                                                                <div class="exec-info-item">
                                                                    <i class="fas fa-hourglass-half text-info"></i>
                                                                    <div class="exec-info-label">总耗时(秒)</div>
                                                                    <div class="exec-info-value">${exec.execution_duration ? exec.execution_duration.toFixed(2) : '-'}</div>
                                                                </div>
                                                            </div>
                                                            <div class="col-md-3">
                                                                <div class="exec-info-item">
                                                                    <i class="fas fa-tachometer-alt text-purple"></i>
                                                                    <div class="exec-info-label">模型响应耗时(秒)</div>
                                                                    <div class="exec-info-value">${exec.model_response_duration ? exec.model_response_duration.toFixed(2) : '-'}</div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- 错误信息 -->
                                            ${exec.error_message ? `
                                            <div class="row">
                                                <div class="col-12">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-exclamation-triangle text-danger"></i> 错误信息
                                                    </h6>
                                                    <div class="alert alert-danger mb-0">
                                                        <small style="white-space: pre-wrap; word-break: break-word;">${formatText(exec.error_message)}</small>
                                                    </div>
                                                </div>
                                            </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        `;
                    });
                    
                    tableHtml += `
                            </tbody>
                        </table>
                    `;
                    
                    // 添加分页
                    const totalPages = Math.ceil(executionsResponse.total / executionPageSize);
                    if (totalPages > 1) {
                        tableHtml += `
                            <div class="pagination-info">
                                <div>
                                    <small>显示 ${page * executionPageSize + 1} - ${Math.min((page + 1) * executionPageSize, executionsResponse.total)} 
                                    / 共 ${executionsResponse.total} 条</small>
                                </div>
                                <nav>
                                    <ul class="pagination pagination-sm mb-0" id="executionPagination">
                        `;
                        
                        // 上一页
                        tableHtml += `
                            <li class="page-item ${page === 0 ? 'disabled' : ''}">
                                <a class="page-link" href="#" data-page="${page - 1}">上一页</a>
                            </li>
                        `;
                        
                        // 页码
                        for (let i = 0; i < totalPages; i++) {
                            if (i < 3 || i >= totalPages - 3 || Math.abs(i - page) <= 1) {
                                tableHtml += `
                                    <li class="page-item ${i === page ? 'active' : ''}">
                                        <a class="page-link" href="#" data-page="${i}">${i + 1}</a>
                                    </li>
                                `;
                            } else if (i === 3 || i === totalPages - 4) {
                                tableHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
                            }
                        }
                        
                        // 下一页
                        tableHtml += `
                            <li class="page-item ${page >= totalPages - 1 ? 'disabled' : ''}">
                                <a class="page-link" href="#" data-page="${page + 1}">下一页</a>
                            </li>
                        `;
                        
                        tableHtml += `
                                    </ul>
                                </nav>
                            </div>
                        `;
                    }
                    
                    $('#executionRecordsContent').html(tableHtml);
                    
                    // 绑定展开/收起事件
                    $('.execution-row').off('click').on('click', function() {
                        const execId = $(this).data('exec-id');
                        const detailRow = $(`#exec-detail-${execId}`);
                        const toggleIcon = $(`#toggle-${execId}`);
                        
                        if (detailRow.is(':visible')) {
                            // 收起
                            detailRow.hide();
                            toggleIcon.removeClass('fa-chevron-down').addClass('fa-chevron-right');
                        } else {
                            // 展开
                            detailRow.show();
                            toggleIcon.removeClass('fa-chevron-right').addClass('fa-chevron-down');
                        }
                    });
                    
                    // 绑定分页点击事件
                    $('#executionPagination .page-link[data-page]').off('click').on('click', function(e) {
                        e.preventDefault();
                        const newPage = parseInt($(this).data('page'));
                        if (!isNaN(newPage) && newPage >= 0 && newPage < totalPages) {
                            executionPage = newPage;
                            loadExecutions(executionPage);
                        }
                    });
                    
                    // 绑定单条回填按钮事件
                    $('.backfill-single-btn').off('click').on('click', function(e) {
                        e.stopPropagation();
                        const execId = $(this).data('exec-id');
                        const useCaseName = $(this).data('use-case-name');
                        self.backfillSingleExecution(execId, useCaseName, loadExecutions, executionPage);
                    });
                    
                } catch (error) {
                    console.error('加载执行记录失败:', error);
                    $('#executionRecordsContent').html(`
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle"></i>
                            加载执行记录失败，请稍后重试
                        </div>
                    `);
                }
            };
            
            // 初始加载执行记录
            loadExecutions(executionPage);
            
            // 模态框关闭后移除
            $('#taskDetailModal').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            UIHelper.showToast('加载任务详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 获取执行状态徽章
     */
    getExecutionStatusBadge(status) {
        const statusMap = {
            'pending': '<span class="badge bg-secondary">待执行</span>',
            'success': '<span class="badge bg-success">成功</span>',
            'failed': '<span class="badge bg-danger">失败</span>'
        };
        return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    /**
     * 启动任务
     */
    async startTask(id) {
        const confirmed = await UIHelper.confirmDialog(
            '确定要启动这个测试任务吗？',
            {
                title: '启动测试任务',
                confirmText: '确认启动',
                cancelText: '取消',
                confirmClass: 'btn-primary'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.testTasks.start(id);
            UIHelper.showToast('任务已启动', 'success');
            this.loadData();
            
            // 开始轮询状态
            this.startStatusPolling(id);
        } catch (error) {
            UIHelper.showToast('启动失败: ' + error.message, 'error');
        }
    }

    /**
     * 更新表格中的任务状态和进度
     * @param {string} id - 任务ID
     * @param {object} status - 状态对象
     */
    updateTaskInTable(id, status) {
        const row = $(`tr[data-task-id="${id}"]`);
        if (row.length === 0) {
            return; // 任务不在当前页，跳过更新
        }
        
        // 更新状态徽章
        const statusBadge = this.getStatusBadge(status.status);
        row.find('.task-status-cell').html(statusBadge);
        
        // 更新进度条
        const progress = status.total_cases > 0 ? Math.round((status.completed_cases / status.total_cases) * 100) : 0;
        const progressBarClass = this.getProgressBarClass(status.status);
        
        row.find('.task-progress-cell').html(`
            <div class="d-flex align-items-center gap-2">
                <div class="progress flex-grow-1" style="height: 20px; min-width: 100px;">
                    <div class="progress-bar ${progressBarClass}" 
                         role="progressbar" 
                         style="width: ${progress}%" 
                         aria-valuenow="${progress}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${progress}%
                    </div>
                </div>
                <small class="text-muted text-nowrap" style="min-width: 50px; text-align: right;">${status.completed_cases}/${status.total_cases}</small>
            </div>
        `);
    }

    /**
     * 开始状态轮询
     * @param {string} id - 任务ID
     * @param {number} interval - 轮询间隔（毫秒），默认3000ms
     * @param {boolean} showNotification - 是否显示完成通知，默认true
     */
    startStatusPolling(id, interval = 3000, showNotification = true) {
        // 清除之前的轮询
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
        }
        
        const self = this;
        this.statusPollingInterval = setInterval(async () => {
            try {
                const status = await ApiService.testTasks.getStatus(id);
                
                if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
                    clearInterval(self.statusPollingInterval);
                    self.statusPollingInterval = null;
                    self.loadData();
                    
                    // 只在用户主动启动时显示通知
                    if (showNotification) {
                        if (status.status === 'completed') {
                            UIHelper.showToast('任务已完成', 'success');
                        } else if (status.status === 'failed') {
                            UIHelper.showToast('任务执行失败', 'error');
                        } else if (status.status === 'cancelled') {
                            UIHelper.showToast('任务已取消', 'warning');
                        }
                    }
                } else {
                    // 仍在运行中，打印进度并更新表格
                    console.log(`任务进度: ${status.progress_percentage}% (${status.completed_cases}/${status.total_cases})`);
                    // 更新表格中的任务状态和进度
                    self.updateTaskInTable(id, status);
                }
            } catch (error) {
                console.error('状态轮询失败:', error);
                clearInterval(self.statusPollingInterval);
                self.statusPollingInterval = null;
            }
        }, interval); // 使用传入的轮询间隔
    }

    /**
     * 检测并轮询运行中的任务
     */
    async startPollingForRunningTasks() {
        try {
            // 获取所有运行中的任务
            const response = await ApiService.testTasks.getAll({ 
                status: 'running',
                limit: 100 
            });
            
            if (response.items && response.items.length > 0) {
                // 如果有运行中的任务，为第一个任务启动轮询（使用10秒间隔）
                const runningTask = response.items[0];
                console.log(`检测到运行中的任务: ${runningTask.task_name}，开始后台轮询`);
                this.startStatusPolling(runningTask.id, 10000, false);
            }
        } catch (error) {
            console.error('检测运行中任务失败:', error);
        }
    }

    /**
     * 取消任务
     */
    async cancelTask(id) {
        const confirmed = await UIHelper.confirmDialog(
            '确定要取消这个测试任务吗？',
            {
                title: '取消测试任务',
                confirmText: '确认取消',
                cancelText: '返回',
                confirmClass: 'btn-warning'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.testTasks.cancel(id);
            UIHelper.showToast('任务已取消', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('取消失败: ' + error.message, 'error');
        }
    }

    /**
     * 重启任务
     */
    async restartTask(id, status) {
        let confirmMessage = '';
        let useForce = false;
        
        if (status === 'running') {
            // 运行中的任务需要询问是否强制重启
            confirmMessage = '这个任务正在运行中。\n\n' +
                '- 选择"普通重启"：需要任务超过10分钟未更新才能重启（更安全）\n' +
                '- 选择"强制重启"：立即重启，忽略时间限制（适合确认任务已卡住的情况）\n\n' +
                '建议先检查任务的更新时间，如果长时间无更新再重启。\n\n' +
                '您要强制重启吗？';
            
            const forceConfirmed = await UIHelper.confirmDialog(
                confirmMessage,
                {
                    title: '重启运行中的任务',
                    confirmText: '强制重启',
                    cancelText: '普通重启',
                    confirmClass: 'btn-warning'
                }
            );
            
            // 如果用户关闭了对话框（返回 null 或 undefined）
            if (forceConfirmed === null || forceConfirmed === undefined) {
                return;
            }
            useForce = forceConfirmed === true;
        } else if (status === 'partial') {
            confirmMessage = '确定要重启这个部分完成的任务吗？\n\n系统将继续执行未完成的用例。';
        } else if (status === 'cancelled') {
            confirmMessage = '确定要重启这个已取消的任务吗？\n\n系统将继续执行未完成的用例。';
        } else {
            confirmMessage = '确定要重启这个任务吗？\n\n系统将继续执行未完成的用例。';
        }
        
        const confirmed = await UIHelper.confirmDialog(
            confirmMessage,
            {
                title: '重启测试任务',
                confirmText: '确认重启',
                cancelText: '取消',
                confirmClass: 'btn-info'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.testTasks.restart(id, useForce);
            UIHelper.showToast('任务已重启', 'success');
            this.loadData();
            
            // 开始轮询状态
            this.startStatusPolling(id);
        } catch (error) {
            UIHelper.showToast('重启失败: ' + error.message, 'error');
        }
    }

    /**
     * 删除任务
     */
    async deleteTask(id, name) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除测试任务 "${name}" 吗？\n\n此操作无法撤销。`,
            {
                title: '删除测试任务',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.testTasks.delete(id);
            UIHelper.showToast('任务删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 批量回填任务执行结果到参考答案（从列表页调用）
     */
    async batchBackfillFromList(taskId, taskName, successCount) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要将任务 "${taskName}" 的所有成功执行结果回填到对应用例的参考答案吗？\n\n` +
            `共有 ${successCount} 条成功记录将被处理。\n` +
            `⚠️ 警告：回填操作会覆盖现有的参考答案！`,
            {
                title: '批量回填参考答案',
                confirmText: '确认回填',
                cancelText: '取消',
                confirmClass: 'btn-success'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            UIHelper.showToast('正在批量回填...', 'info');
            
            const result = await ApiService.testTasks.backfillTaskResults(taskId);
            
            console.log('批量回填结果:', result);
            
            // 显示详细结果
            let message = `批量回填完成！\n\n`;
            message += `✅ 成功更新: ${result.updated_use_cases} 个用例\n`;
            message += `⏭️ 跳过: ${result.skipped} 条记录\n`;
            message += `📊 总处理: ${result.total_executions} 条成功记录`;
            
            if (result.updated_use_cases > 0) {
                UIHelper.showToast(message, 'success');
            } else if (result.skipped > 0) {
                message += '\n\n请检查跳过原因（见控制台详情）';
                UIHelper.showToast(message, 'warning');
            }
            
            // 打印详细信息到控制台
            console.table(result.details);
            
            // 刷新任务列表
            this.loadData();
            
        } catch (error) {
            console.error('批量回填失败:', error);
            UIHelper.showToast('批量回填失败: ' + error.message, 'error');
        }
    }

    /**
     * 单条回填执行结果到参考答案
     */
    async backfillSingleExecution(executionId, useCaseName, reloadCallback, currentPage) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要将此执行结果回填到用例 "${useCaseName}" 的参考答案吗？\n\n` +
            `⚠️ 警告：回填操作会覆盖现有的参考答案！`,
            {
                title: '回填参考答案',
                confirmText: '确认回填',
                cancelText: '取消',
                confirmClass: 'btn-success'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            const result = await ApiService.testTasks.backfillSingleResult(executionId);
            
            console.log('单条回填结果:', result);
            
            if (result.status === 'updated') {
                let message = `✅ 成功回填到用例: ${result.use_case_name}`;
                
                if (result.old_reference_answer) {
                    message += `\n\n旧答案已被覆盖`;
                }
                
                UIHelper.showToast(message, 'success');
            } else if (result.status === 'skipped') {
                UIHelper.showToast(`⏭️ 跳过回填：${result.reason}`, 'warning');
            }
            
            // 刷新执行记录列表
            if (reloadCallback) {
                reloadCallback(currentPage);
            }
            
        } catch (error) {
            console.error('回填失败:', error);
            UIHelper.showToast('回填失败: ' + error.message, 'error');
        }
    }

    /**
     * 销毁组件（清理事件监听和轮询）
     */
    destroy() {
        // 清除状态轮询
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
            this.statusPollingInterval = null;
        }
        
        // 清理事件监听
        $(document).off('click', '#addTestTask');
        $(document).off('click', '#applyTestTaskFilters');
        $(document).off('click', '#resetTestTaskFilters');
        $(document).off('keypress', '#searchKeyword');
        $(document).off('click', '.view-task');
        $(document).off('click', '.edit-task');
        $(document).off('click', '.delete-task');
        $(document).off('click', '.start-task');
        $(document).off('click', '.cancel-task');
        $(document).off('click', '.restart-task');
        $(document).off('click', '.batch-backfill-task');
        $(document).off('click', '#testTasksTableContent .page-link[data-page]');
        $(document).off('click', '#saveTestTask');
        $(document).off('click', '.template-node-toggle');
        $(document).off('change', '.use-case-checkbox');
        $(document).off('click', '.select-all-use-cases');
    }
}



