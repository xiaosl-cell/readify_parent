/**
 * 评估管理组件
 * 负责评估对比的增删改查和结果查看
 */

class EvaluationManagement {
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
        
        // 检测并轮询运行中的评估
        this.startPollingForRunningEvaluations();
    }

    /**
     * 渲染页面结构
     */
    async render() {
        await TemplateLoader.loadInto('evaluations.html', 'content-area');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 创建评估对比按钮
        $(document).off('click', '#addEvaluation').on('click', '#addEvaluation', function() {
            self.showModal();
        });
        
        // 应用过滤
        $(document).off('click', '#applyFilters').on('click', '#applyFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetFilters').on('click', '#resetFilters', function() {
            $('#searchKeyword').val('');
            $('#statusFilter').val('');
            $('#testTaskFilter').val('');
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
        $(document).off('click', '.view-evaluation').on('click', '.view-evaluation', function() {
            const id = $(this).data('id');
            self.viewEvaluation(id);
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-evaluation').on('click', '.edit-evaluation', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-evaluation').on('click', '.delete-evaluation', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            self.deleteEvaluation(id, name);
        });
        
        // 启动评估按钮
        $(document).off('click', '.start-evaluation').on('click', '.start-evaluation', function() {
            const id = $(this).data('id');
            self.startEvaluation(id);
        });
        
        // 重启评估按钮
        $(document).off('click', '.restart-evaluation').on('click', '.restart-evaluation', function() {
            const id = $(this).data('id');
            const status = $(this).data('status');
            self.restartEvaluation(id, status);
        });
        
        // 查看统计按钮
        $(document).off('click', '.view-stats').on('click', '.view-stats', function() {
            const id = $(this).data('id');
            self.viewStats(id);
        });
        
        // 分页按钮
        $(document).off('click', '#evaluationsTableContent .page-link[data-page]').on('click', '#evaluationsTableContent .page-link[data-page]', function(e) {
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
        
        const testTaskId = $('#testTaskFilter').val();
        if (testTaskId) {
            this.currentFilters.test_task_id = testTaskId;
        }
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#evaluationsTableContent').html(`
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
            
            const response = await ApiService.evaluations.getAll(params);
            
            this.totalItems = response.total;
            this.renderTable(response.items);
            
            // 加载测试任务列表用于筛选
            await this.loadCompletedTasks();
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#evaluationsTableContent').html(`
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>加载数据失败，请稍后重试</p>
                </div>
            `);
        }
    }

    /**
     * 加载已完成的测试任务（用于筛选）
     */
    async loadCompletedTasks() {
        try {
            const response = await ApiService.testTasks.getAll({ status: 'completed', limit: 1000 });
            const select = $('#testTaskFilter');
            
            // 清空并重新填充
            select.find('option:not(:first)').remove();
            
            response.items.forEach(task => {
                select.append(`<option value="${task.id}">${task.task_name}</option>`);
            });
        } catch (error) {
            console.error('加载测试任务列表失败:', error);
        }
    }

    /**
     * 渲染表格
     */
    renderTable(items) {
        if (items.length === 0) {
            $('#evaluationsTableContent').html(`
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
                        <th style="width: 18%">对比名称</th>
                        <th style="width: 15%">测试任务</th>
                        <th style="width: 15%">评估策略</th>
                        <th style="width: 9%">状态</th>
                        <th style="width: 20%">进度</th>
                        <th style="width: 15%">创建时间</th>
                        <th style="width: 8%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            const statusBadge = this.getStatusBadge(item.status);
            const progress = item.total_pairs > 0 ? Math.round((item.completed_pairs / item.total_pairs) * 100) : 0;
            
            // 解析评估策略
            let strategies = [];
            try {
                strategies = JSON.parse(item.evaluation_strategies || '[]');
            } catch (e) {
                console.error('解析评估策略失败:', e);
            }
            
            // 格式化策略显示
            const strategyNames = strategies.slice(0, 2).map(s => this.formatStrategyName(s));
            const strategiesDisplay = strategies.length > 0 
                ? `<small class="text-muted">${strategyNames.join('、')}${strategies.length > 2 ? ` +${strategies.length - 2}` : ''}</small>` 
                : '<em class="text-muted">-</em>';
            
            tableHtml += `
                <tr data-evaluation-id="${item.id}">
                    <td><strong>${item.comparison_name}</strong></td>
                    <td>
                        ${item.test_task_name || '<em class="text-muted">未知</em>'}
                        ${item.evaluation_model_name ? `<br><small class="text-muted"><i class="fas fa-brain"></i> ${item.evaluation_model_name}</small>` : ''}
                    </td>
                    <td>${strategiesDisplay}</td>
                    <td class="evaluation-status-cell">${statusBadge}</td>
                    <td class="evaluation-progress-cell">
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
                            <small class="text-muted text-nowrap" style="min-width: 50px; text-align: right;">${item.completed_pairs}/${item.total_pairs}</small>
                        </div>
                    </td>
                    <td>${UIHelper.formatDateTime(item.created_at)}</td>
                    <td class="action-buttons">
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
        
        $('#evaluationsTableContent').html(tableHtml);
    }

    /**
     * 获取状态徽章
     */
    getStatusBadge(status) {
        const statusMap = {
            'pending': '<span class="badge bg-secondary">待执行</span>',
            'running': '<span class="badge bg-primary">执行中</span>',
            'completed': '<span class="badge bg-success">已完成</span>',
            'failed': '<span class="badge bg-danger">失败</span>'
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
            'failed': 'bg-danger'
        };
        return classMap[status] || 'bg-secondary';
    }

    /**
     * 获取相似度徽章颜色类
     */
    getSimilarityBadgeClass(similarity) {
        if (similarity >= 0.9) return 'bg-success';
        if (similarity >= 0.7) return 'bg-info';
        if (similarity >= 0.5) return 'bg-warning';
        return 'bg-danger';
    }

    /**
     * 渲染操作按钮
     */
    renderActionButtons(item) {
        let buttons = `
            <button class="btn btn-sm btn-outline-info view-evaluation" data-id="${item.id}" title="查看详情">
                <i class="fas fa-eye"></i>
            </button>
        `;
        
        if (item.status === 'pending' || item.status === 'failed') {
            buttons += `
                <button class="btn btn-sm btn-outline-success start-evaluation" data-id="${item.id}" title="启动评估">
                    <i class="fas fa-play"></i>
                </button>
            `;
        }
        
        // 重启按钮 - 显示给 running 和 failed 状态
        if (item.status === 'running' || item.status === 'failed') {
            buttons += `
                <button class="btn btn-sm btn-outline-info restart-evaluation" data-id="${item.id}" data-status="${item.status}" title="重启评估">
                    <i class="fas fa-redo"></i>
                </button>
            `;
        }
        
        if (item.status === 'completed') {
            buttons += `
                <button class="btn btn-sm btn-outline-primary view-stats" data-id="${item.id}" title="查看统计">
                    <i class="fas fa-chart-pie"></i>
                </button>
            `;
        }
        
        if (item.status === 'pending') {
            buttons += `
                <button class="btn btn-sm btn-outline-warning edit-evaluation" data-id="${item.id}" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger delete-evaluation" data-id="${item.id}" data-name="${item.comparison_name}" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        }
        
        return buttons;
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
        $('#evaluationModal').remove();
        
        // 加载模态框模板
        await TemplateLoader.appendTo('modals/evaluation-modal.html', 'modal-container');
        
        let evaluationData = null;
        
        if (id) {
            // 编辑模式
            $('#evaluationModalLabel').text('编辑评估对比');
            
            try {
                evaluationData = await ApiService.evaluations.getById(id);
                
                $('#evaluationRowId').val(evaluationData.id);
                $('#comparisonName').val(evaluationData.comparison_name);
                $('#comparisonDescription').val(evaluationData.comparison_description || '');
                $('#evaluationRemarks').val(evaluationData.remarks || '');
                
                // 显示评估策略
                this.displayEvaluationStrategies(evaluationData.evaluation_strategies);
                
                // 显示评估模型
                if (evaluationData.evaluation_model_id) {
                    $('#evaluationModelSelect').val(evaluationData.evaluation_model_id);
                }
            } catch (error) {
                UIHelper.showToast('加载评估数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#evaluationModalLabel').text('创建评估对比');
            $('#evaluationForm')[0].reset();
            $('#evaluationRowId').val('');
        }
        
        // 加载已完成的测试任务列表和 AI 模型列表
        await Promise.all([
            this.loadCompletedTasksForModal(),
            this.loadAIModelsForModal()
        ]);
        
        // 如果是编辑模式，在加载任务列表后设置选中的任务
        if (evaluationData) {
            $('#testTaskSelect').val(evaluationData.test_task_id);
            $('#evaluationModelSelect').val(evaluationData.evaluation_model_id || '');
            // 编辑模式下禁用任务选择和评估模型选择
            $('#testTaskSelect').prop('disabled', true);
            $('#evaluationModelSelect').prop('disabled', true);
        }
        
        // 绑定测试任务选择变化事件（创建模式下预览评估策略）
        if (!id) {
            $(document).off('change', '#testTaskSelect').on('change', '#testTaskSelect', async function() {
                const taskId = $(this).val();
                if (taskId) {
                    await self.previewEvaluationStrategies(taskId);
                } else {
                    $('#evaluationStrategiesInfo').hide();
                    self.updateEvaluationModelRequirement([]);
                }
            });
        }
        
        // 绑定事件
        this.bindModalEvents();
        
        const modal = new bootstrap.Modal(document.getElementById('evaluationModal'));
        modal.show();
        
        // 模态框关闭后移除DOM元素
        $('#evaluationModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }

    /**
     * 绑定模态框事件
     */
    bindModalEvents() {
        const self = this;
        
        // 保存按钮
        $(document).off('click', '#saveEvaluation').on('click', '#saveEvaluation', function() {
            self.saveEvaluation();
        });
    }

    /**
     * 加载已完成的测试任务（用于模态框）
     */
    async loadCompletedTasksForModal() {
        try {
            const response = await ApiService.testTasks.getAll({ status: 'completed', limit: 1000 });
            const testTaskSelect = $('#testTaskSelect');
            
            testTaskSelect.find('option:not(:first)').remove();
            
            response.items.forEach(task => {
                const option = `<option value="${task.id}">${task.task_name} (${task.success_cases}/${task.total_cases} 成功)</option>`;
                testTaskSelect.append(option);
            });
        } catch (error) {
            console.error('加载测试任务列表失败:', error);
            UIHelper.showToast('加载测试任务列表失败', 'warning');
        }
    }
    
    /**
     * 加载 AI 模型列表（用于模态框）
     */
    async loadAIModelsForModal() {
        try {
            const response = await ApiService.aiModels.getAll({ enabled_only: true, limit: 1000 });
            const evaluationModelSelect = $('#evaluationModelSelect');
            
            evaluationModelSelect.find('option:not(:first)').remove();
            
            response.items.forEach(model => {
                const option = `<option value="${model.id}">${model.model_name}</option>`;
                evaluationModelSelect.append(option);
            });
        } catch (error) {
            console.error('加载 AI 模型列表失败:', error);
            UIHelper.showToast('加载 AI 模型列表失败', 'warning');
        }
    }
    
    /**
     * 预览评估策略（从测试任务的执行记录中提取）
     */
    async previewEvaluationStrategies(taskId) {
        try {
            // 获取测试任务的执行记录
            const response = await ApiService.executions.getAll({ 
                task_id: taskId,
                status: 'success',
                limit: 100 
            });
            
            // 提取所有评估策略
            const strategiesSet = new Set();
            response.items.forEach(execution => {
                if (execution.evaluation_strategies_snapshot) {
                    try {
                        const strategies = JSON.parse(execution.evaluation_strategies_snapshot);
                        strategies.forEach(s => strategiesSet.add(s));
                    } catch (e) {
                        console.error('解析评估策略失败:', e);
                    }
                }
            });
            
            const strategies = Array.from(strategiesSet);
            this.displayEvaluationStrategies(JSON.stringify(strategies));
            
            // 更新评估模型必填状态
            this.updateEvaluationModelRequirement(strategies);
            
        } catch (error) {
            console.error('预览评估策略失败:', error);
            $('#evaluationStrategiesInfo').hide();
            this.updateEvaluationModelRequirement([]);
        }
    }
    
    /**
     * 更新评估模型必填状态
     */
    updateEvaluationModelRequirement(strategies) {
        // 检查是否包含需要 LLM 评估的策略
        const needsLLM = strategies.some(s => 
            s === 'answer_accuracy' || s === 'factual_correctness'
        );
        
        if (needsLLM) {
            $('#evaluationModelRequired').html('<span class="text-danger">*</span>');
            $('#evaluationModelSelect').attr('required', true);
            $('#evaluationModelSelect').closest('.mb-3').addClass('required-field');
        } else {
            $('#evaluationModelRequired').html('');
            $('#evaluationModelSelect').removeAttr('required');
            $('#evaluationModelSelect').closest('.mb-3').removeClass('required-field');
        }
    }
    
    /**
     * 显示评估策略
     */
    displayEvaluationStrategies(strategiesJson) {
        try {
            const strategies = JSON.parse(strategiesJson || '[]');
            if (strategies.length > 0) {
                // 映射策略名称为中文
                const strategyNames = {
                    'exact_match': '精确匹配',
                    'json_key_match': 'JSON 键匹配',
                    'answer_accuracy': '答案准确率 ⚠️',
                    'factual_correctness': '事实正确性 ⚠️',
                    'semantic_similarity': '语义相似性',
                    'bleu': 'BLEU',
                    'rouge': 'ROUGE'
                };
                
                const displayNames = strategies.map(s => strategyNames[s] || s).join('、');
                $('#evaluationStrategiesDisplay').html(`<span class="badge bg-info">${displayNames}</span>`);
                $('#evaluationStrategiesInfo').show();
                
                // 更新评估模型必填状态
                this.updateEvaluationModelRequirement(strategies);
            } else {
                $('#evaluationStrategiesInfo').hide();
                this.updateEvaluationModelRequirement([]);
            }
        } catch (e) {
            console.error('显示评估策略失败:', e);
            $('#evaluationStrategiesInfo').hide();
            this.updateEvaluationModelRequirement([]);
        }
    }

    /**
     * 保存评估对比
     */
    async saveEvaluation() {
        const id = $('#evaluationRowId').val();
        const comparisonName = $('#comparisonName').val().trim();
        const comparisonDescription = $('#comparisonDescription').val().trim() || null;
        const testTaskId = $('#testTaskSelect').val();
        const evaluationModelId = $('#evaluationModelSelect').val() || null;
        const remarks = $('#evaluationRemarks').val().trim() || null;
        
        // 验证
        if (!comparisonName) {
            UIHelper.showToast('请填写对比名称', 'warning');
            return;
        }
        
        if (!id) {
            // 创建模式需要验证任务选择
            if (!testTaskId) {
                UIHelper.showToast('请选择测试任务', 'warning');
                return;
            }
            
            // 检查是否需要评估模型
            if ($('#evaluationModelSelect').attr('required') && !evaluationModelId) {
                UIHelper.showToast('当前评估策略包含需要 LLM 评估的策略，请选择评估模型', 'warning');
                return;
            }
        }
        
        let formData;
        
        if (id) {
            // 编辑模式：只能更新基本信息
            formData = {
                comparison_name: comparisonName,
                comparison_description: comparisonDescription,
                remarks: remarks
            };
        } else {
            // 创建模式
            formData = {
                comparison_name: comparisonName,
                comparison_description: comparisonDescription,
                test_task_id: testTaskId,
                evaluation_model_id: evaluationModelId,
                remarks: remarks
            };
        }
        
        try {
            $('#saveEvaluation').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                await ApiService.evaluations.update(id, formData);
                UIHelper.showToast('评估对比更新成功', 'success');
            } else {
                await ApiService.evaluations.create(formData);
                UIHelper.showToast('评估对比创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('evaluationModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveEvaluation').prop('disabled', false).html('保存');
        }
    }

    /**
     * 启动评估对比
     */
    async startEvaluation(id) {
        const confirmed = await UIHelper.confirmDialog(
            '确定要启动这个评估对比吗？\n\n系统将根据执行记录中配置的评估策略分别计算评估分数。',
            {
                title: '启动评估对比',
                confirmText: '确认启动',
                cancelText: '取消',
                confirmClass: 'btn-primary'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.evaluations.start(id);
            UIHelper.showToast('评估已启动', 'success');
            this.loadData();
            
            // 开始轮询状态
            this.startStatusPolling(id);
        } catch (error) {
            UIHelper.showToast('启动失败: ' + error.message, 'error');
        }
    }

    /**
     * 重启评估对比
     */
    async restartEvaluation(id, status) {
        let confirmMessage = '';
        let useForce = false;
        
        if (status === 'running') {
            // 运行中的评估需要询问是否强制重启
            confirmMessage = '这个评估正在运行中。\n\n' +
                '- 选择"普通重启"：需要评估超过10分钟未更新才能重启（更安全）\n' +
                '- 选择"强制重启"：立即重启，忽略时间限制（适合确认评估已卡住的情况）\n\n' +
                '建议先检查评估的更新时间，如果长时间无更新再重启。\n\n' +
                '您要强制重启吗？';
            
            const forceConfirmed = await UIHelper.confirmDialog(
                confirmMessage,
                {
                    title: '重启运行中的评估',
                    confirmText: '强制重启',
                    cancelText: '普通重启',
                    confirmClass: 'btn-warning'
                }
            );
            
            // 如果用户选择"普通重启"（false）或"强制重启"（true）
            if (forceConfirmed === null) {
                // Bootstrap modal 的 cancel 按钮会返回 false，我们需要区分
                // 这里假设点击 X 或背景关闭会返回 undefined，但实际可能需要调整
                return;
            }
            useForce = forceConfirmed === true;
        } else if (status === 'failed') {
            confirmMessage = '确定要重启这个失败的评估吗？\n\n系统将继续执行未完成的评估。';
        } else {
            confirmMessage = '确定要重启这个评估吗？\n\n系统将继续执行未完成的评估。';
        }
        
        const confirmed = await UIHelper.confirmDialog(
            confirmMessage,
            {
                title: '重启评估对比',
                confirmText: '确认重启',
                cancelText: '取消',
                confirmClass: 'btn-info'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.evaluations.restart(id, useForce);
            UIHelper.showToast('评估已重启', 'success');
            this.loadData();
            
            // 开始轮询状态
            this.startStatusPolling(id);
        } catch (error) {
            UIHelper.showToast('重启失败: ' + error.message, 'error');
        }
    }

    /**
     * 更新表格中的评估状态和进度
     * @param {string} id - 评估ID
     * @param {object} status - 状态对象
     */
    updateEvaluationInTable(id, status) {
        const row = $(`tr[data-evaluation-id="${id}"]`);
        if (row.length === 0) {
            return; // 评估不在当前页，跳过更新
        }
        
        // 更新状态徽章
        const statusBadge = this.getStatusBadge(status.status);
        row.find('.evaluation-status-cell').html(statusBadge);
        
        // 更新进度条
        const progress = status.total_pairs > 0 ? Math.round((status.completed_pairs / status.total_pairs) * 100) : 0;
        const progressBarClass = this.getProgressBarClass(status.status);
        
        row.find('.evaluation-progress-cell').html(`
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
                <small class="text-muted text-nowrap" style="min-width: 50px; text-align: right;">${status.completed_pairs}/${status.total_pairs}</small>
            </div>
        `);
    }

    /**
     * 开始状态轮询
     * @param {string} id - 评估ID
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
                const status = await ApiService.evaluations.getStatus(id);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(self.statusPollingInterval);
                    self.statusPollingInterval = null;
                    self.loadData();
                    
                    // 只在用户主动启动时显示通知
                    if (showNotification) {
                        if (status.status === 'completed') {
                            UIHelper.showToast('评估已完成', 'success');
                        } else {
                            UIHelper.showToast('评估失败', 'error');
                        }
                    }
                } else {
                    // 仍在运行中，打印进度并更新表格
                    console.log(`评估进度: ${status.progress_percentage}% (${status.completed_pairs}/${status.total_pairs})`);
                    // 更新表格中的评估状态和进度
                    self.updateEvaluationInTable(id, status);
                }
            } catch (error) {
                console.error('状态轮询失败:', error);
                clearInterval(self.statusPollingInterval);
                self.statusPollingInterval = null;
            }
        }, interval); // 使用传入的轮询间隔
    }

    /**
     * 检测并轮询运行中的评估
     */
    async startPollingForRunningEvaluations() {
        try {
            // 获取所有运行中的评估
            const response = await ApiService.evaluations.getAll({ 
                status: 'running',
                limit: 100 
            });
            
            if (response.items && response.items.length > 0) {
                // 如果有运行中的评估，为第一个评估启动轮询（使用10秒间隔）
                const runningEvaluation = response.items[0];
                console.log(`检测到运行中的评估: ${runningEvaluation.comparison_name}，开始后台轮询`);
                this.startStatusPolling(runningEvaluation.id, 10000, false);
            }
        } catch (error) {
            console.error('检测运行中评估失败:', error);
        }
    }

    /**
     * 查看评估详情
     */
    async viewEvaluation(id) {
        const self = this;
        
        try {
            // 获取评估基本信息
            const evaluation = await ApiService.evaluations.getById(id);
            
            // 创建详情模态框
            const modalHtml = `
                <div class="modal fade" id="evaluationDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">评估对比详情</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="evaluation-detail">
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <strong>对比名称：</strong>${evaluation.comparison_name}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>状态：</strong>${this.getStatusBadge(evaluation.status)}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-12">
                                            <strong>对比描述：</strong>${evaluation.comparison_description || '<em class="text-muted">无</em>'}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <strong>测试任务：</strong>${evaluation.test_task_name || '<em class="text-muted">未知</em>'}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>评估模型：</strong>${evaluation.evaluation_model_name || '<em class="text-muted">未使用</em>'}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-12">
                                            <strong>评估策略：</strong>${self.formatEvaluationStrategies(evaluation.evaluation_strategies)}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <strong>评估结果总数：</strong>${evaluation.total_pairs}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>已完成：</strong>${evaluation.completed_pairs}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-12">
                                            <strong>备注：</strong>${evaluation.remarks || '<em class="text-muted">无</em>'}
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <strong>创建时间：</strong>${UIHelper.formatDateTime(evaluation.created_at)}
                                        </div>
                                        <div class="col-md-6">
                                            <strong>更新时间：</strong>${UIHelper.formatDateTime(evaluation.updated_at)}
                                        </div>
                                    </div>
                                    
                                    <hr>
                                    
                                    <!-- 过滤器 -->
                                    <div class="row mb-3">
                                        <div class="col-md-3">
                                            <label class="form-label">评估策略：</label>
                                            <select id="resultStrategyFilter" class="form-select form-select-sm">
                                                <option value="">全部策略</option>
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">分数过滤：</label>
                                            <select id="resultScoreFilter" class="form-select form-select-sm">
                                                <option value="">全部</option>
                                                <option value="high">高 (≥0.8)</option>
                                                <option value="medium">中 (0.5-0.8)</option>
                                                <option value="low">低 (<0.5)</option>
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">状态过滤：</label>
                                            <select id="resultStatusFilter" class="form-select form-select-sm">
                                                <option value="">全部</option>
                                                <option value="success">成功</option>
                                                <option value="failed">失败</option>
                                                <option value="pending">待执行</option>
                                            </select>
                                        </div>
                                        <div class="col-md-3">
                                            <button id="applyResultFilters" class="btn btn-sm btn-primary" style="margin-top: 30px;">
                                                <i class="fas fa-filter"></i> 应用过滤
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h6 class="mb-0">评估结果</h6>
                                    </div>
                                    <div id="evaluationResultsContent">
                                        <div class="loading">
                                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                                                <span class="visually-hidden">加载中...</span>
                                            </div>
                                            <span class="ms-2">加载评估结果...</span>
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
            
            $('#evaluationDetailModal').remove();
            $('body').append(modalHtml);
            
            const modal = new bootstrap.Modal(document.getElementById('evaluationDetailModal'));
            modal.show();
            
            // 初始化结果分页变量
            let resultPage = 0;
            const resultPageSize = 10;
            let resultFilters = {};
            
            // 加载评估结果的函数
            const loadResults = async (page = 0, filters = {}) => {
                try {
                    $('#evaluationResultsContent').html(`
                        <div class="loading">
                            <div class="spinner-border spinner-border-sm text-primary" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <span class="ms-2">加载评估结果...</span>
                        </div>
                    `);
                    
                    const params = {
                        skip: page * resultPageSize,
                        limit: resultPageSize,
                        ...filters
                    };
                    
                    const resultsResponse = await ApiService.evaluations.getResults(id, params);
                    
                    if (resultsResponse.items.length === 0) {
                        $('#evaluationResultsContent').html('<p class="text-muted">暂无评估结果</p>');
                        return;
                    }
                    
                    // 渲染评估结果表格
                    let tableHtml = `
                        <table class="table table-sm table-hover evaluation-results-table">
                            <thead>
                                <tr>
                                    <th style="width: 3%"></th>
                                    <th style="width: 20%">用例名称</th>
                                    <th style="width: 12%">评估策略</th>
                                    <th style="width: 10%">状态</th>
                                    <th style="width: 10%">评估分数</th>
                                    <th style="width: 20%">模型输出</th>
                                    <th style="width: 20%">参考答案</th>
                                    <th style="width: 5%"></th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    resultsResponse.items.forEach((result) => {
                        const statusBadge = self.getResultStatusBadge(result.status);
                        const scoreDisplay = result.score !== null && result.score !== undefined
                            ? `<span class="badge ${self.getScoreBadgeClass(result.score)}">${result.score.toFixed(3)}</span>`
                            : '<em class="text-muted">-</em>';
                        
                        const modelOutputPreview = result.model_output ? self.truncateText(result.model_output, 60) : '<em class="text-muted">无</em>';
                        const referencePreview = result.reference_answer ? self.truncateText(result.reference_answer, 60) : '<em class="text-muted">无</em>';
                        
                        // 格式化策略名称
                        const strategyName = self.formatStrategyName(result.evaluation_strategy);
                        
                        const resultDetailId = `result-detail-${result.id}`;
                        
                        tableHtml += `
                            <tr class="result-row" data-result-id="${result.id}" style="cursor: pointer;">
                                <td>
                                    <i class="fas fa-chevron-right toggle-icon" id="toggle-${result.id}"></i>
                                </td>
                                <td><strong>${result.prompt_use_case_name || '<em class="text-muted">未知用例</em>'}</strong></td>
                                <td><span class="badge bg-secondary">${strategyName}</span></td>
                                <td>${statusBadge}</td>
                                <td>${scoreDisplay}</td>
                                <td><small class="text-muted">${modelOutputPreview}</small></td>
                                <td><small class="text-muted">${referencePreview}</small></td>
                                <td></td>
                            </tr>
                        `;
                        
                        // 格式化文本
                        const formatText = (text) => {
                            if (!text) return '<em class="text-muted">无内容</em>';
                            return text.replace(/</g, '&lt;')
                                      .replace(/>/g, '&gt;')
                                      .replace(/\n/g, '<br>')
                                      .replace(/  /g, '&nbsp;&nbsp;');
                        };
                        
                        // 解析结果详情
                        let resultDetails = '';
                        if (result.result_details) {
                            try {
                                const details = JSON.parse(result.result_details);
                                resultDetails = JSON.stringify(details, null, 2);
                            } catch (e) {
                                resultDetails = result.result_details;
                            }
                        }
                        
                        tableHtml += `
                            <tr class="result-detail" id="${resultDetailId}" style="display: none;">
                                <td colspan="8">
                                    <div class="card border-0 bg-light">
                                        <div class="card-body p-3">
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-robot text-primary"></i> 模型输出
                                                    </h6>
                                                    <div class="evaluation-output-content">${formatText(result.model_output)}</div>
                                                </div>
                                                <div class="col-md-6">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-check-circle text-success"></i> 参考答案
                                                    </h6>
                                                    <div class="evaluation-reference-content">${formatText(result.reference_answer)}</div>
                                                </div>
                                            </div>
                                            ${resultDetails ? `
                                            <div class="row mt-3">
                                                <div class="col-12">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-info-circle text-info"></i> 评估详情
                                                    </h6>
                                                    <div class="evaluation-detail-json">
                                                        <pre class="mb-0">${resultDetails}</pre>
                                                    </div>
                                                </div>
                                            </div>
                                            ` : ''}
                                            ${result.error_message ? `
                                            <div class="row mt-3">
                                                <div class="col-12">
                                                    <h6 class="mb-2">
                                                        <i class="fas fa-exclamation-triangle text-danger"></i> 错误信息
                                                    </h6>
                                                    <div class="alert alert-danger mb-0">
                                                        <small class="evaluation-error-message">${formatText(result.error_message)}</small>
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
                    const totalPages = Math.ceil(resultsResponse.total / resultPageSize);
                    if (totalPages > 1) {
                        tableHtml += `
                            <div class="pagination-info">
                                <div>
                                    <small>显示 ${page * resultPageSize + 1} - ${Math.min((page + 1) * resultPageSize, resultsResponse.total)} 
                                    / 共 ${resultsResponse.total} 条</small>
                                </div>
                                <nav>
                                    <ul class="pagination pagination-sm mb-0" id="resultPagination">
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
                    
                    $('#evaluationResultsContent').html(tableHtml);
                    
                    // 绑定展开/收起事件
                    $('.result-row').off('click').on('click', function() {
                        const resultId = $(this).data('result-id');
                        const detailRow = $(`#result-detail-${resultId}`);
                        const toggleIcon = $(`#toggle-${resultId}`);
                        
                        if (detailRow.is(':visible')) {
                            detailRow.hide();
                            toggleIcon.removeClass('fa-chevron-down').addClass('fa-chevron-right');
                        } else {
                            detailRow.show();
                            toggleIcon.removeClass('fa-chevron-right').addClass('fa-chevron-down');
                        }
                    });
                    
                    // 绑定分页点击事件
                    $('#resultPagination .page-link[data-page]').off('click').on('click', function(e) {
                        e.preventDefault();
                        const newPage = parseInt($(this).data('page'));
                        if (!isNaN(newPage) && newPage >= 0 && newPage < totalPages) {
                            resultPage = newPage;
                            loadResults(resultPage, resultFilters);
                        }
                    });
                    
                } catch (error) {
                    console.error('加载评估结果失败:', error);
                    $('#evaluationResultsContent').html(`
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle"></i>
                            加载评估结果失败，请稍后重试
                        </div>
                    `);
                }
            };
            
            // 填充策略过滤器选项
            const strategies = self.parseEvaluationStrategies(evaluation.evaluation_strategies);
            strategies.forEach(strategy => {
                const name = self.formatStrategyName(strategy);
                $('#resultStrategyFilter').append(`<option value="${strategy}">${name}</option>`);
            });
            
            // 绑定过滤器事件
            $(document).off('click', '#applyResultFilters').on('click', '#applyResultFilters', function() {
                resultFilters = {};
                
                const scoreFilter = $('#resultScoreFilter').val();
                if (scoreFilter === 'high') {
                    resultFilters.min_score = 0.8;
                } else if (scoreFilter === 'medium') {
                    resultFilters.min_score = 0.5;
                    resultFilters.max_score = 0.8;
                } else if (scoreFilter === 'low') {
                    resultFilters.max_score = 0.5;
                }
                
                const strategyFilter = $('#resultStrategyFilter').val();
                if (strategyFilter) {
                    resultFilters.evaluation_strategy = strategyFilter;
                }
                
                const statusFilter = $('#resultStatusFilter').val();
                if (statusFilter) {
                    resultFilters.status = statusFilter;
                }
                
                resultPage = 0;
                loadResults(resultPage, resultFilters);
            });
            
            // 初始加载评估结果
            loadResults(resultPage, resultFilters);
            
            // 模态框关闭后移除
            $('#evaluationDetailModal').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            UIHelper.showToast('加载评估详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 获取结果状态徽章
     */
    getResultStatusBadge(status) {
        const statusMap = {
            'pending': '<span class="badge bg-secondary">待执行</span>',
            'success': '<span class="badge bg-success">成功</span>',
            'failed': '<span class="badge bg-danger">失败</span>'
        };
        return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    /**
     * 查看统计信息
     */
    async viewStats(id) {
        const self = this;
        
        try {
            const stats = await ApiService.evaluations.getComprehensiveStats(id);
            
            // 创建统计模态框
            let modalHtml = `
                <div class="modal fade" id="evaluationStatsModal" tabindex="-1">
                    <div class="modal-dialog modal-fullscreen">
                        <div class="modal-content">
                            <div class="modal-header bg-primary text-white">
                                <h5 class="modal-title">
                                    <i class="fas fa-chart-line"></i> 评估统计报告 - ${stats.comparison_name}
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body bg-light">
                                <!-- 状态信息 -->
                                <div class="alert ${stats.status === 'completed' ? 'alert-success' : 'alert-warning'} mb-4">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>状态：</strong>${this.getStatusBadge(stats.status)}
                                    <span class="ms-3">
                                        <strong>评估对比ID：</strong>${stats.comparison_id}
                                    </span>
                                </div>
                                
                                <!-- 评估任务信息 -->
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <div class="card bg-light border-0">
                                            <div class="card-body">
                                                <h6 class="text-muted mb-2">
                                                    <i class="fas fa-tasks"></i> 测试任务
                                                </h6>
                                                <p class="mb-0 fw-bold">${stats.overall_stats.test_task_name || '<em class="text-muted">未知</em>'}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="card bg-light border-0">
                                            <div class="card-body">
                                                <h6 class="text-muted mb-2">
                                                    <i class="fas fa-brain"></i> 评估模型
                                                </h6>
                                                <p class="mb-0 fw-bold">${stats.overall_stats.evaluation_model_name || '<em class="text-muted">未使用</em>'}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 整体统计 -->
                                <h5 class="mb-3">
                                    <i class="fas fa-chart-bar"></i> 评估概况
                                </h5>
                                <div class="row mb-4">
                                    <div class="col-md-2">
                                        <div class="card border-primary h-100">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted mb-2 small">总用例数</h6>
                                                <h2 class="mb-0 text-primary">${stats.overall_stats.total_use_cases}</h2>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <div class="card border-info h-100">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted mb-2 small">总模板数</h6>
                                                <h2 class="mb-0 text-info">${stats.overall_stats.total_templates}</h2>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <div class="card border-secondary h-100">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted mb-2 small">评估对数</h6>
                                                <h2 class="mb-0 text-secondary">${stats.overall_stats.total_pairs || 0}</h2>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <div class="card border-success h-100">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted mb-2 small">成功</h6>
                                                <h2 class="mb-0 text-success">${stats.overall_stats.success_pairs || 0}</h2>
                                                <small class="text-muted">${stats.overall_stats.total_pairs > 0 ? ((stats.overall_stats.success_pairs / stats.overall_stats.total_pairs) * 100).toFixed(1) : 0}%</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <div class="card border-danger h-100">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted mb-2 small">失败</h6>
                                                <h2 class="mb-0 text-danger">${stats.overall_stats.failed_pairs || 0}</h2>
                                                <small class="text-muted">${stats.overall_stats.total_pairs > 0 ? ((stats.overall_stats.failed_pairs / stats.overall_stats.total_pairs) * 100).toFixed(1) : 0}%</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <div class="card border-warning h-100">
                                            <div class="card-body text-center">
                                                <h6 class="text-muted mb-2 small">已完成</h6>
                                                <h2 class="mb-0 text-warning">${stats.overall_stats.completed_pairs || 0}</h2>
                                                <small class="text-muted">${stats.overall_stats.total_pairs > 0 ? ((stats.overall_stats.completed_pairs / stats.overall_stats.total_pairs) * 100).toFixed(1) : 0}%</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 整体策略统计 -->
                                <h6 class="mb-3">整体评估策略得分</h6>
                                <div class="row mb-4">
            `;
            
            // 渲染整体策略统计
            const strategies = stats.overall_stats.strategies || {};
            for (const [strategy, strategyData] of Object.entries(strategies)) {
                const strategyName = this.formatStrategyName(strategy);
                const avgScore = strategyData.avg;
                const scoreClass = avgScore !== null ? this.getScoreTextClass(avgScore) : 'text-muted';
                
                modalHtml += `
                    <div class="col-md-4 col-lg-3 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h6 class="card-title text-truncate" title="${strategyName}">${strategyName}</h6>
                                <div class="d-flex justify-content-between align-items-end">
                                    <div>
                                        <small class="text-muted d-block">平均分</small>
                                        <h4 class="mb-0 ${scoreClass}">
                                            ${avgScore !== null ? avgScore.toFixed(4) : '-'}
                                        </h4>
                                    </div>
                                    <div class="text-end">
                                        <small class="text-muted d-block">范围</small>
                                        <small class="text-muted">
                                            ${strategyData.min !== null ? strategyData.min.toFixed(2) : '-'} ~ 
                                            ${strategyData.max !== null ? strategyData.max.toFixed(2) : '-'}
                                        </small>
                                        <small class="text-muted d-block">N=${strategyData.count}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            modalHtml += `
                                </div>
                                
                                <hr class="my-4">
                                
                                <!-- 模板统计 -->
                                <h5 class="mb-3">
                                    <i class="fas fa-layer-group"></i> 各模板详细统计
                                </h5>
            `;
            
            // 渲染各模板的统计
            if (stats.template_stats && stats.template_stats.length > 0) {
                stats.template_stats.forEach(template => {
                    modalHtml += `
                        <div class="card mb-3 border-0 shadow-sm">
                            <div class="card-header bg-white">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0">
                                        <i class="fas fa-file-alt text-primary"></i>
                                        <strong>${template.template_name || '未命名模板'}</strong>
                                        ${template.function_category ? `<span class="badge bg-info ms-2">${template.function_category}</span>` : ''}
                                    </h6>
                                    <span class="badge bg-secondary">${template.use_case_count} 个用例</span>
                                </div>
                            </div>
                            <div class="card-body">
                                <!-- LLM 参数配置 -->
                                ${template.max_tokens || template.temperature !== undefined || template.top_p !== undefined || template.top_k !== undefined ? `
                                <div class="mb-3">
                                    <h6 class="text-muted mb-2">
                                        <i class="fas fa-sliders-h"></i> LLM 参数配置
                                    </h6>
                                    <div class="row g-2">
                                        ${template.max_tokens ? `
                                        <div class="col-auto">
                                            <span class="badge bg-light text-dark border">
                                                <i class="fas fa-hashtag"></i> max_tokens: ${template.max_tokens}
                                            </span>
                                        </div>
                                        ` : ''}
                                        ${template.temperature !== undefined && template.temperature !== null ? `
                                        <div class="col-auto">
                                            <span class="badge bg-light text-dark border">
                                                <i class="fas fa-thermometer-half"></i> temperature: ${template.temperature}
                                            </span>
                                        </div>
                                        ` : ''}
                                        ${template.top_p !== undefined && template.top_p !== null ? `
                                        <div class="col-auto">
                                            <span class="badge bg-light text-dark border">
                                                <i class="fas fa-percentage"></i> top_p: ${template.top_p}
                                            </span>
                                        </div>
                                        ` : ''}
                                        ${template.top_k !== undefined && template.top_k !== null ? `
                                        <div class="col-auto">
                                            <span class="badge bg-light text-dark border">
                                                <i class="fas fa-sort-amount-down"></i> top_k: ${template.top_k}
                                            </span>
                                        </div>
                                        ` : ''}
                                    </div>
                                </div>
                                ` : ''}
                                
                                <!-- 提示词模板 -->
                                ${template.system_prompt || template.user_prompt ? `
                                <div class="mb-3">
                                    <button class="btn btn-sm btn-outline-secondary toggle-prompts" 
                                            data-template-id="${template.template_id}"
                                            type="button">
                                        <i class="fas fa-chevron-down"></i> 
                                        查看提示词模板
                                    </button>
                                    <div class="prompts-detail mt-2" 
                                         id="prompts-${template.template_id}" 
                                         style="display: none;">
                                        ${template.system_prompt ? `
                                        <div class="mb-2">
                                            <strong class="text-muted small">系统提示词：</strong>
                                            <div class="p-2 bg-light border rounded font-monospace small" 
                                                 style="max-height: 150px; overflow-y: auto; white-space: pre-wrap;">${self.escapeHtml(template.system_prompt)}</div>
                                        </div>
                                        ` : ''}
                                        ${template.user_prompt ? `
                                        <div>
                                            <strong class="text-muted small">用户提示词：</strong>
                                            <div class="p-2 bg-light border rounded font-monospace small" 
                                                 style="max-height: 150px; overflow-y: auto; white-space: pre-wrap;">${self.escapeHtml(template.user_prompt)}</div>
                                        </div>
                                        ` : ''}
                                    </div>
                                </div>
                                ` : ''}
                                
                                <!-- 模板策略统计 -->
                                <h6 class="text-muted mb-2">
                                    <i class="fas fa-chart-line"></i> 评估策略得分
                                </h6>
                                <div class="row mb-3">
                    `;
                    
                    // 模板各策略得分
                    for (const [strategy, strategyData] of Object.entries(template.strategies)) {
                        const strategyName = this.formatStrategyName(strategy);
                        const avgScore = strategyData.avg;
                        const scoreClass = avgScore !== null ? this.getScoreTextClass(avgScore) : 'text-muted';
                        
                        modalHtml += `
                            <div class="col-md-3 mb-2">
                                <div class="p-2 border rounded bg-light">
                                    <small class="text-muted d-block mb-1">${strategyName}</small>
                                    <div class="d-flex justify-content-between">
                                        <strong class="${scoreClass}">
                                            ${avgScore !== null ? avgScore.toFixed(4) : '-'}
                                        </strong>
                                        <small class="text-muted">N=${strategyData.count}</small>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    modalHtml += `
                                </div>
                                
                                <!-- 用例详情 -->
                                <div class="mt-3">
                                    <button class="btn btn-sm btn-outline-primary toggle-use-cases" 
                                            data-template-id="${template.template_id}"
                                            type="button">
                                        <i class="fas fa-chevron-down"></i> 
                                        查看用例详情 (${template.use_case_count})
                                    </button>
                                    <div class="use-cases-detail mt-3" 
                                         id="use-cases-${template.template_id}" 
                                         style="display: none;">
                                        <table class="table table-sm table-hover use-case-detail-table">
                                            <thead class="table-light">
                                                <tr>
                                                    <th style="width: 3%"></th>
                                                    <th style="width: 22%">用例名称</th>
                                                    <th style="width: 8%">响应时间</th>
                    `;
                    
                    // 动态生成策略列头
                    const templateStrategies = Object.keys(template.strategies);
                    const strategyColWidth = Math.floor(67 / templateStrategies.length);
                    templateStrategies.forEach(strategy => {
                        modalHtml += `<th style="width: ${strategyColWidth}%">${this.formatStrategyName(strategy)}</th>`;
                    });
                    
                    modalHtml += `
                                                </tr>
                                            </thead>
                                            <tbody>
                    `;
                    
                    // 渲染用例
                    template.use_cases.forEach((useCase, useCaseIndex) => {
                        const useCaseRowId = `use-case-row-${template.template_id}-${useCaseIndex}`;
                        const useCaseDetailId = `use-case-detail-${template.template_id}-${useCaseIndex}`;
                        
                        modalHtml += `
                            <tr class="use-case-row" data-detail-id="${useCaseDetailId}" style="cursor: pointer;">
                                <td><i class="fas fa-chevron-right toggle-icon-small"></i></td>
                                <td><strong>${useCase.use_case_name}</strong></td>
                                <td>
                                    ${useCase.response_time !== undefined && useCase.response_time !== null 
                                        ? `<span class="badge bg-light text-dark">${useCase.response_time.toFixed(2)}s</span>` 
                                        : '<span class="text-muted">-</span>'}
                                </td>
                        `;
                        
                        // 为每个策略显示得分
                        templateStrategies.forEach(strategy => {
                            const result = useCase.results.find(r => r.strategy === strategy);
                            if (result) {
                                const score = result.score;
                                const status = result.status;
                                
                                if (status === 'success' && score !== null) {
                                    const scoreClass = this.getScoreTextClass(score);
                                    modalHtml += `<td><span class="${scoreClass}">${score.toFixed(4)}</span></td>`;
                                } else if (status === 'failed') {
                                    modalHtml += `<td><span class="text-danger" title="${self.escapeHtml(result.error_message || '失败')}">失败</span></td>`;
                                } else {
                                    modalHtml += `<td><span class="text-muted">-</span></td>`;
                                }
                            } else {
                                modalHtml += `<td><span class="text-muted">-</span></td>`;
                            }
                        });
                        
                        modalHtml += `
                            </tr>
                        `;
                        
                        // 详细信息行（默认隐藏）
                        modalHtml += `
                            <tr class="use-case-detail-row" id="${useCaseDetailId}" style="display: none;">
                                <td colspan="${3 + templateStrategies.length}">
                                    <div class="p-3 bg-light border rounded">
                                        <div class="row">
                                            <!-- 渲染后的提示词 -->
                                            ${useCase.rendered_system_prompt || useCase.rendered_user_prompt ? `
                                            <div class="col-md-6 mb-3">
                                                <h6 class="text-muted mb-2">
                                                    <i class="fas fa-comment-dots"></i> 实际提示词
                                                </h6>
                                                ${useCase.rendered_system_prompt ? `
                                                <div class="mb-2">
                                                    <small class="text-muted fw-bold">系统：</small>
                                                    <div class="p-2 bg-white border rounded font-monospace" 
                                                         style="max-height: 120px; overflow-y: auto; font-size: 0.75rem; white-space: pre-wrap;">${self.escapeHtml(useCase.rendered_system_prompt)}</div>
                                                </div>
                                                ` : ''}
                                                ${useCase.rendered_user_prompt ? `
                                                <div>
                                                    <small class="text-muted fw-bold">用户：</small>
                                                    <div class="p-2 bg-white border rounded font-monospace" 
                                                         style="max-height: 120px; overflow-y: auto; font-size: 0.75rem; white-space: pre-wrap;">${self.escapeHtml(useCase.rendered_user_prompt)}</div>
                                                </div>
                                                ` : ''}
                                            </div>
                                            ` : ''}
                                            
                                            <!-- LLM 参数快照 -->
                                            ${useCase.llm_params ? `
                                            <div class="col-md-6 mb-3">
                                                <h6 class="text-muted mb-2">
                                                    <i class="fas fa-cog"></i> LLM 参数快照
                                                </h6>
                                                <div class="p-2 bg-white border rounded">
                                                    <div class="row g-1">
                                                        ${Object.entries(useCase.llm_params).map(([key, value]) => `
                                                        <div class="col-6">
                                                            <small class="text-muted">${key}:</small>
                                                            <strong class="ms-1">${value}</strong>
                                                        </div>
                                                        `).join('')}
                                                    </div>
                                                </div>
                                            </div>
                                            ` : ''}
                                        </div>
                                        
                                        <!-- 各策略的模型输出和参考答案 -->
                                        <div class="row">
                                            <div class="col-12">
                                                <h6 class="text-muted mb-2">
                                                    <i class="fas fa-balance-scale"></i> 评估对比详情
                                                </h6>
                                            </div>
                                        </div>
                                        ${useCase.results.map(result => {
                                            if (result.model_output || result.reference_answer) {
                                                return `
                                                <div class="row mb-2">
                                                    <div class="col-12">
                                                        <div class="card border-0 bg-white">
                                                            <div class="card-header py-1 px-2 bg-light">
                                                                <small class="fw-bold">${self.formatStrategyName(result.strategy)}</small>
                                                                ${result.score !== null ? `
                                                                <span class="ms-2 badge ${self.getScoreBadgeClass(result.score)}">${result.score.toFixed(4)}</span>
                                                                ` : ''}
                                                            </div>
                                                            <div class="card-body p-2">
                                                                <div class="row g-2">
                                                                    <div class="col-md-6">
                                                                        <small class="text-muted fw-bold d-block mb-1">
                                                                            <i class="fas fa-robot"></i> 模型输出
                                                                        </small>
                                                                        <div class="p-2 border rounded font-monospace" 
                                                                             style="max-height: 100px; overflow-y: auto; font-size: 0.7rem; white-space: pre-wrap; background-color: #f8f9fa;">${self.escapeHtml(result.model_output || '-')}</div>
                                                                    </div>
                                                                    <div class="col-md-6">
                                                                        <small class="text-muted fw-bold d-block mb-1">
                                                                            <i class="fas fa-check-circle"></i> 参考答案
                                                                        </small>
                                                                        <div class="p-2 border rounded font-monospace" 
                                                                             style="max-height: 100px; overflow-y: auto; font-size: 0.7rem; white-space: pre-wrap; background-color: #f8f9fa;">${self.escapeHtml(result.reference_answer || '-')}</div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                `;
                                            }
                                            return '';
                                        }).join('')}
                                        
                                        ${useCase.execution_error ? `
                                        <div class="row mt-2">
                                            <div class="col-12">
                                                <div class="alert alert-danger py-2 mb-0">
                                                    <small>
                                                        <i class="fas fa-exclamation-triangle"></i>
                                                        <strong>执行错误：</strong>${self.escapeHtml(useCase.execution_error)}
                                                    </small>
                                                </div>
                                            </div>
                                        </div>
                                        ` : ''}
                                    </div>
                                </td>
                            </tr>
                        `;
                    });
                    
                    modalHtml += `
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } else {
                modalHtml += '<p class="text-muted">暂无模板统计数据</p>';
            }
            
            modalHtml += `
                            </div>
                            <div class="modal-footer bg-white">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    <i class="fas fa-times"></i> 关闭
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            $('#evaluationStatsModal').remove();
            $('body').append(modalHtml);
            
            // 绑定展开/收起提示词模板事件
            $('.toggle-prompts').on('click', function() {
                const templateId = $(this).data('template-id');
                const detailDiv = $(`#prompts-${templateId}`);
                const icon = $(this).find('i');
                
                if (detailDiv.is(':visible')) {
                    detailDiv.slideUp();
                    icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
                    $(this).html('<i class="fas fa-chevron-down"></i> 查看提示词模板');
                } else {
                    detailDiv.slideDown();
                    icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
                    $(this).html('<i class="fas fa-chevron-up"></i> 收起提示词模板');
                }
            });
            
            // 绑定展开/收起用例详情事件
            $('.toggle-use-cases').on('click', function() {
                const templateId = $(this).data('template-id');
                const detailDiv = $(`#use-cases-${templateId}`);
                const icon = $(this).find('i');
                
                if (detailDiv.is(':visible')) {
                    detailDiv.slideUp();
                    icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
                    $(this).html('<i class="fas fa-chevron-down"></i> 查看用例详情 (' + detailDiv.parent().prev().find('.badge').text().match(/\d+/)[0] + ')');
                } else {
                    detailDiv.slideDown();
                    icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
                    $(this).html('<i class="fas fa-chevron-up"></i> 收起用例详情');
                }
            });
            
            // 绑定用例行点击展开详情
            $('.use-case-row').on('click', function() {
                const detailId = $(this).data('detail-id');
                const detailRow = $(`#${detailId}`);
                const icon = $(this).find('.toggle-icon-small');
                
                if (detailRow.is(':visible')) {
                    detailRow.hide();
                    icon.removeClass('fa-chevron-down').addClass('fa-chevron-right');
                } else {
                    detailRow.show();
                    icon.removeClass('fa-chevron-right').addClass('fa-chevron-down');
                }
            });
            
            const modal = new bootstrap.Modal(document.getElementById('evaluationStatsModal'));
            modal.show();
            
            // 模态框关闭后移除
            $('#evaluationStatsModal').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            console.error('加载统计信息失败:', error);
            UIHelper.showToast('加载统计信息失败: ' + error.message, 'error');
        }
    }

    /**
     * HTML 转义
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 获取分数文本颜色类
     */
    getScoreTextClass(score) {
        if (score === null || score === undefined) return '';
        if (score >= 0.8) return 'text-success';
        if (score >= 0.5) return 'text-info';
        if (score >= 0.3) return 'text-warning';
        return 'text-danger';
    }
    
    /**
     * 获取分数徽章颜色类
     */
    getScoreBadgeClass(score) {
        if (score >= 0.8) return 'bg-success';
        if (score >= 0.5) return 'bg-info';
        if (score >= 0.3) return 'bg-warning';
        return 'bg-danger';
    }
    
    /**
     * 格式化评估策略名称
     */
    formatStrategyName(strategy) {
        const strategyNames = {
            'exact_match': '精确匹配',
            'json_key_match': 'JSON 键匹配',
            'answer_accuracy': '答案准确率 ⚠️',
            'factual_correctness': '事实正确性 ⚠️',
            'semantic_similarity': '语义相似性',
            'bleu': 'BLEU',
            'rouge': 'ROUGE',
            'chrf': 'CHRF'
        };
        return strategyNames[strategy] || strategy;
    }
    
    /**
     * 解析评估策略 JSON
     */
    parseEvaluationStrategies(strategiesJson) {
        try {
            return JSON.parse(strategiesJson || '[]');
        } catch (e) {
            console.error('解析评估策略失败:', e);
            return [];
        }
    }
    
    /**
     * 格式化评估策略显示
     */
    formatEvaluationStrategies(strategiesJson) {
        const strategies = this.parseEvaluationStrategies(strategiesJson);
        if (strategies.length === 0) {
            return '<em class="text-muted">-</em>';
        }
        
        return strategies.map(s => {
            const name = this.formatStrategyName(s);
            return `<span class="badge bg-info me-1">${name}</span>`;
        }).join('');
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
     * 删除评估对比
     */
    async deleteEvaluation(id, name) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除评估对比 "${name}" 吗？\n\n⚠️ 此操作将删除所有相关的评估结果，且无法撤销。`,
            {
                title: '删除评估对比',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.evaluations.delete(id);
            UIHelper.showToast('评估对比删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
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
        $(document).off('click', '#addEvaluation');
        $(document).off('click', '#applyFilters');
        $(document).off('click', '#resetFilters');
        $(document).off('keypress', '#searchKeyword');
        $(document).off('click', '.view-evaluation');
        $(document).off('click', '.edit-evaluation');
        $(document).off('click', '.delete-evaluation');
        $(document).off('click', '.start-evaluation');
        $(document).off('click', '.restart-evaluation');
        $(document).off('click', '.view-stats');
        $(document).off('click', '#evaluationsTableContent .page-link[data-page]');
        $(document).off('click', '#saveEvaluation');
        $(document).off('click', '#applyResultFilters');
    }
}

