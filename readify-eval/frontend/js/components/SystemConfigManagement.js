/**
 * 系统配置管理组件
 * 负责系统配置的增删改查操作
 */

class SystemConfigManagement {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalItems = 0;
        this.currentFilters = {};
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
        await TemplateLoader.loadInto('system-configs.html', 'content-area');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 添加配置按钮
        $(document).off('click', '#addSystemConfig').on('click', '#addSystemConfig', function() {
            self.showModal();
        });
        
        // 应用过滤
        $(document).off('click', '#applyConfigFilters').on('click', '#applyConfigFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetConfigFilters').on('click', '#resetConfigFilters', function() {
            $('#searchKeyword').val('');
            self.currentFilters = {};
            self.loadData();
        });
        
        // 搜索框回车
        $(document).off('keypress', '#searchKeyword').on('keypress', '#searchKeyword', function(e) {
            if (e.which === 13) {
                self.applyFilters();
            }
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-config').on('click', '.edit-config', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-config').on('click', '.delete-config', function() {
            const id = $(this).data('id');
            const name = $(this).data('name');
            self.deleteConfig(id, name);
        });
        
        // 查看详情按钮
        $(document).off('click', '.view-config').on('click', '.view-config', function() {
            const id = $(this).data('id');
            self.viewConfig(id);
        });
        
        // 保存配置
        $(document).off('click', '#saveSystemConfig').on('click', '#saveSystemConfig', function() {
            self.saveConfig();
        });
        
        // 分页按钮（仅限主列表的分页）
        $(document).off('click', '#systemConfigsTableContent .page-link[data-page]').on('click', '#systemConfigsTableContent .page-link[data-page]', function(e) {
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
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#systemConfigsTableContent').html(`
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
            
            const response = await ApiService.systemConfigs.getAll(params);
            
            this.totalItems = response.total;
            this.renderTable(response.items);
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#systemConfigsTableContent').html(`
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
            $('#systemConfigsTableContent').html(`
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
                        <th style="width: 15%">配置编码</th>
                        <th style="width: 15%">配置名称</th>
                        <th style="width: 20%">配置描述</th>
                        <th style="width: 25%">配置内容</th>
                        <th style="width: 10%">更新时间</th>
                        <th style="width: 15%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            // 截断长文本并添加提示
            const description = this.truncateText(item.config_description || '<em class="text-muted">无</em>', 50);
            const content = this.truncateText(item.config_content, 100);
            
            tableHtml += `
                <tr>
                    <td><strong>${item.config_code}</strong></td>
                    <td>${item.config_name}</td>
                    <td><div class="text-truncate-cell" title="${this.escapeHtml(item.config_description || '')}">${description}</div></td>
                    <td><div class="text-truncate-cell" title="${this.escapeHtml(item.config_content)}">${content}</div></td>
                    <td>${UIHelper.formatDateTime(item.updated_at)}</td>
                    <td class="action-buttons">
                        <button class="btn btn-sm btn-outline-info view-config" data-id="${item.id}" title="查看详情">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary edit-config" data-id="${item.id}" title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-config" data-id="${item.id}" data-name="${item.config_name}" title="删除">
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
        
        $('#systemConfigsTableContent').html(tableHtml);
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
     * 查看配置详情
     */
    async viewConfig(id) {
        try {
            const config = await ApiService.systemConfigs.getById(id);
            
            const detailHtml = `
                <div class="config-detail">
                    <div class="mb-3">
                        <strong>配置编码：</strong>${config.config_code}
                    </div>
                    <div class="mb-3">
                        <strong>配置名称：</strong>${config.config_name}
                    </div>
                    <div class="mb-3">
                        <strong>配置描述：</strong>
                        <div class="config-content">${config.config_description || '<em class="text-muted">无</em>'}</div>
                    </div>
                    <div class="mb-3">
                        <strong>配置内容：</strong>
                        <div class="config-content">${this.formatConfigContent(config.config_content)}</div>
                    </div>
                    <div class="mb-3">
                        <strong>创建时间：</strong>${UIHelper.formatDateTime(config.created_at)}
                    </div>
                    <div class="mb-3">
                        <strong>更新时间：</strong>${UIHelper.formatDateTime(config.updated_at)}
                    </div>
                </div>
            `;
            
            // 创建临时模态框显示详情
            const modalHtml = `
                <div class="modal fade" id="configDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">系统配置详情</h5>
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
            $('#configDetailModal').remove();
            
            // 添加新的模态框
            $('body').append(modalHtml);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('configDetailModal'));
            modal.show();
            
            // 模态框关闭后移除
            $('#configDetailModal').on('hidden.bs.modal', function() {
                $(this).remove();
            });
            
        } catch (error) {
            UIHelper.showToast('加载配置详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 格式化配置内容
     */
    formatConfigContent(content) {
        if (!content) return '<em class="text-muted">无</em>';
        
        // 尝试解析为JSON并格式化显示
        try {
            const parsed = JSON.parse(content);
            return `<pre class="json-content">${JSON.stringify(parsed, null, 2)}</pre>`;
        } catch (e) {
            // 如果不是JSON，按原样显示
            return `<pre class="text-content">${this.escapeHtml(content)}</pre>`;
        }
    }

    /**
     * 显示模态框（创建或编辑）
     */
    async showModal(id = null) {
        if (id) {
            // 编辑模式
            $('#systemConfigModalLabel').text('编辑系统配置');
            
            try {
                const config = await ApiService.systemConfigs.getById(id);
                
                $('#configRowId').val(config.id);
                $('#configCode').val(config.config_code).prop('readonly', true);
                $('#configName').val(config.config_name);
                $('#configDescription').val(config.config_description || '');
                $('#configContent').val(config.config_content);
            } catch (error) {
                UIHelper.showToast('加载配置数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#systemConfigModalLabel').text('添加系统配置');
            $('#systemConfigForm')[0].reset();
            $('#configRowId').val('');
            $('#configCode').prop('readonly', false);
        }
        
        const modal = new bootstrap.Modal(document.getElementById('systemConfigModal'));
        modal.show();
    }

    /**
     * 保存配置
     */
    async saveConfig() {
        const id = $('#configRowId').val();
        const formData = {
            config_code: $('#configCode').val().trim(),
            config_name: $('#configName').val().trim(),
            config_description: $('#configDescription').val().trim() || null,
            config_content: $('#configContent').val().trim()
        };
        
        // 验证
        if (!formData.config_code) {
            UIHelper.showToast('请填写配置编码', 'warning');
            return;
        }
        
        if (!formData.config_name) {
            UIHelper.showToast('请填写配置名称', 'warning');
            return;
        }
        
        if (!formData.config_content) {
            UIHelper.showToast('请填写配置内容', 'warning');
            return;
        }
        
        try {
            $('#saveSystemConfig').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                // 更新
                await ApiService.systemConfigs.update(id, formData);
                UIHelper.showToast('配置更新成功', 'success');
            } else {
                // 创建
                await ApiService.systemConfigs.create(formData);
                UIHelper.showToast('配置创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('systemConfigModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveSystemConfig').prop('disabled', false).html('保存');
        }
    }

    /**
     * 删除配置
     */
    async deleteConfig(id, name) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除系统配置 "${name}" 吗？\n\n此操作无法撤销。`,
            {
                title: '删除系统配置',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.systemConfigs.delete(id);
            UIHelper.showToast('配置删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 销毁组件（清理事件监听）
     */
    destroy() {
        $(document).off('click', '#addSystemConfig');
        $(document).off('click', '#applyConfigFilters');
        $(document).off('click', '#resetConfigFilters');
        $(document).off('keypress', '#searchKeyword');
        $(document).off('click', '.edit-config');
        $(document).off('click', '.delete-config');
        $(document).off('click', '.view-config');
        $(document).off('click', '#saveSystemConfig');
        $(document).off('click', '#systemConfigsTableContent .page-link[data-page]');
    }
}

