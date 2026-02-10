/**
 * 模板加载器
 * 负责加载和缓存HTML模板文件
 */

const TemplateLoader = {
    // 模板缓存
    cache: {},
    
    // 模板基础路径
    basePath: 'templates/',

    /**
     * 加载模板文件
     * @param {string} templatePath - 模板路径（相对于templates目录）
     * @param {boolean} useCache - 是否使用缓存，默认true
     * @returns {Promise<string>} 模板HTML内容
     */
    load: async function(templatePath, useCache = true) {
        // 检查缓存
        if (useCache && this.cache[templatePath]) {
            return this.cache[templatePath];
        }

        try {
            const response = await fetch(`${this.basePath}${templatePath}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load template: ${templatePath}`);
            }
            
            const html = await response.text();
            
            // 存入缓存
            if (useCache) {
                this.cache[templatePath] = html;
            }
            
            return html;
        } catch (error) {
            console.error('Template loading error:', error);
            throw error;
        }
    },

    /**
     * 加载模板并渲染到指定容器
     * @param {string} templatePath - 模板路径
     * @param {string} containerId - 容器ID（不含#）
     * @returns {Promise<void>}
     */
    loadInto: async function(templatePath, containerId) {
        const html = await this.load(templatePath);
        $(`#${containerId}`).html(html);
    },

    /**
     * 加载多个模板
     * @param {Array<string>} templatePaths - 模板路径数组
     * @returns {Promise<Object>} 返回包含所有模板的对象
     */
    loadMultiple: async function(templatePaths) {
        const promises = templatePaths.map(path => this.load(path));
        const results = await Promise.all(promises);
        
        const templates = {};
        templatePaths.forEach((path, index) => {
            templates[path] = results[index];
        });
        
        return templates;
    },

    /**
     * 清空模板缓存
     * @param {string} templatePath - 可选，指定清空某个模板，不传则清空全部
     */
    clearCache: function(templatePath = null) {
        if (templatePath) {
            delete this.cache[templatePath];
        } else {
            this.cache = {};
        }
    },

    /**
     * 预加载模板（提前加载到缓存中）
     * @param {Array<string>} templatePaths - 要预加载的模板路径数组
     */
    preload: async function(templatePaths) {
        await this.loadMultiple(templatePaths);
        console.log(`Preloaded ${templatePaths.length} templates`);
    },

    /**
     * 将模板追加到容器（而不是替换）
     * @param {string} templatePath - 模板路径
     * @param {string} containerId - 容器ID（不含#）
     */
    appendTo: async function(templatePath, containerId) {
        const html = await this.load(templatePath);
        $(`#${containerId}`).append(html);
    }
};

