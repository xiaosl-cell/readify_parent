/**
 * 提示词用例管理组件
 * 负责提示词用例的增删改查操作
 */

class PromptUseCaseManagement {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalItems = 0;
        this.currentFilters = {};
        this.templates = []; // 缓存模板列表
        this.currentEditingVariables = {}; // 编辑时的变量值缓存
        this.currentTemplate = null; // 当前选中的模板
        this.systemDefaults = {}; // 存储系统默认配置
        this.aiModels = []; // 缓存AI模型列表
    }

    /**
     * 初始化组件
     */
    async init() {
        await this.render();
        await this.loadSystemDefaults(); // 加载系统默认配置
        await this.loadTemplates(); // 加载模板列表用于下拉选择
        await this.loadAIModels(); // 加载AI模型列表
        this.populateTemplateFilter(); // 填充筛选下拉框
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
     * 填充模板筛选下拉框
     */
    populateTemplateFilter() {
        let options = '<option value="">全部模板</option>';
        this.templates.forEach(template => {
            options += `<option value="${template.id}">${template.template_name}</option>`;
        });
        $('#filterTemplateId').html(options);
    }

    /**
     * 渲染页面结构
     */
    async render() {
        await TemplateLoader.loadInto('prompt-use-cases.html', 'content-area');
    }

    /**
     * 加载模板列表
     */
    async loadTemplates() {
        try {
            const response = await ApiService.promptTemplates.getAll({ limit: 1000 });
            this.templates = response.items;
        } catch (error) {
            console.error('加载模板列表失败:', error);
            this.templates = [];
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
    populateAIModelSelect() {
        let options = '<option value="">选择AI模型</option>';
        this.aiModels.forEach(model => {
            options += `<option value="${model.id}">${model.model_name}</option>`;
        });
        $('#aiModelSelect').html(options);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 添加用例按钮
        $(document).off('click', '#addPromptUseCase').on('click', '#addPromptUseCase', function() {
            self.showModal();
        });
        
        // 应用过滤
        $(document).off('click', '#applyUseCaseFilters').on('click', '#applyUseCaseFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetUseCaseFilters').on('click', '#resetUseCaseFilters', function() {
            $('#searchUseCaseKeyword').val('');
            $('#filterTemplateId').val('');
            self.currentFilters = {};
            self.loadData();
        });
        
        // 搜索框回车
        $(document).off('keypress', '#searchUseCaseKeyword').on('keypress', '#searchUseCaseKeyword', function(e) {
            if (e.which === 13) {
                self.applyFilters();
            }
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-use-case').on('click', '.edit-use-case', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-use-case').on('click', '.delete-use-case', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            self.deleteUseCase(id, name);
        });
        
        // 查看详情按钮
        $(document).off('click', '.view-use-case').on('click', '.view-use-case', function() {
            const id = $(this).data('id');
            self.viewUseCase(id);
        });
        
        // 保存用例
        $(document).off('click', '#savePromptUseCase').on('click', '#savePromptUseCase', function() {
            self.saveUseCase();
        });
        
        // AI模型选择变化 - 启用/禁用生成按钮
        $(document).off('change', '#aiModelSelect').on('change', '#aiModelSelect', function() {
            self.updateGenerateButtonState();
        });
        
        // 变量输入变化 - 检查是否可以生成
        $(document).off('input', '.variable-value').on('input', '.variable-value', function() {
            self.updateGenerateButtonState();
        });
        
        // AI生成参考答案
        $(document).off('click', '#generateReferenceAnswer').on('click', '#generateReferenceAnswer', function() {
            self.generateReferenceAnswer();
        });
        
        // 分页按钮（仅限主列表的分页）
        $(document).off('click', '#promptUseCasesTableContent .page-link[data-page]').on('click', '#promptUseCasesTableContent .page-link[data-page]', function(e) {
            e.preventDefault();
            const page = $(this).data('page');
            self.currentPage = page;
            self.loadData();
        });

        // 模板选择变化 - 显示模板预览并生成变量输入框
        $(document).off('change', '#useCaseTemplateId').on('change', '#useCaseTemplateId', function() {
            const templateId = $(this).val();
            self.showTemplatePreview(templateId);
        });

        // 变量值输入变化 - 实时渲染预览
        $(document).off('input', '.variable-value').on('input', '.variable-value', function() {
            self.renderPreviewWithVariables();
        });

        // 预览切换按钮
        $(document).off('click', '.preview-tab').on('click', '.preview-tab', function() {
            if (!$(this).hasClass('active')) {
                $('.preview-tab').removeClass('active');
                $(this).addClass('active');
                const mode = $(this).data('mode');
                self.switchPreviewMode(mode);
            }
        });
    }

    /**
     * 应用过滤条件
     */
    applyFilters() {
        this.currentFilters = {};
        
        const keyword = $('#searchUseCaseKeyword').val().trim();
        if (keyword) {
            this.currentFilters.keyword = keyword;
        }

        const templateId = $('#filterTemplateId').val();
        if (templateId) {
            this.currentFilters.template_id = templateId;
        }
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#promptUseCasesTableContent').html(`
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
            
            const response = await ApiService.promptUseCases.getAll(params);
            
            this.totalItems = response.total;
            this.renderTable(response.items);
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#promptUseCasesTableContent').html(`
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
            $('#promptUseCasesTableContent').html(`
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
                        <th style="width: 18%">用例名称</th>
                        <th style="width: 15%">关联模板</th>
                        <th style="width: 25%">渲染后系统提示词</th>
                        <th style="width: 25%">渲染后用户提示词</th>
                        <th style="width: 10%">更新时间</th>
                        <th style="width: 7%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            const template = this.templates.find(t => t.id === item.template_id);
            const templateName = template ? template.template_name : item.template_id;
            
            // 处理渲染后的系统提示词显示
            let systemPromptDisplay = item.rendered_system_prompt;
            let systemPromptTitle = item.rendered_system_prompt || '';
            
            if (item.rendered_system_prompt === '__NONE__' || !item.rendered_system_prompt) {
                systemPromptDisplay = '<em class="text-muted">无</em>';
                systemPromptTitle = '';
            } else if (item.rendered_system_prompt === '__USE_SYSTEM_DEFAULT__') {
                const defaultValue = this.systemDefaults['DEFAULT_SYSTEM_PROMPT'] || '';
                systemPromptDisplay = defaultValue ? 
                    `<span class="badge bg-primary">系统默认</span> ${this.truncateText(defaultValue, 60)}` : 
                    '<span class="badge bg-primary">系统默认</span> <em class="text-muted">（未配置）</em>';
                systemPromptTitle = defaultValue;
            }
            
            const renderedSystemPrompt = this.truncateText(systemPromptDisplay, 80);
            const renderedUserPrompt = this.truncateText(item.rendered_user_prompt || '<em class="text-muted">无</em>', 80);
            
            tableHtml += `
                <tr>
                    <td><strong>${item.use_case_name}</strong></td>
                    <td><span class="badge bg-primary">${templateName}</span></td>
                    <td><div class="text-truncate-cell" title="${this.escapeHtml(systemPromptTitle)}">${renderedSystemPrompt}</div></td>
                    <td><div class="text-truncate-cell" title="${this.escapeHtml(item.rendered_user_prompt || '')}">${renderedUserPrompt}</div></td>
                    <td>${UIHelper.formatDateTime(item.updated_at)}</td>
                    <td class="action-buttons">
                        <button class="btn btn-sm btn-outline-info view-use-case" data-id="${item.id}" title="查看详情">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary edit-use-case" data-id="${item.id}" title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-use-case" data-id="${item.id}" data-name="${item.use_case_name}" title="删除">
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
        
        $('#promptUseCasesTableContent').html(tableHtml);
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
     * 查看用例详情
     */
    async viewUseCase(id) {
        try {
            const useCase = await ApiService.promptUseCases.getById(id);
            const template = this.templates.find(t => t.id === useCase.template_id);
            
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
            
            // 渲染模板预览（使用实际的变量值）
            const variables = useCase.template_variables || {};
            const renderedSystemPrompt = this.renderText(template.system_prompt, variables);
            const renderedUserPrompt = this.renderText(template.user_prompt, variables);
            
            // 构建详情HTML，参照编辑页面的布局
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
                            <input type="text" class="form-control" value="${template ? template.template_name : useCase.template_id}" readonly>
                        </div>

                        <div class="mb-3">
                            <label class="form-label">模板变量</label>
                            <div id="viewVariablesContainer">
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
                                <div class="preview-section" id="viewTemplateSection" style="display: none;">
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
                                <div class="preview-section" id="viewRenderedSection">
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
            
            // 创建临时模态框显示详情
            const modalHtml = `
                <div class="modal fade" id="useCaseDetailModal" tabindex="-1">
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
            
            // 移除旧的详情模态框（如果存在）
            $('#useCaseDetailModal').remove();
            
            // 添加新的模态框
            $('body').append(modalHtml);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('useCaseDetailModal'));
            modal.show();
            
            // 绑定预览切换事件
            $('#useCaseDetailModal').on('click', '.preview-tab', function() {
                if (!$(this).hasClass('active')) {
                    $('#useCaseDetailModal .preview-tab').removeClass('active');
                    $(this).addClass('active');
                    const mode = $(this).data('mode');
                    if (mode === 'template') {
                        $('#viewTemplateSection').fadeIn(200);
                        $('#viewRenderedSection').fadeOut(200);
                    } else {
                        $('#viewTemplateSection').fadeOut(200);
                        $('#viewRenderedSection').fadeIn(200);
                    }
                }
            });
            
            // 模态框关闭后移除
            $('#useCaseDetailModal').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            UIHelper.showToast('加载用例详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 显示模态框（创建或编辑）
     */
    async showModal(id = null) {
        // 填充模板下拉列表
        let templateOptions = '<option value="">请选择提示词模板</option>';
        this.templates.forEach(template => {
            templateOptions += `<option value="${template.id}">${template.template_name}</option>`;
        });
        $('#useCaseTemplateId').html(templateOptions);
        
        // 填充AI模型下拉框
        this.populateAIModelSelect();

        if (id) {
            // 编辑模式
            $('#promptUseCaseModalLabel').text('编辑提示词用例');
            
            try {
                const useCase = await ApiService.promptUseCases.getById(id);
                
                $('#useCaseRowId').val(useCase.id);
                $('#useCaseName').val(useCase.use_case_name);
                $('#useCaseTemplateId').val(useCase.template_id);
                $('#useCaseReferenceAnswer').val(useCase.reference_answer || '');
                $('#useCaseRemarks').val(useCase.remarks || '');
                
                // 显示模板预览并自动生成变量输入框
                // 传递已有的变量值，会在生成时自动填充
                this.currentEditingVariables = useCase.template_variables || {};
                this.showTemplatePreview(useCase.template_id);
                
                // 延迟渲染预览，确保DOM已更新
                setTimeout(() => {
                    this.renderPreviewWithVariables();
                }, 100);
            } catch (error) {
                UIHelper.showToast('加载用例数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#promptUseCaseModalLabel').text('添加提示词用例');
            $('#promptUseCaseForm')[0].reset();
            $('#useCaseRowId').val('');
            $('#variablesContainer').html('<p class="text-muted">请先选择模板</p>');
            $('#templatePreview').html('<p class="text-muted">请选择模板</p>');
            this.currentEditingVariables = {}; // 清空编辑变量缓存
        }
        
        const modal = new bootstrap.Modal(document.getElementById('promptUseCaseModal'));
        modal.show();
    }

    /**
     * 显示模板预览并自动生成变量输入框
     */
    showTemplatePreview(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) {
            $('#templatePreview').html('<p class="text-muted">未找到模板</p>');
            $('#variablesContainer').empty();
            return;
        }

        // 保存当前模板引用
        this.currentTemplate = template;

        // 显示模板预览
        this.renderTemplatePreview();

        // 提取模板中的变量并生成输入框
        this.generateVariableInputs(template);
    }

    /**
     * 渲染模板预览（包含实时渲染和切换按钮）
     */
    renderTemplatePreview() {
        if (!this.currentTemplate) {
            $('#templatePreview').html('<p class="text-muted">未找到模板</p>');
            return;
        }

        // 收集当前的变量值
        const variables = this.collectVariables() || {};
        
        // 渲染系统提示词
        const renderedSystemPrompt = this.renderText(this.currentTemplate.system_prompt, variables);
        
        // 渲染用户提示词
        const renderedUserPrompt = this.renderText(this.currentTemplate.user_prompt, variables);

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
                <div class="preview-section" id="templateSection" style="display: none;">
                    <div class="template-text-original">
                        <div class="mb-3">
                            <strong class="text-primary">系统提示词模板：</strong>
                            <div class="template-text-display">${this.formatTemplateDisplay(this.currentTemplate.system_prompt)}</div>
                        </div>
                        <div>
                            <strong class="text-primary">用户提示词模板：</strong>
                            <div class="template-text-display">${this.currentTemplate.user_prompt || '<em class="text-muted">无</em>'}</div>
                        </div>
                    </div>
                </div>

                <!-- 实时渲染预览 -->
                <div class="preview-section" id="renderedSection">
                    <div class="rendered-preview">
                        <div class="mb-3">
                            <strong class="text-success">渲染后系统提示词：</strong>
                            <div class="rendered-text" id="renderedSystemPrompt">${renderedSystemPrompt}</div>
                        </div>
                        <div>
                            <strong class="text-success">渲染后用户提示词：</strong>
                            <div class="rendered-text" id="renderedUserPrompt">${renderedUserPrompt}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#templatePreview').html(previewHtml);
    }

    /**
     * 切换预览模式
     */
    switchPreviewMode(mode) {
        if (mode === 'template') {
            // 显示模板预览
            $('#templateSection').fadeIn(200);
            $('#renderedSection').fadeOut(200);
        } else {
            // 显示实时渲染
            $('#templateSection').fadeOut(200);
            $('#renderedSection').fadeIn(200);
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
     * 渲染文本，替换变量并添加高亮
     * 处理 __USE_SYSTEM_DEFAULT__ 和 __NONE__ 特殊值
     */
    renderText(text, variables) {
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
        const replacedVars = [];

        // 替换所有变量
        for (const [key, value] of Object.entries(variables)) {
            const regex = new RegExp(`<\\$${key}>`, 'g');
            if (value && value.trim()) {
                // 如果有值，替换并添加高亮标记
                rendered = rendered.replace(regex, `<span class="variable-highlight" data-var="${key}">${value}</span>`);
                replacedVars.push(key);
            } else {
                // 如果没有值，保持原样但添加待填写标记
                rendered = rendered.replace(regex, `<span class="variable-placeholder" data-var="${key}"><$${key}></span>`);
            }
        }

        return rendered;
    }

    /**
     * 实时渲染预览（当变量值改变时调用）
     */
    renderPreviewWithVariables() {
        if (!this.currentTemplate) {
            return;
        }

        // 收集当前的变量值
        const variables = this.collectVariables() || {};
        
        // 渲染系统提示词
        const renderedSystemPrompt = this.renderText(this.currentTemplate.system_prompt, variables);
        
        // 渲染用户提示词
        const renderedUserPrompt = this.renderText(this.currentTemplate.user_prompt, variables);

        // 更新预览区域（带动画效果）
        const systemPromptEl = $('#renderedSystemPrompt');
        const userPromptEl = $('#renderedUserPrompt');

        if (systemPromptEl.length > 0) {
            systemPromptEl.fadeOut(150, function() {
                $(this).html(renderedSystemPrompt).fadeIn(150);
            });
        }

        if (userPromptEl.length > 0) {
            userPromptEl.fadeOut(150, function() {
                $(this).html(renderedUserPrompt).fadeIn(150);
            });
        }
    }

    /**
     * 从模板中提取变量
     */
    extractVariables(template) {
        const variables = new Set();
        const regex = /<\$([a-zA-Z0-9_]+)>/g;
        
        // 从系统提示词中提取
        if (template.system_prompt) {
            let match;
            while ((match = regex.exec(template.system_prompt)) !== null) {
                variables.add(match[1]);
            }
        }
        
        // 从用户提示词中提取
        if (template.user_prompt) {
            regex.lastIndex = 0; // 重置正则表达式状态
            let match;
            while ((match = regex.exec(template.user_prompt)) !== null) {
                variables.add(match[1]);
            }
        }
        
        return Array.from(variables).sort();
    }

    /**
     * 生成变量输入框
     */
    generateVariableInputs(template) {
        const variables = this.extractVariables(template);
        const container = $('#variablesContainer');
        
        // 保存当前输入框中的变量值
        const existingValues = {};
        $('.variable-row').each(function() {
            const key = $(this).find('.variable-key').val().trim();
            const value = $(this).find('.variable-value').val().trim();
            if (key) {
                existingValues[key] = value;
            }
        });
        
        // 合并编辑时传入的变量值
        const allValues = { ...this.currentEditingVariables, ...existingValues };
        
        // 清空容器
        container.empty();
        
        if (variables.length === 0) {
            container.html('<p class="text-muted">此模板没有定义变量</p>');
            // 即便无变量也需要根据模板/模型选择状态刷新按钮可用性
            this.updateGenerateButtonState();
            return;
        }
        
        // 为每个变量生成输入框
        variables.forEach(varName => {
            const value = allValues[varName] || '';
            this.addVariableRow(varName, value, true);
        });
        
        // 清除临时变量
        this.currentEditingVariables = {};
        
        // 更新生成按钮状态
        this.updateGenerateButtonState();
    }

    /**
     * 添加变量行
     */
    addVariableRow(key = '', value = '', readonly = false) {
        const readonlyAttr = readonly ? 'readonly' : '';
        const rowHtml = `
            <div class="variable-row mb-2">
                <div class="row g-2">
                    <div class="col-md-4">
                        <input type="text" class="form-control variable-key" placeholder="变量名" value="${key}" ${readonlyAttr}>
                    </div>
                    <div class="col-md-8">
                        <input type="text" class="form-control variable-value" placeholder="请输入 ${key || '变量'} 的值" value="${value}">
                    </div>
                </div>
            </div>
        `;
        $('#variablesContainer').append(rowHtml);
    }

    /**
     * 收集变量数据
     */
    collectVariables() {
        const variables = {};
        $('.variable-row').each(function() {
            const key = $(this).find('.variable-key').val().trim();
            const value = $(this).find('.variable-value').val().trim();
            if (key) {
                variables[key] = value;
            }
        });
        return Object.keys(variables).length > 0 ? variables : null;
    }

    /**
     * 保存用例
     */
    async saveUseCase() {
        const id = $('#useCaseRowId').val();
        const formData = {
            use_case_name: $('#useCaseName').val().trim(),
            template_id: $('#useCaseTemplateId').val(),
            template_variables: this.collectVariables(),
            reference_answer: $('#useCaseReferenceAnswer').val().trim() || null,
            remarks: $('#useCaseRemarks').val().trim() || null
        };
        
        // 验证
        if (!formData.use_case_name) {
            UIHelper.showToast('请填写用例名称', 'warning');
            return;
        }

        if (!formData.template_id) {
            UIHelper.showToast('请选择提示词模板', 'warning');
            return;
        }
        
        try {
            $('#savePromptUseCase').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                // 更新
                await ApiService.promptUseCases.update(id, formData);
                UIHelper.showToast('用例更新成功', 'success');
            } else {
                // 创建
                await ApiService.promptUseCases.create(formData);
                UIHelper.showToast('用例创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('promptUseCaseModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#savePromptUseCase').prop('disabled', false).html('保存');
        }
    }

    /**
     * 检查所有变量是否已填写
     */
    checkAllVariablesFilled() {
        const variableInputs = $('#variablesContainer .variable-value');
        
        // 如果没有变量输入框，返回true（没有变量需要填写）
        if (variableInputs.length === 0) {
            return true;
        }
        
        let allFilled = true;
        variableInputs.each(function() {
            if (!$(this).val().trim()) {
                allFilled = false;
                return false; // 跳出循环
            }
        });
        return allFilled;
    }

    /**
     * 更新生成按钮状态
     */
    updateGenerateButtonState() {
        const modelId = $('#aiModelSelect').val();
        const allFilled = this.checkAllVariablesFilled();
        const hasTemplate = $('#useCaseTemplateId').val();
        $('#generateReferenceAnswer').prop('disabled', !modelId || !hasTemplate || !allFilled);
    }

    /**
     * AI生成参考答案
     */
    async generateReferenceAnswer() {
        console.log('生成参考答案按钮被点击');
        
        const modelId = $('#aiModelSelect').val();
        if (!modelId) {
            UIHelper.showToast('请先选择AI模型', 'warning');
            return;
        }
        
        const templateId = $('#useCaseTemplateId').val();
        if (!templateId) {
            UIHelper.showToast('请先选择模板', 'warning');
            return;
        }
        
        // 检查变量是否都已填写
        if (!this.checkAllVariablesFilled()) {
            UIHelper.showToast('请先填写完所有模板变量', 'warning');
            return;
        }
        
        // 获取模板信息
        const template = this.templates.find(t => t.id === templateId);
        if (!template) {
            UIHelper.showToast('模板信息未找到', 'error');
            return;
        }
        
        // 收集变量值
        const variables = this.collectVariables() || {};
        
        // 渲染提示词
        const systemPrompt = this.renderPromptForAPI(template.system_prompt, variables);
        const userPrompt = this.renderPromptForAPI(template.user_prompt, variables);
        
        console.log('渲染后的提示词:', { systemPrompt, userPrompt });
        
        try {
            // 显示生成中状态
            $('#generateReferenceAnswer')
                .prop('disabled', true)
                .html('<i class="fas fa-spinner fa-spin"></i> 生成中...');
            
            // 调用AI模型生成答案（通过后端中转，避免跨域问题）
            const aiModel = this.aiModels.find(m => m.id === modelId);
            if (!aiModel) {
                throw new Error('AI模型未找到');
            }
            
            console.log('使用的AI模型:', aiModel);
            
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
            
            console.log('请求数据:', requestData);
            
             // 通过后端API中转调用AI模型
            const result = await ApiService.aiModels.chatCompletion(modelId, requestData);
            console.log('API响应结果:', result);
            
            // 提取生成的答案
            const generatedAnswer = result.content || '';
            
            // 回填到参考答案输入框
            $('#useCaseReferenceAnswer').val(generatedAnswer);
            UIHelper.showToast('参考答案生成成功', 'success');
            
        } catch (error) {
            UIHelper.showToast('生成失败: ' + error.message, 'error');
            console.error('AI生成参考答案失败:', error);
        } finally {
            // 恢复按钮状态
            this.updateGenerateButtonState();
            $('#generateReferenceAnswer').html('<i class="fas fa-magic me-1"></i>模型生成');
        }
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
     * 删除用例
     */
    async deleteUseCase(id, name) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除提示词用例 "${name}" 吗？\n\n此操作无法撤销。`,
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
            await ApiService.promptUseCases.delete(id);
            UIHelper.showToast('用例删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 销毁组件（清理事件监听）
     */
    destroy() {
        $(document).off('click', '#addPromptUseCase');
        $(document).off('click', '#applyUseCaseFilters');
        $(document).off('click', '#resetUseCaseFilters');
        $(document).off('keypress', '#searchUseCaseKeyword');
        $(document).off('click', '.edit-use-case');
        $(document).off('click', '.delete-use-case');
        $(document).off('click', '.view-use-case');
        $(document).off('click', '#savePromptUseCase');
        $(document).off('click', '#promptUseCasesTableContent .page-link[data-page]');
        $(document).off('change', '#useCaseTemplateId');
        $(document).off('input', '.variable-value');
        $(document).off('click', '.preview-tab');
        $(document).off('change', '#aiModelSelect');
        $(document).off('input', '#variablesContainer .variable-value');
        $(document).off('click', '#generateReferenceAnswer');
    }
}
