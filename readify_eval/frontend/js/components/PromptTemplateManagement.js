/**
 * 提示词模板管理组件
 * 负责提示词模板的增删改查操作
 */

class PromptTemplateManagement {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalItems = 0;
        this.currentFilters = {};
        this.systemDefaults = {}; // 存储系统默认配置
        this.aiModels = []; // 缓存AI模型列表
    }

    /**
     * 初始化组件
     */
    async init() {
        await this.render();
        await this.loadSystemDefaults(); // 加载系统默认配置
        await this.loadAIModels(); // 加载AI模型列表
        this.bindEvents();
        this.loadData();
    }
    
    /**
     * 加载系统默认配置
     */
    async loadSystemDefaults() {
        try {
            const codes = [
                'DEFAULT_SYSTEM_PROMPT',
                'DEFAULT_MAX_TOKENS',
                'DEFAULT_TOP_P',
                'DEFAULT_TOP_K',
                'DEFAULT_TEMPERATURE'
            ];
            
            const result = await ApiService.systemConfigs.getByCodes(codes);
            
            // 将配置转换为键值对存储
            result.items.forEach(config => {
                this.systemDefaults[config.config_code] = config.config_content;
            });
            
            console.log('系统默认配置加载成功:', this.systemDefaults);
        } catch (error) {
            console.error('加载系统默认配置失败:', error);
            UIHelper.showToast('加载系统默认配置失败，将使用空值', 'warning');
        }
    }

    /**
     * 加载AI模型列表
     */
    async loadAIModels() {
        try {
            const response = await ApiService.aiModels.getAll({ enabled_only: true, limit: 1000 });
            this.aiModels = response.items;
        } catch (error) {
            console.error('加载AI模型列表失败:', error);
            this.aiModels = [];
        }
    }

    /**
     * 填充AI模型下拉框
     */
    populateAIModelSelect(selectId) {
        let options = '<option value="">选择AI模型生成参考答案...</option>';
        this.aiModels.forEach(model => {
            options += `<option value="${model.id}">${model.model_name}</option>`;
        });
        $(selectId).html(options);
    }

    /**
     * 渲染页面结构
     */
    async render() {
        await TemplateLoader.loadInto('prompt-templates.html', 'content-area');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 添加模板按钮
        $(document).off('click', '#addPromptTemplate').on('click', '#addPromptTemplate', function() {
            self.showModal();
        });
        
        // 系统提示词模式切换
        $(document).off('change', '#systemPromptMode').on('change', '#systemPromptMode', function() {
            const mode = $(this).val();
            const previousMode = $(this).data('previous-mode') || 'default';
            
            if (mode === 'custom') {
                // 切换到自定义时，清空文本框并启用编辑，恢复placeholder
                $('#systemPrompt').prop('disabled', false).val('').attr('placeholder', '输入系统提示词...');
            } else if (mode === 'default') {
                // 切换到系统默认时，显示默认值并禁用编辑，设置提示文字
                $('#systemPrompt').prop('disabled', true).val(self.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '').attr('placeholder', '使用系统默认配置');
            } else {
                // 切换到"无"时，清空、禁用并清除placeholder
                $('#systemPrompt').prop('disabled', true).val('').attr('placeholder', '');
            }
            
            // 保存当前模式，用于下次切换时判断
            $(this).data('previous-mode', mode);
        });
        
        // 模型参数模式切换
        $(document).off('change', '#maxTokensMode').on('change', '#maxTokensMode', function() {
            const mode = $(this).val();
            if (mode === 'custom') {
                // 切换到自定义时，清空输入框并启用编辑
                $('#maxTokens').prop('disabled', false).val('').attr('placeholder', '输入最大Token数');
            } else if (mode === 'default') {
                // 切换到系统默认时，显示默认值并禁用编辑
                $('#maxTokens').prop('disabled', true).val(self.systemDefaults['DEFAULT_MAX_TOKENS'] || '').attr('placeholder', '使用系统默认');
            } else {
                // 切换到"无"时，清空、禁用并清除placeholder
                $('#maxTokens').prop('disabled', true).val('').attr('placeholder', '');
            }
        });
        
        $(document).off('change', '#temperatureMode').on('change', '#temperatureMode', function() {
            const mode = $(this).val();
            if (mode === 'custom') {
                // 切换到自定义时，清空输入框并启用编辑
                $('#temperature').prop('disabled', false).val('').attr('placeholder', '输入温度参数 (0-2)');
            } else if (mode === 'default') {
                // 切换到系统默认时，显示默认值并禁用编辑
                $('#temperature').prop('disabled', true).val(self.systemDefaults['DEFAULT_TEMPERATURE'] || '').attr('placeholder', '使用系统默认');
            } else {
                // 切换到"无"时，清空、禁用并清除placeholder
                $('#temperature').prop('disabled', true).val('').attr('placeholder', '');
            }
        });
        
        $(document).off('change', '#topPMode').on('change', '#topPMode', function() {
            const mode = $(this).val();
            if (mode === 'custom') {
                // 切换到自定义时，清空输入框并启用编辑
                $('#topP').prop('disabled', false).val('').attr('placeholder', '输入Top-P参数 (0-1)');
            } else if (mode === 'default') {
                // 切换到系统默认时，显示默认值并禁用编辑
                $('#topP').prop('disabled', true).val(self.systemDefaults['DEFAULT_TOP_P'] || '').attr('placeholder', '使用系统默认');
            } else {
                // 切换到"无"时，清空、禁用并清除placeholder
                $('#topP').prop('disabled', true).val('').attr('placeholder', '');
            }
        });
        
        $(document).off('change', '#topKMode').on('change', '#topKMode', function() {
            const mode = $(this).val();
            if (mode === 'custom') {
                // 切换到自定义时，清空输入框并启用编辑
                $('#topK').prop('disabled', false).val('').attr('placeholder', '输入Top-K参数');
            } else if (mode === 'default') {
                // 切换到系统默认时，显示默认值并禁用编辑
                $('#topK').prop('disabled', true).val(self.systemDefaults['DEFAULT_TOP_K'] || '').attr('placeholder', '使用系统默认');
            } else {
                // 切换到"无"时，清空、禁用并清除placeholder
                $('#topK').prop('disabled', true).val('').attr('placeholder', '');
            }
        });
        
        // 应用过滤
        $(document).off('click', '#applyTemplateFilters').on('click', '#applyTemplateFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetTemplateFilters').on('click', '#resetTemplateFilters', function() {
            $('#searchKeyword').val('');
            $('#filterOwner').val('');
            $('#filterQcNumber').val('');
            $('#filterPromptSource').val('');
            self.currentFilters = {};
            self.loadData();
        });
        
        // 搜索框回车
        $(document).off('keypress', '#searchKeyword').on('keypress', '#searchKeyword', function(e) {
            if (e.which === 13) {
                self.applyFilters();
            }
        });
        
        // 过滤输入框回车
        $(document).off('keypress', '#filterOwner, #filterQcNumber, #filterPromptSource').on('keypress', '#filterOwner, #filterQcNumber, #filterPromptSource', function(e) {
            if (e.which === 13) {
                self.applyFilters();
            }
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-template').on('click', '.edit-template', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-template').on('click', '.delete-template', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            self.deleteTemplate(id, name);
        });
        
        // 查看详情按钮
        $(document).off('click', '.view-template').on('click', '.view-template', function() {
            const id = $(this).data('id');
            self.viewTemplate(id);
        });
        
        // 查看用例按钮
        $(document).off('click', '.view-use-cases').on('click', '.view-use-cases', function() {
            const templateId = $(this).data('id');
            const templateName = $(this).data('name');
            self.viewUseCases(templateId, templateName);
        });
        
        // 创建用例按钮
        $(document).off('click', '.create-use-case').on('click', '.create-use-case', function() {
            const templateId = $(this).data('id');
            const templateName = $(this).data('name');
            self.showCreateUseCaseModal(templateId, templateName);
        });
        
        // 保存模板
        $(document).off('click', '#savePromptTemplate').on('click', '#savePromptTemplate', function() {
            self.saveTemplate();
        });
        
        // 分页按钮（仅限主列表的分页）
        $(document).off('click', '#promptTemplatesTableContent .page-link[data-page]').on('click', '#promptTemplatesTableContent .page-link[data-page]', function(e) {
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
        
        const owner = $('#filterOwner').val().trim();
        if (owner) {
            this.currentFilters.owner = owner;
        }
        
        const qcNumber = $('#filterQcNumber').val().trim();
        if (qcNumber) {
            this.currentFilters.qc_number = qcNumber;
        }
        
        const promptSource = $('#filterPromptSource').val().trim();
        if (promptSource) {
            this.currentFilters.prompt_source = promptSource;
        }
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#promptTemplatesTableContent').html(`
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
            
            const response = await ApiService.promptTemplates.getAll(params);
            
            this.totalItems = response.total;
            this.renderTable(response.items);
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#promptTemplatesTableContent').html(`
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
            $('#promptTemplatesTableContent').html(`
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
                        <th style="width: 12%">模板名称</th>
                        <th style="width: 18%">系统提示词</th>
                        <th style="width: 18%">用户提示词</th>
                        <th style="width: 8%">功能分类</th>
                        <th style="width: 8%">负责人</th>
                        <th style="width: 8%">QC号</th>
                        <th style="width: 8%">提示词来源</th>
                        <th style="width: 10%">创建时间</th>
                        <th style="width: 10%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            // 处理系统提示词的显示
            let systemPromptDisplay = item.system_prompt;
            let systemPromptTitle = item.system_prompt || '';
            
            if (item.system_prompt === '__NONE__') {
                systemPromptDisplay = '<em class="text-muted">无</em>';
                systemPromptTitle = '';
            } else if (item.system_prompt === '__USE_SYSTEM_DEFAULT__') {
                const defaultValue = this.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '';
                systemPromptDisplay = defaultValue ? `<span class="badge bg-primary">系统默认</span> ${this.truncateText(defaultValue, 80)}` : '<span class="badge bg-primary">系统默认</span>';
                systemPromptTitle = defaultValue;
            } else if (!item.system_prompt) {
                systemPromptDisplay = '<em class="text-muted">无</em>';
                systemPromptTitle = '';
            }
            
            // 截断长文本并添加提示
            const systemPrompt = this.truncateText(systemPromptDisplay, 80);
            const userPrompt = this.truncateText(item.user_prompt || '<em class="text-muted">无</em>', 80);
            const functionCategory = item.function_category || '<em class="text-muted">未分类</em>';
            const owner = item.owner || '<em class="text-muted">-</em>';
            const qcNumber = item.qc_number || '<em class="text-muted">-</em>';
            const promptSource = item.prompt_source || '<em class="text-muted">-</em>';
            
            tableHtml += `
                <tr>
                    <td><strong>${item.template_name}</strong></td>
                    <td><div class="text-truncate-cell" title="${this.escapeHtml(systemPromptTitle)}">${systemPrompt}</div></td>
                    <td><div class="text-truncate-cell" title="${this.escapeHtml(item.user_prompt || '')}">${userPrompt}</div></td>
                    <td>${functionCategory}</td>
                    <td>${owner}</td>
                    <td>${qcNumber}</td>
                    <td>${promptSource}</td>
                    <td>${UIHelper.formatDateTime(item.created_at)}</td>
                    <td class="action-buttons">
                        <button class="btn btn-sm btn-outline-success view-use-cases" data-id="${item.id}" data-name="${item.template_name}" title="查看用例">
                            <i class="fas fa-list"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info view-template" data-id="${item.id}" title="查看详情">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary edit-template" data-id="${item.id}" title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-template" data-id="${item.id}" data-name="${item.template_name}" title="删除">
                            <i class="fas fa-trash"></i>
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
        
        $('#promptTemplatesTableContent').html(tableHtml);
    }

    /**
     * 截断文本
     */
    truncateText(text, maxLength) {
        if (!text || text.startsWith('<em')) return text;
        
        const strippedText = text.replace(/<[^>]*>/g, ''); // 移除HTML标签
        if (strippedText.length <= maxLength) {
            return text;
        }
        return strippedText.substring(0, maxLength) + '...';
    }

    /**
     * 转义HTML（用于在HTML属性中安全显示文本）
     */
    escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
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
     * 显示创建用例模态框
     */
    async showCreateUseCaseModal(templateId, templateName, onSuccess) {
        const self = this;
        
        // 获取模板详情
        let template = null;
        try {
            template = await ApiService.promptTemplates.getById(templateId);
        } catch (error) {
            UIHelper.showToast('加载模板数据失败: ' + error.message, 'error');
            return;
        }
        
        // 创建模态框HTML（参照提示词用例的添加用例模态框）
        const modalHtml = `
            <div class="modal fade" id="createUseCaseFromTemplateModal" tabindex="-1">
                <div class="modal-dialog modal-use-cases">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">添加提示词用例</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="createUseCaseFromTemplateForm">
                                <input type="hidden" id="newUseCaseTemplateId" value="${templateId}">
                                
                                <div class="row">
                                    <!-- 左侧：表单 -->
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="newUseCaseName" class="form-label">用例名称 <span class="text-danger">*</span></label>
                                            <input type="text" class="form-control" id="newUseCaseName" required>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="newUseCaseTemplateDisplay" class="form-label">关联模板 <span class="text-danger">*</span></label>
                                            <input type="text" class="form-control" id="newUseCaseTemplateDisplay" value="${templateName}" readonly disabled>
                                        </div>

                                        <div class="mb-3">
                                            <label class="form-label">模板变量</label>
                                            <div id="newUseCaseVariablesContainer">
                                                <p class="text-muted">正在加载...</p>
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="newUseCaseReferenceAnswer" class="form-label">参考答案</label>
                                            <div class="d-flex gap-2 mb-2">
                                                <select class="form-select flex-grow-1" id="newUseCaseAiModelSelect">
                                                    <option value="">选择AI模型生成参考答案...</option>
                                                </select>
                                                <button class="btn btn-primary" type="button" id="generateNewUseCaseReferenceAnswer" disabled style="min-width: 120px;">
                                                    <i class="fas fa-magic me-1"></i>模型生成
                                                </button>
                                            </div>
                                            <textarea class="form-control" id="newUseCaseReferenceAnswer" rows="6" placeholder="输入参考答案..."></textarea>
                                            <div class="form-text">可选：用于评估的参考答案或标准答案。选择AI模型并填写完变量后可自动生成</div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="newUseCaseRemarks" class="form-label">备注</label>
                                            <textarea class="form-control" id="newUseCaseRemarks" rows="3" placeholder="输入备注信息..."></textarea>
                                            <div class="form-text">可选：关于该用例的额外说明</div>
                                        </div>
                                    </div>

                                    <!-- 右侧：模板预览 -->
                                    <div class="col-md-6">
                                        <div class="template-preview-panel">
                                            <h6 class="mb-3">模板预览</h6>
                                            <div id="newUseCaseTemplatePreview">
                                                <p class="text-muted">正在加载...</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="saveNewUseCase">保存</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除旧的模态框（如果存在）
        $('#createUseCaseFromTemplateModal').remove();
        
        // 添加新的模态框
        $('body').append(modalHtml);
        
        // 填充AI模型下拉框
        this.populateAIModelSelect('#newUseCaseAiModelSelect');
        
        // 显示模板预览并生成变量输入框
        this.showTemplatePreviewForNewUseCase(template);
        
        // 绑定变量值输入变化 - 实时渲染预览和更新生成按钮状态
        $(document).off('input', '#createUseCaseFromTemplateModal .variable-value').on('input', '#createUseCaseFromTemplateModal .variable-value', function() {
            self.renderPreviewForNewUseCase(template);
            self.updateNewUseCaseGenerateButtonState();
        });

        // AI模型选择变化 - 启用/禁用生成按钮
        $(document).off('change', '#newUseCaseAiModelSelect').on('change', '#newUseCaseAiModelSelect', function() {
            self.updateNewUseCaseGenerateButtonState();
        });

        // AI生成参考答案
        $(document).off('click', '#generateNewUseCaseReferenceAnswer').on('click', '#generateNewUseCaseReferenceAnswer', function() {
            self.generateNewUseCaseReferenceAnswer(template);
        });

        // 绑定预览切换按钮
        $(document).off('click', '#createUseCaseFromTemplateModal .preview-tab').on('click', '#createUseCaseFromTemplateModal .preview-tab', function() {
            if (!$(this).hasClass('active')) {
                $('#createUseCaseFromTemplateModal .preview-tab').removeClass('active');
                $(this).addClass('active');
                const mode = $(this).data('mode');
                if (mode === 'template') {
                    $('#newUseCaseTemplateSection').fadeIn(200);
                    $('#newUseCaseRenderedSection').fadeOut(200);
                } else {
                    $('#newUseCaseTemplateSection').fadeOut(200);
                    $('#newUseCaseRenderedSection').fadeIn(200);
                }
            }
        });
        
        // 绑定保存按钮
        $(document).off('click', '#saveNewUseCase').on('click', '#saveNewUseCase', async function() {
            await self.saveNewUseCase(onSuccess);
        });
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('createUseCaseFromTemplateModal'));
        modal.show();
        
        // 模态框关闭后移除并清理事件
        $('#createUseCaseFromTemplateModal').on('hidden.bs.modal', function() {
            $(document).off('input', '#createUseCaseFromTemplateModal .variable-value');
            $(document).off('click', '#createUseCaseFromTemplateModal .preview-tab');
            $(document).off('click', '#saveNewUseCase');
            $(this).remove();
        });
    }

    /**
     * 显示模板预览（用于新建用例）
     */
    showTemplatePreviewForNewUseCase(template) {
        // 生成变量输入框
        this.generateVariableInputsForNewUseCase(template);
        
        // 渲染模板预览
        this.renderPreviewForNewUseCase(template);
    }

    /**
     * 生成变量输入框（用于新建用例）
     */
    generateVariableInputsForNewUseCase(template) {
        const variables = this.extractVariablesFromTemplate(template);
        const container = $('#newUseCaseVariablesContainer');
        
        container.empty();
        
        if (variables.length === 0) {
            container.html('<p class="text-muted">此模板没有定义变量</p>');
            return;
        }
        
        // 为每个变量生成输入控件（改为多行文本框）
        variables.forEach(varName => {
            const rowHtml = `
                <div class="variable-row mb-2">
                    <div class="row g-2">
                        <div class="col-md-4">
                            <input type="text" class="form-control variable-key" value="${varName}" readonly>
                        </div>
                        <div class="col-md-8">
                            <textarea class="form-control variable-value" placeholder="请输入 ${varName} 的值" data-var="${varName}" rows="3"></textarea>
                        </div>
                    </div>
                </div>
            `;
            container.append(rowHtml);
        });
    }

    /**
     * 从模板中提取变量
     * 按照变量在模板中首次出现的顺序返回（先系统提示词，后用户提示词）
     */
    extractVariablesFromTemplate(template) {
        const variables = [];
        const seen = new Set();
        const regex = /<\$([a-zA-Z0-9_]+)>/g;
        
        // 从系统提示词中提取（保持首次出现顺序）
        if (template.system_prompt) {
            let match;
            while ((match = regex.exec(template.system_prompt)) !== null) {
                const varName = match[1];
                if (!seen.has(varName)) {
                    seen.add(varName);
                    variables.push(varName);
                }
            }
        }
        
        // 从用户提示词中提取（保持首次出现顺序）
        if (template.user_prompt) {
            regex.lastIndex = 0;
            let match;
            while ((match = regex.exec(template.user_prompt)) !== null) {
                const varName = match[1];
                if (!seen.has(varName)) {
                    seen.add(varName);
                    variables.push(varName);
                }
            }
        }
        
        return variables;
    }

    /**
     * 渲染预览（用于新建用例）
     */
    renderPreviewForNewUseCase(template) {
        // 收集当前的变量值
        const variables = {};
        $('#newUseCaseVariablesContainer .variable-value').each(function() {
            const key = $(this).data('var');
            const value = $(this).val().trim();
            if (key) {
                variables[key] = value;
            }
        });
        
        // 渲染系统提示词
        const renderedSystemPrompt = this.renderTextForView(template.system_prompt, variables);
        
        // 渲染用户提示词
        const renderedUserPrompt = this.renderTextForView(template.user_prompt, variables);

        const previewHtml = `
            <div class="template-preview-content">
                <!-- 切换标签 -->
                <div class="preview-tabs mb-3">
                    <button type="button" class="preview-tab" data-mode="template">
                        <i class="fas fa-file-code"></i> 模板
                    </button>
                    <button type="button" class="preview-tab active" data-mode="rendered">
                        <i class="fas fa-eye"></i> 预览
                    </button>
                </div>

                <!-- 原始模板 -->
                <div class="preview-section" id="newUseCaseTemplateSection" style="display: none;">
                    <div class="template-text-original">
                        <div class="mb-3">
                            <strong class="text-primary">系统提示词模板：</strong>
                            <div class="template-text-display">${this.formatTemplateDisplay(template.system_prompt)}</div>
                        </div>
                        <div>
                            <strong class="text-primary">用户提示词模板：</strong>
                            <div class="template-text-display">${template.user_prompt || '<em class="text-muted">无</em>'}</div>
                        </div>
                    </div>
                </div>

                <!-- 实时渲染预览 -->
                <div class="preview-section" id="newUseCaseRenderedSection">
                    <div class="rendered-preview">
                        <div class="mb-3">
                            <strong class="text-success">渲染后系统提示词：</strong>
                            <div class="rendered-text" id="newUseCaseRenderedSystemPrompt">${renderedSystemPrompt}</div>
                        </div>
                        <div>
                            <strong class="text-success">渲染后用户提示词：</strong>
                            <div class="rendered-text" id="newUseCaseRenderedUserPrompt">${renderedUserPrompt}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('#newUseCaseTemplatePreview').html(previewHtml);
    }

    /**
     * 保存新建的用例
     */
    async saveNewUseCase(onSuccess) {
        const templateId = $('#newUseCaseTemplateId').val();
        const useCaseName = $('#newUseCaseName').val().trim();
        const referenceAnswer = $('#newUseCaseReferenceAnswer').val().trim() || null;
        const remarks = $('#newUseCaseRemarks').val().trim() || null;
        
        // 验证
        if (!useCaseName) {
            UIHelper.showToast('请填写用例名称', 'warning');
            return;
        }

        if (!templateId) {
            UIHelper.showToast('请选择提示词模板', 'warning');
            return;
        }
        
        // 收集变量
        const variables = {};
        let hasVariables = false;
        $('#newUseCaseVariablesContainer .variable-value').each(function() {
            const key = $(this).data('var');
            const value = $(this).val().trim();
            if (key) {
                variables[key] = value;
                hasVariables = true;
            }
        });
        
        const formData = {
            use_case_name: useCaseName,
            template_id: templateId,
            template_variables: hasVariables ? variables : null,
            reference_answer: referenceAnswer,
            remarks: remarks
        };
        
        try {
            $('#saveNewUseCase').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            await ApiService.promptUseCases.create(formData);
            UIHelper.showToast('用例创建成功', 'success');
            
            bootstrap.Modal.getInstance(document.getElementById('createUseCaseFromTemplateModal')).hide();
            
            // 调用成功回调，刷新用例列表
            if (onSuccess) {
                onSuccess();
            }
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveNewUseCase').prop('disabled', false).html('保存');
        }
    }

    /**
     * 查看模板关联的用例
     */
    async viewUseCases(templateId, templateName) {
        const self = this;
        
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal fade" id="templateUseCasesModal" tabindex="-1">
                <div class="modal-dialog modal-use-cases">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">模板关联用例 - ${templateName}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3 d-flex justify-content-end">
                                <button class="btn btn-primary" id="createUseCaseInModal" data-template-id="${templateId}" data-template-name="${templateName}">
                                    <i class="fas fa-plus"></i> 创建用例
                                </button>
                            </div>
                            <div id="useCasesTableContent">
                                <div class="loading">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">加载中...</span>
                                    </div>
                                    <p class="mt-3">加载用例数据中...</p>
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
        
        // 移除旧的模态框（如果存在）
        $('#templateUseCasesModal').remove();
        
        // 添加新的模态框
        $('body').append(modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('templateUseCasesModal'));
        modal.show();
        
        // 初始化分页状态
        let currentPage = 0;
        const pageSize = 10;
        
        // 加载用例数据的函数
        const loadUseCases = async (page = 0) => {
            try {
                $('#useCasesTableContent').html(`
                    <div class="loading">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <p class="mt-3">加载用例数据中...</p>
                    </div>
                `);
                
                const params = {
                    template_id: templateId,
                    skip: page * pageSize,
                    limit: pageSize
                };
                
                const response = await ApiService.promptUseCases.getAll(params);
                
                if (response.items.length === 0) {
                    $('#useCasesTableContent').html(`
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <p>该模板暂无关联用例</p>
                        </div>
                    `);
                    return;
                }
                
                // 渲染用例表格
                let tableHtml = `
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th style="width: 20%">用例名称</th>
                                <th style="width: 27%">渲染后系统提示词</th>
                                <th style="width: 27%">渲染后用户提示词</th>
                                <th style="width: 13%">更新时间</th>
                                <th style="width: 13%">操作</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                response.items.forEach(item => {
                    // 处理渲染后的系统提示词显示
                    let systemPromptDisplay = item.rendered_system_prompt;
                    let systemPromptTitle = item.rendered_system_prompt || '';
                    
                    if (item.rendered_system_prompt === '__NONE__' || !item.rendered_system_prompt) {
                        systemPromptDisplay = '<em class="text-muted">无</em>';
                        systemPromptTitle = '';
                    } else if (item.rendered_system_prompt === '__USE_SYSTEM_DEFAULT__') {
                        const defaultValue = self.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '';
                        systemPromptDisplay = defaultValue ? 
                            `<span class="badge bg-primary">系统默认</span> ${self.truncateText(defaultValue, 60)}` : 
                            '<span class="badge bg-primary">系统默认</span> <em class="text-muted">（未配置）</em>';
                        systemPromptTitle = defaultValue;
                    }
                    
                    const renderedSystemPrompt = self.truncateText(systemPromptDisplay, 80);
                    const renderedUserPrompt = self.truncateText(item.rendered_user_prompt || '<em class="text-muted">无</em>', 80);
                    
                    tableHtml += `
                        <tr>
                            <td><strong>${item.use_case_name}</strong></td>
                            <td><div class="text-truncate-cell" title="${self.escapeHtml(systemPromptTitle)}">${renderedSystemPrompt}</div></td>
                            <td><div class="text-truncate-cell" title="${self.escapeHtml(item.rendered_user_prompt || '')}">${renderedUserPrompt}</div></td>
                            <td>${UIHelper.formatDateTime(item.updated_at)}</td>
                            <td class="action-buttons">
                                <button class="btn btn-sm btn-outline-info view-use-case-detail" data-id="${item.id}" title="查看详情">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-primary edit-use-case-in-modal" data-id="${item.id}" data-template-id="${templateId}" data-template-name="${templateName}" title="编辑">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger delete-use-case-in-modal" data-id="${item.id}" data-name="${item.use_case_name}" title="删除">
                                    <i class="fas fa-trash"></i>
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
                const totalPages = Math.ceil(response.total / pageSize);
                if (totalPages > 1) {
                    tableHtml += `
                        <div class="pagination-info">
                            <div>
                                显示 ${page * pageSize + 1} - ${Math.min((page + 1) * pageSize, response.total)} 
                                / 共 ${response.total} 条
                            </div>
                            <nav>
                                <ul class="pagination mb-0" id="useCasesPagination">
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
                
                $('#useCasesTableContent').html(tableHtml);
                
                // 绑定分页点击事件
                $('#useCasesPagination .page-link[data-page]').off('click').on('click', function(e) {
                    e.preventDefault();
                    const newPage = parseInt($(this).data('page'));
                    if (!isNaN(newPage) && newPage >= 0 && newPage < totalPages) {
                        currentPage = newPage;
                        loadUseCases(currentPage);
                    }
                });
                
                // 绑定查看用例详情按钮
                $('.view-use-case-detail').off('click').on('click', function() {
                    const useCaseId = $(this).data('id');
                    self.viewUseCaseDetail(useCaseId);
                });
                
                // 绑定编辑用例按钮
                $('.edit-use-case-in-modal').off('click').on('click', function() {
                    const useCaseId = $(this).data('id');
                    const templateId = $(this).data('template-id');
                    const templateName = $(this).data('template-name');
                    self.showEditUseCaseModal(useCaseId, templateId, templateName, () => {
                        loadUseCases(currentPage);
                    });
                });
                
                // 绑定删除用例按钮
                $('.delete-use-case-in-modal').off('click').on('click', async function() {
                    const useCaseId = $(this).data('id');
                    const useCaseName = $(this).data('name');
                    await self.deleteUseCaseInModal(useCaseId, useCaseName, () => {
                        loadUseCases(currentPage);
                    });
                });
                
            } catch (error) {
                UIHelper.showToast('加载用例数据失败: ' + error.message, 'error');
                $('#useCasesTableContent').html(`
                    <div class="empty-state">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>加载数据失败，请稍后重试</p>
                    </div>
                `);
            }
        };
        
        // 初始加载
        loadUseCases(currentPage);
        
        // 绑定创建用例按钮
        $(document).off('click', '#createUseCaseInModal').on('click', '#createUseCaseInModal', function() {
            const tid = $(this).data('template-id');
            const tname = $(this).data('template-name');
            self.showCreateUseCaseModal(tid, tname, () => {
                loadUseCases(currentPage);
            });
        });
        
        // 模态框关闭后移除
        $('#templateUseCasesModal').on('hidden.bs.modal', function() {
            $(document).off('click', '#createUseCaseInModal');
            $(this).remove();
        });
    }

    /**
     * 编辑用例（在查看用例模态框中调用）
     */
    async showEditUseCaseModal(useCaseId, templateId, templateName, onSuccess) {
        const self = this;
        
        // 获取用例详情
        let useCase = null;
        try {
            useCase = await ApiService.promptUseCases.getById(useCaseId);
        } catch (error) {
            UIHelper.showToast('加载用例数据失败: ' + error.message, 'error');
            return;
        }
        
        // 获取模板详情
        let template = null;
        try {
            template = await ApiService.promptTemplates.getById(templateId);
        } catch (error) {
            UIHelper.showToast('加载模板数据失败: ' + error.message, 'error');
            return;
        }
        
        // 创建编辑模态框HTML
        const modalHtml = `
            <div class="modal fade" id="editUseCaseFromTemplateModal" tabindex="-1">
                <div class="modal-dialog modal-use-cases">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">编辑提示词用例</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editUseCaseFromTemplateForm">
                                <input type="hidden" id="editUseCaseId" value="${useCaseId}">
                                <input type="hidden" id="editUseCaseTemplateId" value="${templateId}">
                                
                                <div class="row">
                                    <!-- 左侧：表单 -->
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="editUseCaseName" class="form-label">用例名称 <span class="text-danger">*</span></label>
                                            <input type="text" class="form-control" id="editUseCaseName" value="${useCase.use_case_name}" required>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="editUseCaseTemplateDisplay" class="form-label">关联模板 <span class="text-danger">*</span></label>
                                            <input type="text" class="form-control" id="editUseCaseTemplateDisplay" value="${templateName}" readonly disabled>
                                        </div>

                                        <div class="mb-3">
                                            <label class="form-label">模板变量</label>
                                            <div id="editUseCaseVariablesContainer">
                                                <p class="text-muted">正在加载...</p>
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="editUseCaseReferenceAnswer" class="form-label">参考答案</label>
                                            <div class="d-flex gap-2 mb-2">
                                                <select class="form-select flex-grow-1" id="editUseCaseAiModelSelect">
                                                    <option value="">选择AI模型生成参考答案...</option>
                                                </select>
                                                <button class="btn btn-primary" type="button" id="generateEditUseCaseReferenceAnswer" disabled style="min-width: 120px;">
                                                    <i class="fas fa-magic me-1"></i>模型生成
                                                </button>
                                            </div>
                                            <textarea class="form-control" id="editUseCaseReferenceAnswer" rows="6" placeholder="输入参考答案...">${useCase.reference_answer || ''}</textarea>
                                            <div class="form-text">可选：用于评估的参考答案或标准答案。选择AI模型并填写完变量后可自动生成</div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="editUseCaseRemarks" class="form-label">备注</label>
                                            <textarea class="form-control" id="editUseCaseRemarks" rows="3" placeholder="输入备注信息...">${useCase.remarks || ''}</textarea>
                                            <div class="form-text">可选：关于该用例的额外说明</div>
                                        </div>
                                    </div>

                                    <!-- 右侧：模板预览 -->
                                    <div class="col-md-6">
                                        <div class="template-preview-panel">
                                            <h6 class="mb-3">模板预览</h6>
                                            <div id="editUseCaseTemplatePreview">
                                                <p class="text-muted">正在加载...</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="saveEditUseCase">保存</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 移除旧的模态框（如果存在）
        $('#editUseCaseFromTemplateModal').remove();
        
        // 添加新的模态框
        $('body').append(modalHtml);
        
        // 填充AI模型下拉框
        this.populateAIModelSelect('#editUseCaseAiModelSelect');
        
        // 显示模板预览并生成变量输入框（带已有值）
        this.showTemplatePreviewForEditUseCase(template, useCase.template_variables || {});
        
        // 绑定变量值输入变化 - 实时渲染预览和更新生成按钮状态
        $(document).off('input', '#editUseCaseFromTemplateModal .variable-value').on('input', '#editUseCaseFromTemplateModal .variable-value', function() {
            self.renderPreviewForEditUseCase(template);
            self.updateEditUseCaseGenerateButtonState();
        });

        // AI模型选择变化 - 启用/禁用生成按钮
        $(document).off('change', '#editUseCaseAiModelSelect').on('change', '#editUseCaseAiModelSelect', function() {
            self.updateEditUseCaseGenerateButtonState();
        });

        // AI生成参考答案
        $(document).off('click', '#generateEditUseCaseReferenceAnswer').on('click', '#generateEditUseCaseReferenceAnswer', function() {
            self.generateEditUseCaseReferenceAnswer(template);
        });

        // 绑定预览切换按钮
        $(document).off('click', '#editUseCaseFromTemplateModal .preview-tab').on('click', '#editUseCaseFromTemplateModal .preview-tab', function() {
            if (!$(this).hasClass('active')) {
                $('#editUseCaseFromTemplateModal .preview-tab').removeClass('active');
                $(this).addClass('active');
                const mode = $(this).data('mode');
                if (mode === 'template') {
                    $('#editUseCaseTemplateSection').fadeIn(200);
                    $('#editUseCaseRenderedSection').fadeOut(200);
                } else {
                    $('#editUseCaseTemplateSection').fadeOut(200);
                    $('#editUseCaseRenderedSection').fadeIn(200);
                }
            }
        });
        
        // 绑定保存按钮
        $(document).off('click', '#saveEditUseCase').on('click', '#saveEditUseCase', async function() {
            await self.saveEditUseCase(onSuccess);
        });
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('editUseCaseFromTemplateModal'));
        modal.show();
        
        // 模态框关闭后移除并清理事件
        $('#editUseCaseFromTemplateModal').on('hidden.bs.modal', function() {
            $(document).off('input', '#editUseCaseFromTemplateModal .variable-value');
            $(document).off('click', '#editUseCaseFromTemplateModal .preview-tab');
            $(document).off('click', '#saveEditUseCase');
            $(this).remove();
        });
    }

    /**
     * 显示模板预览（用于编辑用例）
     */
    showTemplatePreviewForEditUseCase(template, existingVariables) {
        // 生成变量输入框（带已有值）
        this.generateVariableInputsForEditUseCase(template, existingVariables);
        
        // 渲染模板预览
        this.renderPreviewForEditUseCase(template);
    }

    /**
     * 生成变量输入框（用于编辑用例）
     */
    generateVariableInputsForEditUseCase(template, existingVariables) {
        const variables = this.extractVariablesFromTemplate(template);
        const container = $('#editUseCaseVariablesContainer');
        
        container.empty();
        
        if (variables.length === 0) {
            container.html('<p class="text-muted">此模板没有定义变量</p>');
            return;
        }
        
        // 为每个变量生成输入框（填充已有值）
        variables.forEach(varName => {
            const value = existingVariables[varName] || '';
            const rowHtml = `
                <div class="variable-row mb-2">
                    <div class="row g-2">
                        <div class="col-md-4">
                            <input type="text" class="form-control variable-key" value="${varName}" readonly>
                        </div>
                        <div class="col-md-8">
                            <input type="text" class="form-control variable-value" placeholder="请输入 ${varName} 的值" data-var="${varName}" value="${value}">
                        </div>
                    </div>
                </div>
            `;
            container.append(rowHtml);
        });
    }

    /**
     * 渲染预览（用于编辑用例）
     */
    renderPreviewForEditUseCase(template) {
        // 收集当前的变量值
        const variables = {};
        $('#editUseCaseVariablesContainer .variable-value').each(function() {
            const key = $(this).data('var');
            const value = $(this).val().trim();
            if (key) {
                variables[key] = value;
            }
        });
        
        // 渲染系统提示词
        const renderedSystemPrompt = this.renderTextForView(template.system_prompt, variables);
        
        // 渲染用户提示词
        const renderedUserPrompt = this.renderTextForView(template.user_prompt, variables);

        const previewHtml = `
            <div class="template-preview-content">
                <!-- 切换标签 -->
                <div class="preview-tabs mb-3">
                    <button type="button" class="preview-tab" data-mode="template">
                        <i class="fas fa-file-code"></i> 模板
                    </button>
                    <button type="button" class="preview-tab active" data-mode="rendered">
                        <i class="fas fa-eye"></i> 预览
                    </button>
                </div>

                <!-- 原始模板 -->
                <div class="preview-section" id="editUseCaseTemplateSection" style="display: none;">
                    <div class="template-text-original">
                        <div class="mb-3">
                            <strong class="text-primary">系统提示词模板：</strong>
                            <div class="template-text-display">${this.formatTemplateDisplay(template.system_prompt)}</div>
                        </div>
                        <div>
                            <strong class="text-primary">用户提示词模板：</strong>
                            <div class="template-text-display">${template.user_prompt || '<em class="text-muted">无</em>'}</div>
                        </div>
                    </div>
                </div>

                <!-- 实时渲染预览 -->
                <div class="preview-section" id="editUseCaseRenderedSection">
                    <div class="rendered-preview">
                        <div class="mb-3">
                            <strong class="text-success">渲染后系统提示词：</strong>
                            <div class="rendered-text" id="editUseCaseRenderedSystemPrompt">${renderedSystemPrompt}</div>
                        </div>
                        <div>
                            <strong class="text-success">渲染后用户提示词：</strong>
                            <div class="rendered-text" id="editUseCaseRenderedUserPrompt">${renderedUserPrompt}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('#editUseCaseTemplatePreview').html(previewHtml);
    }

    /**
     * 保存编辑的用例
     */
    async saveEditUseCase(onSuccess) {
        const useCaseId = $('#editUseCaseId').val();
        const templateId = $('#editUseCaseTemplateId').val();
        const useCaseName = $('#editUseCaseName').val().trim();
        const referenceAnswer = $('#editUseCaseReferenceAnswer').val().trim() || null;
        const remarks = $('#editUseCaseRemarks').val().trim() || null;
        
        // 验证
        if (!useCaseName) {
            UIHelper.showToast('请填写用例名称', 'warning');
            return;
        }

        if (!templateId) {
            UIHelper.showToast('请选择提示词模板', 'warning');
            return;
        }
        
        // 收集变量
        const variables = {};
        let hasVariables = false;
        $('#editUseCaseVariablesContainer .variable-value').each(function() {
            const key = $(this).data('var');
            const value = $(this).val().trim();
            if (key) {
                variables[key] = value;
                hasVariables = true;
            }
        });
        
        const formData = {
            use_case_name: useCaseName,
            template_id: templateId,
            template_variables: hasVariables ? variables : null,
            reference_answer: referenceAnswer,
            remarks: remarks
        };
        
        try {
            $('#saveEditUseCase').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            await ApiService.promptUseCases.update(useCaseId, formData);
            UIHelper.showToast('用例更新成功', 'success');
            
            bootstrap.Modal.getInstance(document.getElementById('editUseCaseFromTemplateModal')).hide();
            
            // 调用成功回调，刷新用例列表
            if (onSuccess) {
                onSuccess();
            }
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveEditUseCase').prop('disabled', false).html('保存');
        }
    }

    /**
     * 删除用例（在查看用例模态框中调用）
     */
    async deleteUseCaseInModal(useCaseId, useCaseName, onSuccess) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除提示词用例 "${useCaseName}" 吗？\n\n此操作无法撤销。`,
            {
                title: '删除提示词用例',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.promptUseCases.delete(useCaseId);
            UIHelper.showToast('用例删除成功', 'success');
            
            // 调用成功回调，刷新用例列表
            if (onSuccess) {
                onSuccess();
            }
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 查看用例详情（在用例列表中调用）
     */
    async viewUseCaseDetail(useCaseId) {
        try {
            const useCase = await ApiService.promptUseCases.getById(useCaseId);
            
            // 获取模板信息（从缓存中）
            const template = await ApiService.promptTemplates.getById(useCase.template_id);
            
            // 构建变量显示
            let variablesHtml = '<p class="text-muted">此模板没有定义变量</p>';
            if (useCase.template_variables && Object.keys(useCase.template_variables).length > 0) {
                variablesHtml = '';
                for (const [key, value] of Object.entries(useCase.template_variables)) {
                    variablesHtml += `
                        <div class="variable-row mb-2">
                            <div class="row g-2">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" value="${key}" readonly>
                                </div>
                                <div class="col-md-8">
                                    <input type="text" class="form-control" value="${value}" readonly>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }
            
            // 渲染模板预览
            const variables = useCase.template_variables || {};
            const renderedSystemPrompt = this.renderTextForView(template.system_prompt, variables);
            const renderedUserPrompt = this.renderTextForView(template.user_prompt, variables);
            
            // 构建详情HTML
            const detailHtml = `
                <div class="row">
                    <!-- 左侧：信息展示 -->
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">用例名称</label>
                            <input type="text" class="form-control" value="${useCase.use_case_name}" readonly>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">关联模板</label>
                            <input type="text" class="form-control" value="${template.template_name}" readonly>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">模板变量</label>
                            <div>
                                ${variablesHtml}
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">参考答案</label>
                            <textarea class="form-control" rows="6" readonly>${useCase.reference_answer || ''}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">备注</label>
                            <textarea class="form-control" rows="3" readonly>${useCase.remarks || ''}</textarea>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">创建时间</label>
                            <input type="text" class="form-control" value="${UIHelper.formatDateTime(useCase.created_at)}" readonly>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">更新时间</label>
                            <input type="text" class="form-control" value="${UIHelper.formatDateTime(useCase.updated_at)}" readonly>
                        </div>
                    </div>

                    <!-- 右侧：模板预览 -->
                    <div class="col-md-6">
                        <div class="template-preview-panel">
                            <h6 class="mb-3">模板预览</h6>
                            <div class="template-preview-content">
                                <!-- 切换标签 -->
                                <div class="preview-tabs mb-3">
                                    <button type="button" class="preview-tab" data-mode="template">
                                        <i class="fas fa-file-code"></i> 模板
                                    </button>
                                    <button type="button" class="preview-tab active" data-mode="rendered">
                                        <i class="fas fa-eye"></i> 预览
                                    </button>
                                </div>

                                <!-- 原始模板 -->
                                <div class="preview-section" id="detailTemplateSection" style="display: none;">
                                    <div class="template-text-original">
                                        <div class="mb-3">
                                            <strong class="text-primary">系统提示词模板：</strong>
                                            <div class="template-text-display">${this.formatTemplateDisplay(template.system_prompt)}</div>
                                        </div>
                                        <div>
                                            <strong class="text-primary">用户提示词模板：</strong>
                                            <div class="template-text-display">${template.user_prompt || '<em class="text-muted">无</em>'}</div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 实时渲染预览 -->
                                <div class="preview-section" id="detailRenderedSection">
                                    <div class="rendered-preview">
                                        <div class="mb-3">
                                            <strong class="text-success">渲染后系统提示词：</strong>
                                            <div class="rendered-text">${renderedSystemPrompt}</div>
                                        </div>
                                        <div>
                                            <strong class="text-success">渲染后用户提示词：</strong>
                                            <div class="rendered-text">${renderedUserPrompt}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 创建用例详情模态框
            const useCaseModalHtml = `
                <div class="modal fade" id="useCaseDetailModal2" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">提示词用例详情</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                ${detailHtml}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除旧的模态框（如果存在）
            $('#useCaseDetailModal2').remove();
            
            // 添加新的模态框
            $('body').append(useCaseModalHtml);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('useCaseDetailModal2'));
            modal.show();
            
            // 绑定预览切换事件
            $('#useCaseDetailModal2').on('click', '.preview-tab', function() {
                if (!$(this).hasClass('active')) {
                    $('#useCaseDetailModal2 .preview-tab').removeClass('active');
                    $(this).addClass('active');
                    const mode = $(this).data('mode');
                    if (mode === 'template') {
                        $('#detailTemplateSection').fadeIn(200);
                        $('#detailRenderedSection').fadeOut(200);
                    } else {
                        $('#detailTemplateSection').fadeOut(200);
                        $('#detailRenderedSection').fadeIn(200);
                    }
                }
            });
            
            // 模态框关闭后移除
            $('#useCaseDetailModal2').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            UIHelper.showToast('加载用例详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 格式化模板显示（用于显示原始模板内容）
     */
    formatTemplateDisplay(text) {
        if (text === '__NONE__') {
            return '<em class="text-muted">无</em>';
        }
        
        if (text === '__USE_SYSTEM_DEFAULT__') {
            const defaultValue = this.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '';
            if (!defaultValue) {
                return '<span class="badge bg-primary">系统默认</span> <em class="text-muted">（未配置）</em>';
            }
            return `<span class="badge bg-primary">系统默认</span><br/>${defaultValue}`;
        }
        
        if (!text) {
            return '<em class="text-muted">无</em>';
        }
        
        return text;
    }
    
    /**
     * 渲染文本用于查看（与PromptUseCaseManagement中的renderText方法相同）
     * 处理 __USE_SYSTEM_DEFAULT__ 和 __NONE__ 特殊值
     */
    renderTextForView(text, variables) {
        // 处理特殊值
        if (text === '__NONE__') {
            return '<em class="text-muted">无</em>';
        }
        
        if (text === '__USE_SYSTEM_DEFAULT__') {
            // 替换为系统默认值
            text = this.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '';
            if (!text) {
                return '<em class="text-muted">系统默认（未配置）</em>';
            }
        }
        
        if (!text) {
            return '<em class="text-muted">无</em>';
        }

        let rendered = text;

        // 替换所有变量
        for (const [key, value] of Object.entries(variables)) {
            const regex = new RegExp(`<\\$${key}>`, 'g');
            if (value && value.trim()) {
                // 如果有值，替换并添加高亮标记
                rendered = rendered.replace(regex, `<span class="variable-highlight" data-var="${key}">${value}</span>`);
            } else {
                // 如果没有值，保持原样但添加待填写标记
                rendered = rendered.replace(regex, `<span class="variable-placeholder" data-var="${key}"><$${key}></span>`);
            }
        }

        return rendered;
    }

    /**
     * 查看模板详情
     */
    async viewTemplate(id) {
        try {
            const template = await ApiService.promptTemplates.getById(id);
            
            const detailHtml = `
                <div class="template-detail">
                    <div class="mb-3">
                        <strong>模板名称：</strong>${template.template_name}
                    </div>
                    <div class="mb-3">
                        <strong>功能分类：</strong>${template.function_category || '<em class="text-muted">未分类</em>'}
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <div class="mb-2">
                                <strong>负责人：</strong>${template.owner || '<em class="text-muted">未设置</em>'}
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-2">
                                <strong>QC号：</strong>${template.qc_number || '<em class="text-muted">未设置</em>'}
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-2">
                                <strong>提示词来源：</strong>${template.prompt_source || '<em class="text-muted">未设置</em>'}
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <strong>系统提示词：</strong>
                        <div class="prompt-content">${this.formatFieldDisplay(template.system_prompt, 'systemPrompt')}</div>
                    </div>
                    <div class="mb-3">
                        <strong>用户提示词：</strong>
                        <div class="prompt-content">${template.user_prompt || '<em class="text-muted">无</em>'}</div>
                    </div>
                    <div class="mb-3">
                        <strong>备注：</strong>
                        <div class="prompt-content">${template.remarks || '<em class="text-muted">无</em>'}</div>
                    </div>
                    
                    <!-- 模型入参配置 -->
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="mb-0"><i class="fas fa-cogs"></i> 模型入参配置</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-2">
                                        <strong>最大Token数：</strong>${this.formatFieldDisplay(template.max_tokens, 'maxTokens')}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-2">
                                        <strong>温度参数：</strong>${this.formatFieldDisplay(template.temperature, 'temperature')}
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-2">
                                        <strong>Top P参数：</strong>${this.formatFieldDisplay(template.top_p, 'topP')}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-2">
                                        <strong>Top K参数：</strong>${this.formatFieldDisplay(template.top_k, 'topK')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 评估策略 -->
                    <div class="card mb-3">
                        
                        <div class="card-body">
                            <div class="mb-3">
                                <div class="mt-2">${this.formatEvaluationStrategies(template.evaluation_strategies)}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <strong>创建时间：</strong>${UIHelper.formatDateTime(template.created_at)}
                    </div>
                    <div class="mb-3">
                        <strong>更新时间：</strong>${UIHelper.formatDateTime(template.updated_at)}
                    </div>
                </div>
            `;
            
            // 创建临时模态框显示详情
            const modalHtml = `
                <div class="modal fade" id="templateDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">提示词模板详情</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                ${detailHtml}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除旧的详情模态框（如果存在）
            $('#templateDetailModal').remove();
            
            // 添加新的模态框
            $('body').append(modalHtml);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('templateDetailModal'));
            modal.show();
            
            // 模态框关闭后移除
            $('#templateDetailModal').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            UIHelper.showToast('加载模板详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 显示模态框（创建或编辑）
     */
    async showModal(id = null) {
        if (id) {
            // 编辑模式
            $('#promptTemplateModalLabel').text('编辑提示词模板');
            
            try {
                const template = await ApiService.promptTemplates.getById(id);
                
                $('#templateRowId').val(template.id);
                $('#templateName').val(template.template_name);
                $('#userPrompt').val(template.user_prompt || '');
                $('#functionCategory').val(template.function_category || '');
                $('#remarks').val(template.remarks || '');
                $('#owner').val(template.owner || '');
                $('#qcNumber').val(template.qc_number || '');
                $('#promptSource').val(template.prompt_source || '');
                
                // 设置系统提示词模式
                this.setFieldMode('systemPrompt', template.system_prompt);
                
                // 设置模型参数模式
                this.setFieldMode('maxTokens', template.max_tokens);
                this.setFieldMode('temperature', template.temperature);
                this.setFieldMode('topP', template.top_p);
                this.setFieldMode('topK', template.top_k);
                
                // 设置评估策略
                this.setEvaluationStrategies(template.evaluation_strategies);
            } catch (error) {
                UIHelper.showToast('加载模板数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#promptTemplateModalLabel').text('添加提示词模板');
            $('#promptTemplateForm')[0].reset();
            $('#templateRowId').val('');
            
            // 初始化为系统默认配置
            this.resetFieldMode('systemPrompt');
            this.resetFieldMode('maxTokens');
            this.resetFieldMode('temperature');
            this.resetFieldMode('topP');
            this.resetFieldMode('topK');
            
            // 清空评估策略
            this.setEvaluationStrategies(null);
        }
        
        const modal = new bootstrap.Modal(document.getElementById('promptTemplateModal'));
        modal.show();
    }
    
    /**
     * 设置字段模式（编辑时使用）
     */
    setFieldMode(fieldName, value) {
        const modeName = fieldName + 'Mode';
        const placeholders = {
            'systemPrompt': { custom: '输入系统提示词...', default: '使用系统默认配置', none: '' },
            'maxTokens': { custom: '输入最大Token数', default: '使用系统默认', none: '' },
            'temperature': { custom: '输入温度参数 (0-2)', default: '使用系统默认', none: '' },
            'topP': { custom: '输入Top-P参数 (0-1)', default: '使用系统默认', none: '' },
            'topK': { custom: '输入Top-K参数', default: '使用系统默认', none: '' }
        };
        
        if (value === '__USE_SYSTEM_DEFAULT__') {
            // 系统默认配置
            $(`#${modeName}`).val('default').data('previous-mode', 'default');
            const defaultValue = this.getSystemDefaultValue(fieldName);
            const placeholder = placeholders[fieldName]?.default || '使用系统默认';
            $(`#${fieldName}`).prop('disabled', true).val(defaultValue).attr('placeholder', placeholder);
        } else if (value === '__NONE__') {
            // 空
            $(`#${modeName}`).val('none').data('previous-mode', 'none');
            $(`#${fieldName}`).prop('disabled', true).val('').attr('placeholder', '');
        } else if (value === null || value === undefined || value === '') {
            // null 或未设置，设置为系统默认
            $(`#${modeName}`).val('default').data('previous-mode', 'default');
            const defaultValue = this.getSystemDefaultValue(fieldName);
            const placeholder = placeholders[fieldName]?.default || '使用系统默认';
            $(`#${fieldName}`).prop('disabled', true).val(defaultValue).attr('placeholder', placeholder);
        } else {
            // 自定义 - 将数值类型转换为字符串
            $(`#${modeName}`).val('custom').data('previous-mode', 'custom');
            const displayValue = this.convertToString(value);
            const placeholder = placeholders[fieldName]?.custom || '';
            $(`#${fieldName}`).prop('disabled', false).val(displayValue).attr('placeholder', placeholder);
        }
    }
    
    /**
     * 将值转换为字符串（用于显示）
     */
    convertToString(value) {
        if (typeof value === 'number') {
            return value.toString();
        }
        return value;
    }
    
    /**
     * 重置字段模式为系统默认（新建时使用）
     */
    resetFieldMode(fieldName) {
        const modeName = fieldName + 'Mode';
        const placeholders = {
            'systemPrompt': '使用系统默认配置',
            'maxTokens': '使用系统默认',
            'temperature': '使用系统默认',
            'topP': '使用系统默认',
            'topK': '使用系统默认'
        };
        
        $(`#${modeName}`).val('default').data('previous-mode', 'default');
        const defaultValue = this.getSystemDefaultValue(fieldName);
        const placeholder = placeholders[fieldName] || '使用系统默认';
        $(`#${fieldName}`).prop('disabled', true).val(defaultValue).attr('placeholder', placeholder);
    }
    
    /**
     * 获取系统默认值
     */
    getSystemDefaultValue(fieldName) {
        const configMap = {
            'systemPrompt': 'DEFAULT_SYSTEM_PROMPT',
            'maxTokens': 'DEFAULT_MAX_TOKENS',
            'temperature': 'DEFAULT_TEMPERATURE',
            'topP': 'DEFAULT_TOP_P',
            'topK': 'DEFAULT_TOP_K'
        };
        
        const configCode = configMap[fieldName];
        return configCode ? (this.systemDefaults[configCode] || '') : '';
    }
    
    /**
     * 根据模式获取字段值
     */
    getFieldValue(fieldName) {
        const modeName = fieldName + 'Mode';
        const mode = $(`#${modeName}`).val();
        
        if (mode === 'default') {
            // 系统默认配置
            return '__USE_SYSTEM_DEFAULT__';
        } else if (mode === 'none') {
            // 空
            return '__NONE__';
        } else {
            // 自定义
            const value = $(`#${fieldName}`).val().trim();
            if (!value) {
                return null;
            }
            
            // 根据字段类型转换
            if (fieldName === 'systemPrompt') {
                return value;
            } else if (fieldName === 'maxTokens' || fieldName === 'topK') {
                // 数值类型转换为字符串
                return String(parseInt(value));
            } else if (fieldName === 'temperature' || fieldName === 'topP') {
                // 数值类型转换为字符串
                return String(parseFloat(value));
            }
            return value;
        }
    }
    
    /**
     * 格式化字段显示值（用于详情查看）
     */
    formatFieldDisplay(value, fieldName) {
        if (value === '__USE_SYSTEM_DEFAULT__') {
            const defaultValue = this.getSystemDefaultValue(fieldName);
            return `<span class="badge bg-primary">系统默认</span> ${defaultValue ? `<span class="text-muted ms-2">(${defaultValue})</span>` : ''}`;
        } else if (value === '__NONE__') {
            return '<span class="badge bg-secondary">空</span>';
        } else if (value === null || value === undefined || value === '') {
            return '<em class="text-muted">未设置</em>';
        } else {
            // 将数值类型转换为字符串显示
            return this.convertToString(value);
        }
    }

    /**
     * 格式化评估策略显示
     */
    formatEvaluationStrategies(strategies) {
        if (!strategies || !Array.isArray(strategies) || strategies.length === 0) {
            return '<em class="text-muted">未配置</em>';
        }
        
        const strategyLabels = {
            'exact_match': '精确匹配',
            'json_key_match': 'JSON 键匹配',
            'answer_accuracy': '答案准确率',
            'factual_correctness': '事实正确性',
            'semantic_similarity': '语义相似性',
            'bleu': 'BLEU',
            'rouge': 'ROUGE',
            'chrf': 'CHRF'
        };
        
        const badges = strategies.map(strategy => {
            const label = strategyLabels[strategy] || strategy;
            return `<span class="badge bg-info me-1">${label}</span>`;
        }).join('');
        
        return badges;
    }

    /**
     * 设置评估策略（用于编辑时回显）
     */
    setEvaluationStrategies(strategies) {
        // 先清空所有选择
        $('#evaluationStrategiesContainer input[type="checkbox"]').prop('checked', false);
        
        // 如果有策略，则勾选对应的复选框
        if (strategies && Array.isArray(strategies)) {
            strategies.forEach(strategy => {
                $(`#strategy_${strategy}`).prop('checked', true);
            });
        }
    }
    
    /**
     * 获取选中的评估策略
     */
    getEvaluationStrategies() {
        const strategies = [];
        $('#evaluationStrategiesContainer input[type="checkbox"]:checked').each(function() {
            strategies.push($(this).val());
        });
        return strategies.length > 0 ? strategies : null;
    }

    /**
     * 保存模板
     */
    async saveTemplate() {
        const id = $('#templateRowId').val();
        
        // 根据模式获取字段值
        const systemPromptValue = this.getFieldValue('systemPrompt');
        const maxTokensValue = this.getFieldValue('maxTokens');
        const temperatureValue = this.getFieldValue('temperature');
        const topPValue = this.getFieldValue('topP');
        const topKValue = this.getFieldValue('topK');
        
        const formData = {
            template_name: $('#templateName').val().trim(),
            system_prompt: systemPromptValue,
            user_prompt: $('#userPrompt').val().trim() || null,
            function_category: $('#functionCategory').val().trim() || null,
            remarks: $('#remarks').val().trim() || null,
            owner: $('#owner').val().trim() || null,
            qc_number: $('#qcNumber').val().trim() || null,
            prompt_source: $('#promptSource').val().trim() || null,
            max_tokens: maxTokensValue,
            top_p: topPValue,
            top_k: topKValue,
            temperature: temperatureValue,
            evaluation_strategies: this.getEvaluationStrategies()
        };
        
        // 验证
        if (!formData.template_name) {
            UIHelper.showToast('请填写模板名称', 'warning');
            return;
        }
        
        // 验证模型参数的范围（仅在自定义模式下）
        if (formData.max_tokens && formData.max_tokens !== '__USE_SYSTEM_DEFAULT__' && formData.max_tokens !== '__NONE__') {
            const maxTokens = parseFloat(formData.max_tokens);
            if (maxTokens < 1) {
                UIHelper.showToast('最大Token数必须大于0', 'warning');
                return;
            }
        }
        if (formData.top_p && formData.top_p !== '__USE_SYSTEM_DEFAULT__' && formData.top_p !== '__NONE__') {
            const topP = parseFloat(formData.top_p);
            if (topP < 0 || topP > 1) {
                UIHelper.showToast('Top P参数必须在0-1之间', 'warning');
                return;
            }
        }
        if (formData.top_k && formData.top_k !== '__USE_SYSTEM_DEFAULT__' && formData.top_k !== '__NONE__') {
            const topK = parseFloat(formData.top_k);
            if (topK < 0) {
                UIHelper.showToast('Top K参数必须大于等于0', 'warning');
                return;
            }
        }
        if (formData.temperature && formData.temperature !== '__USE_SYSTEM_DEFAULT__' && formData.temperature !== '__NONE__') {
            const temperature = parseFloat(formData.temperature);
            if (temperature < 0 || temperature > 2) {
                UIHelper.showToast('温度参数必须在0-2之间', 'warning');
                return;
            }
        }
        
        try {
            $('#savePromptTemplate').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                // 更新
                await ApiService.promptTemplates.update(id, formData);
                UIHelper.showToast('模板更新成功', 'success');
            } else {
                // 创建
                await ApiService.promptTemplates.create(formData);
                UIHelper.showToast('模板创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('promptTemplateModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#savePromptTemplate').prop('disabled', false).html('保存');
        }
    }

    /**
     * 删除模板
     */
    async deleteTemplate(id, name) {
        try {
            // 先查询该模板关联的用例数量
            const useCasesResponse = await ApiService.promptUseCases.getAll({
                template_id: id,
                limit: 1  // 只需要知道总数，不需要获取所有数据
            });
            
            const useCaseCount = useCasesResponse.total;
            
            // 根据是否有关联用例显示不同的确认消息
            let confirmMessage = `确定要删除提示词模板 "${name}" 吗？\n\n此操作无法撤销。`;
            let confirmOptions = {
                title: '删除提示词模板',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            };
            
            if (useCaseCount > 0) {
                confirmMessage = `确定要删除提示词模板 "${name}" 吗？\n\n⚠️ 警告：该模板关联了 ${useCaseCount} 个用例，删除模板后这些用例也将被一并删除！\n\n此操作无法撤销。`;
            }
            
            const confirmed = await UIHelper.confirmDialog(confirmMessage, confirmOptions);
            
            if (!confirmed) {
                return;
            }
            
            await ApiService.promptTemplates.delete(id);
            UIHelper.showToast('模板删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 检查所有变量是否已填写（新建用例）
     */
    checkNewUseCaseAllVariablesFilled() {
        const variableInputs = $('#newUseCaseVariablesContainer .variable-value');
        
        if (variableInputs.length === 0) {
            return true;
        }
        
        let allFilled = true;
        variableInputs.each(function() {
            if (!$(this).val().trim()) {
                allFilled = false;
                return false;
            }
        });
        return allFilled;
    }

    /**
     * 更新生成按钮状态（新建用例）
     */
    updateNewUseCaseGenerateButtonState() {
        const modelId = $('#newUseCaseAiModelSelect').val();
        const allFilled = this.checkNewUseCaseAllVariablesFilled();
        const hasTemplate = $('#newUseCaseTemplateId').val();
        $('#generateNewUseCaseReferenceAnswer').prop('disabled', !modelId || !hasTemplate || !allFilled);
    }

    /**
     * AI生成参考答案（新建用例）
     */
    async generateNewUseCaseReferenceAnswer(template) {
        const modelId = $('#newUseCaseAiModelSelect').val();
        if (!modelId) {
            UIHelper.showToast('请先选择AI模型', 'warning');
            return;
        }
        
        if (!this.checkNewUseCaseAllVariablesFilled()) {
            UIHelper.showToast('请先填写完所有模板变量', 'warning');
            return;
        }
        
        // 收集变量值
        const variables = {};
        $('#newUseCaseVariablesContainer .variable-value').each(function() {
            const key = $(this).data('var');
            const value = $(this).val().trim();
            if (key) {
                variables[key] = value;
            }
        });
        
        await this.callAIModelToGenerateAnswer(modelId, template, variables, '#newUseCaseReferenceAnswer', '#generateNewUseCaseReferenceAnswer', () => {
            this.updateNewUseCaseGenerateButtonState();
        });
    }

    /**
     * 检查所有变量是否已填写（编辑用例）
     */
    checkEditUseCaseAllVariablesFilled() {
        const variableInputs = $('#editUseCaseVariablesContainer .variable-value');
        
        if (variableInputs.length === 0) {
            return true;
        }
        
        let allFilled = true;
        variableInputs.each(function() {
            if (!$(this).val().trim()) {
                allFilled = false;
                return false;
            }
        });
        return allFilled;
    }

    /**
     * 更新生成按钮状态（编辑用例）
     */
    updateEditUseCaseGenerateButtonState() {
        const modelId = $('#editUseCaseAiModelSelect').val();
        const allFilled = this.checkEditUseCaseAllVariablesFilled();
        const hasTemplate = $('#editUseCaseTemplateId').val();
        $('#generateEditUseCaseReferenceAnswer').prop('disabled', !modelId || !hasTemplate || !allFilled);
    }

    /**
     * AI生成参考答案（编辑用例）
     */
    async generateEditUseCaseReferenceAnswer(template) {
        const modelId = $('#editUseCaseAiModelSelect').val();
        if (!modelId) {
            UIHelper.showToast('请先选择AI模型', 'warning');
            return;
        }
        
        if (!this.checkEditUseCaseAllVariablesFilled()) {
            UIHelper.showToast('请先填写完所有模板变量', 'warning');
            return;
        }
        
        // 收集变量值
        const variables = {};
        $('#editUseCaseVariablesContainer .variable-value').each(function() {
            const key = $(this).data('var');
            const value = $(this).val().trim();
            if (key) {
                variables[key] = value;
            }
        });
        
        await this.callAIModelToGenerateAnswer(modelId, template, variables, '#editUseCaseReferenceAnswer', '#generateEditUseCaseReferenceAnswer', () => {
            this.updateEditUseCaseGenerateButtonState();
        });
    }

    /**
     * 渲染提示词用于API调用（处理特殊值）
     */
    renderPromptForAPI(prompt, variables) {
        if (!prompt) return '';
        if (prompt === '__NONE__') return '';
        if (prompt === '__USE_SYSTEM_DEFAULT__') {
            prompt = this.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '';
        }
        
        // 替换变量
        let rendered = prompt;
        for (const [key, value] of Object.entries(variables)) {
            const regex = new RegExp(`<\\$${key}>`, 'g');
            rendered = rendered.replace(regex, value);
        }
        
        return rendered;
    }

    /**
     * 构建模型参数
     */
    buildModelParams(template) {
        const params = {};
        
        // max_tokens
        if (template.max_tokens && template.max_tokens !== '__NONE__') {
            if (template.max_tokens === '__USE_SYSTEM_DEFAULT__') {
                const defaultValue = this.systemDefaults['DEFAULT_MAX_TOKENS'];
                if (defaultValue) params.max_tokens = parseInt(defaultValue);
            } else {
                params.max_tokens = parseInt(template.max_tokens);
            }
        }
        
        // temperature
        if (template.temperature && template.temperature !== '__NONE__') {
            if (template.temperature === '__USE_SYSTEM_DEFAULT__') {
                const defaultValue = this.systemDefaults['DEFAULT_TEMPERATURE'];
                if (defaultValue) params.temperature = parseFloat(defaultValue);
            } else {
                params.temperature = parseFloat(template.temperature);
            }
        }
        
        // top_p
        if (template.top_p && template.top_p !== '__NONE__') {
            if (template.top_p === '__USE_SYSTEM_DEFAULT__') {
                const defaultValue = this.systemDefaults['DEFAULT_TOP_P'];
                if (defaultValue) params.top_p = parseFloat(defaultValue);
            } else {
                params.top_p = parseFloat(template.top_p);
            }
        }
        
        // top_k
        if (template.top_k && template.top_k !== '__NONE__') {
            if (template.top_k === '__USE_SYSTEM_DEFAULT__') {
                const defaultValue = this.systemDefaults['DEFAULT_TOP_K'];
                if (defaultValue) params.top_k = parseInt(defaultValue);
            } else {
                params.top_k = parseInt(template.top_k);
            }
        }
        
        return params;
    }

    /**
     * 调用AI模型生成答案（通用方法）
     */
    async callAIModelToGenerateAnswer(modelId, template, variables, answerFieldSelector, buttonSelector, restoreCallback) {
        try {
            // 显示生成中状态
            $(buttonSelector)
                .prop('disabled', true)
                .html('<i class="fas fa-spinner fa-spin"></i> 生成中...');
            
            // 获取AI模型信息
            const aiModel = this.aiModels.find(m => m.id === modelId);
            if (!aiModel) {
                throw new Error('AI模型未找到');
            }
            
            // 渲染提示词
            const systemPrompt = this.renderPromptForAPI(template.system_prompt, variables);
            const userPrompt = this.renderPromptForAPI(template.user_prompt, variables);
            
            // 构建请求参数
            const requestData = {
                messages: []
            };
            
            // 添加系统提示词
            if (systemPrompt && systemPrompt !== '__NONE__' && systemPrompt.trim()) {
                requestData.messages.push({
                    role: 'system',
                    content: systemPrompt
                });
            }
            
            // 添加用户提示词
            if (userPrompt && userPrompt.trim()) {
                requestData.messages.push({
                    role: 'user',
                    content: userPrompt
                });
            }
            
            // 如果没有任何提示词，给一个默认的用户提示
            if (requestData.messages.length === 0) {
                requestData.messages.push({
                    role: 'user',
                    content: '请生成一个参考答案'
                });
            }
            
            // 添加模型参数
            const params = this.buildModelParams(template);
            if (params.max_tokens) requestData.max_tokens = params.max_tokens;
            if (params.temperature !== undefined) requestData.temperature = params.temperature;
            if (params.top_p) requestData.top_p = params.top_p;
            if (params.top_k) requestData.top_k = params.top_k;
            
            // 通过后端API中转调用AI模型
            const result = await ApiService.aiModels.chatCompletion(modelId, requestData);
            
            // 提取生成的答案
            const generatedAnswer = result.content || '';
            
            // 回填到参考答案输入框
            $(answerFieldSelector).val(generatedAnswer);
            UIHelper.showToast('参考答案生成成功', 'success');
            
        } catch (error) {
            UIHelper.showToast('生成失败: ' + error.message, 'error');
            console.error('AI生成参考答案失败:', error);
        } finally {
            // 恢复按钮状态
            if (restoreCallback) {
                restoreCallback();
            }
            $(buttonSelector).html('<i class="fas fa-magic me-1"></i>模型生成');
        }
    }

    /**
     * 销毁组件（清理事件监听）
     */
    destroy() {
        $(document).off('click', '#addPromptTemplate');
        $(document).off('click', '#applyTemplateFilters');
        $(document).off('click', '#resetTemplateFilters');
        $(document).off('keypress', '#searchKeyword');
        $(document).off('click', '.edit-template');
        $(document).off('click', '.delete-template');
        $(document).off('click', '.view-template');
        $(document).off('click', '.view-use-cases');
        $(document).off('click', '.create-use-case');
        $(document).off('click', '#savePromptTemplate');
        $(document).off('click', '#promptTemplatesTableContent .page-link[data-page]');
        $(document).off('change', '#systemPromptMode');
        $(document).off('change', '#maxTokensMode');
        $(document).off('change', '#temperatureMode');
        $(document).off('change', '#topPMode');
        $(document).off('change', '#topKMode');
    }
}
