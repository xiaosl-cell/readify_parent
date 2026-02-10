/**
 * UI 辅助工具类
 * 提供通用的UI交互方法
 */

const UIHelper = {
    /**
     * 显示Toast提示
     * @param {string} message - 提示消息
     * @param {string} type - 类型: success, error, warning, info
     */
    showToast: function(message, type = 'info') {
        const toastContainer = $('#toastContainer');
        
        // 如果容器不存在，创建它
        if (toastContainer.length === 0) {
            $('body').append(`
                <div id="toastContainer" class="position-fixed top-0 end-0 p-3" style="z-index: 9999"></div>
            `);
        }
        
        const toastId = 'toast-' + Date.now();
        const bgClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';
        
        const toast = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        $('#toastContainer').append(toast);
        
        const toastElement = document.getElementById(toastId);
        const bsToast = new bootstrap.Toast(toastElement, { delay: 3000 });
        bsToast.show();
        
        // 移除已隐藏的toast
        $(toastElement).on('hidden.bs.toast', function() {
            $(this).remove();
        });
    },

    /**
     * 格式化日期时间
     * @param {string} dateString - ISO日期字符串
     * @returns {string} 格式化后的日期时间
     */
    formatDateTime: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },

    /**
     * 确认对话框
     * @param {string} message - 确认消息
     * @param {object} options - 配置选项
     * @param {string} options.title - 对话框标题
     * @param {string} options.confirmText - 确认按钮文字
     * @param {string} options.cancelText - 取消按钮文字
     * @param {string} options.confirmClass - 确认按钮样式类
     * @returns {Promise<boolean>} 用户是否确认
     */
    confirmDialog: function(message, options = {}) {
        return new Promise((resolve) => {
            const {
                title = '确认操作',
                confirmText = '确认',
                cancelText = '取消',
                confirmClass = 'btn-danger'
            } = options;
            
            // 移除已存在的确认对话框
            $('#confirmDialog').remove();
            
            // 将消息中的换行符转换为HTML换行
            const formattedMessage = message.replace(/\n/g, '<br>');
            
            // 创建模态框HTML
            const modalHtml = `
                <div class="modal fade" id="confirmDialog" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                                    ${title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p class="mb-0" style="white-space: pre-line;">${formattedMessage}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="confirmDialogCancel">
                                    ${cancelText}
                                </button>
                                <button type="button" class="btn ${confirmClass}" id="confirmDialogConfirm">
                                    ${confirmText}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 添加到页面
            $('body').append(modalHtml);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('confirmDialog'));
            modal.show();
            
            // 绑定确认按钮事件
            $('#confirmDialogConfirm').off('click').on('click', function() {
                modal.hide();
                resolve(true);
            });
            
            // 绑定取消按钮和关闭事件
            $('#confirmDialogCancel, #confirmDialog .btn-close').off('click').on('click', function() {
                modal.hide();
                resolve(false);
            });
            
            // 模态框关闭后移除
            $('#confirmDialog').on('hidden.bs.modal', function() {
                $(this).remove();
            });
        });
    },

    /**
     * 显示加载动画
     * @param {string} containerId - 容器ID
     * @param {string} message - 加载提示文字
     */
    showLoading: function(containerId, message = '加载中...') {
        $(`#${containerId}`).html(`
            <div class="loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${message}</span>
                </div>
                <p class="mt-3">${message}</p>
            </div>
        `);
    },

    /**
     * 显示空数据状态
     * @param {string} containerId - 容器ID
     * @param {string} message - 提示文字
     * @param {string} icon - Font Awesome图标类名
     */
    showEmptyState: function(containerId, message = '暂无数据', icon = 'fa-inbox') {
        $(`#${containerId}`).html(`
            <div class="empty-state">
                <i class="fas ${icon}"></i>
                <p>${message}</p>
            </div>
        `);
    },

    /**
     * 显示错误状态
     * @param {string} containerId - 容器ID
     * @param {string} message - 错误消息
     */
    showError: function(containerId, message = '加载失败，请稍后重试') {
        $(`#${containerId}`).html(`
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>${message}</p>
            </div>
        `);
    }
};

