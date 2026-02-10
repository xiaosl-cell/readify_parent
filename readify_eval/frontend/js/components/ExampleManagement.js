/**
 * 示例管理组件
 * 负责示例的增删改查操作
 */

class ExampleManagement {
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
        await TemplateLoader.loadInto('examples.html', 'content-area');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const self = this;
        
        // 添加示例按钮
        $(document).off('click', '#addExample').on('click', '#addExample', function() {
            self.showModal();
        });
        
        // 应用过滤
        $(document).off('click', '#applyExampleFilters').on('click', '#applyExampleFilters', function() {
            self.applyFilters();
        });
        
        // 重置过滤
        $(document).off('click', '#resetExampleFilters').on('click', '#resetExampleFilters', function() {
            $('#filterActive').val('');
            self.currentFilters = {};
            self.loadData();
        });
        
        // 编辑按钮
        $(document).off('click', '.edit-example').on('click', '.edit-example', function() {
            const id = $(this).data('id');
            self.showModal(id);
        });
        
        // 删除按钮
        $(document).off('click', '.delete-example').on('click', '.delete-example', function() {
            const id = $(this).data('id');
            const title = $(this).data('title');
            self.deleteExample(id, title);
        });
        
        // 保存示例
        $(document).off('click', '#saveExample').on('click', '#saveExample', function() {
            self.saveExample();
        });
        
        // 分页按钮（仅限主列表的分页）
        $(document).off('click', '#examplesTableContent .page-link[data-page]').on('click', '#examplesTableContent .page-link[data-page]', function(e) {
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
        
        const activeFilter = $('#filterActive').val();
        if (activeFilter === 'true') {
            this.currentFilters.active_only = true;
        }
        
        this.currentPage = 0;
        this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            $('#examplesTableContent').html(`
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
            
            const response = await ApiService.examples.getAll(params);
            
            this.totalItems = response.total;
            this.renderTable(response.items);
        } catch (error) {
            UIHelper.showToast('加载数据失败: ' + error.message, 'error');
            $('#examplesTableContent').html(`
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
            $('#examplesTableContent').html(`
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
                        <th style="width: 25%">标题</th>
                        <th style="width: 35%">描述</th>
                        <th style="width: 10%">状态</th>
                        <th style="width: 15%">创建时间</th>
                        <th style="width: 15%">操作</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        items.forEach(item => {
            const statusBadge = item.is_active 
                ? '<span class="badge bg-success">激活</span>' 
                : '<span class="badge bg-secondary">未激活</span>';
            
            const description = item.description || '<em class="text-muted">无描述</em>';
            
            tableHtml += `
                <tr>
                    <td><strong>${item.title}</strong></td>
                    <td>${description}</td>
                    <td>${statusBadge}</td>
                    <td>${UIHelper.formatDateTime(item.created_at)}</td>
                    <td class="action-buttons">
                        <button class="btn btn-sm btn-outline-primary edit-example" data-id="${item.id}">
                            <i class="fas fa-edit"></i> 编辑
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-example" data-id="${item.id}" data-title="${item.title}">
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
        
        $('#examplesTableContent').html(tableHtml);
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
            $('#exampleModalLabel').text('编辑示例');
            
            try {
                const example = await ApiService.examples.getById(id);
                
                $('#exampleRowId').val(example.id);
                $('#exampleTitle').val(example.title);
                $('#exampleDescription').val(example.description || '');
                $('#isActive').prop('checked', example.is_active);
            } catch (error) {
                UIHelper.showToast('加载示例数据失败: ' + error.message, 'error');
                return;
            }
        } else {
            // 创建模式
            $('#exampleModalLabel').text('添加示例');
            $('#exampleForm')[0].reset();
            $('#exampleRowId').val('');
            $('#isActive').prop('checked', true);
        }
        
        const modal = new bootstrap.Modal(document.getElementById('exampleModal'));
        modal.show();
    }

    /**
     * 保存示例
     */
    async saveExample() {
        const id = $('#exampleRowId').val();
        const formData = {
            title: $('#exampleTitle').val().trim(),
            description: $('#exampleDescription').val().trim() || null,
            is_active: $('#isActive').is(':checked')
        };
        
        // 验证
        if (!formData.title) {
            UIHelper.showToast('请填写标题', 'warning');
            return;
        }
        
        try {
            $('#saveExample').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> 保存中...');
            
            if (id) {
                // 更新
                await ApiService.examples.update(id, formData);
                UIHelper.showToast('示例更新成功', 'success');
            } else {
                // 创建
                await ApiService.examples.create(formData);
                UIHelper.showToast('示例创建成功', 'success');
            }
            
            bootstrap.Modal.getInstance(document.getElementById('exampleModal')).hide();
            this.loadData();
        } catch (error) {
            UIHelper.showToast('保存失败: ' + error.message, 'error');
        } finally {
            $('#saveExample').prop('disabled', false).html('保存');
        }
    }

    /**
     * 删除示例
     */
    async deleteExample(id, title) {
        const confirmed = await UIHelper.confirmDialog(
            `确定要删除示例 "${title}" 吗？\n\n此操作无法撤销。`,
            {
                title: '删除示例',
                confirmText: '确认删除',
                cancelText: '取消',
                confirmClass: 'btn-danger'
            }
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            await ApiService.examples.delete(id);
            UIHelper.showToast('示例删除成功', 'success');
            this.loadData();
        } catch (error) {
            UIHelper.showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 销毁组件（清理事件监听）
     */
    destroy() {
        $(document).off('click', '#addExample');
        $(document).off('click', '#applyExampleFilters');
        $(document).off('click', '#resetExampleFilters');
        $(document).off('click', '.edit-example');
        $(document).off('click', '.delete-example');
        $(document).off('click', '#saveExample');
        $(document).off('click', '#examplesTableContent .page-link[data-page]');
    }
}

