<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <Navbar />

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="content-container">
        <div class="welcome-section">
          <h1>Welcome to Readify Notebook Assistant</h1>
          
          <div class="action-bar">
            <div class="action-left">
              <el-button type="primary" @click="handleCreateProject" :icon="Plus">
                创建工程
              </el-button>
            </div>
            <div class="action-right">
              <el-button-group>
                <el-button 
                  :type="viewMode === 'card' ? 'primary' : 'default'"
                  @click="viewMode = 'card'"
                  :icon="Grid"
                />
                <el-button 
                  :type="viewMode === 'list' ? 'primary' : 'default'"
                  @click="viewMode = 'list'"
                  :icon="List"
                />
              </el-button-group>
            </div>
          </div>
        </div>

        <!-- 工程列表 -->
        <div class="projects-grid" v-loading="loading">
          <el-empty v-if="projects.length === 0" description="暂无工程" />
          <template v-else>
            <!-- 卡片视图 -->
            <el-row v-if="viewMode === 'card'" :gutter="16">
              <el-col v-for="project in projects" :key="project.id" :span="4.8">
                <ProjectCard 
                  :project="project" 
                  :color-index="projectColorIndices[project.id]" 
                  :soft-colors="softColors"
                  @click="handleCardClick"
                  @edit="handleEditProject"
                  @delete="handleDeleteProject"
                />
              </el-col>
            </el-row>

            <!-- 列表视图 -->
            <ProjectList 
              v-else 
              :projects="projects"
              @click="handleCardClick"
              @edit="handleEditProject"
              @delete="handleDeleteProject"
            />
          </template>
        </div>
      </div>
    </div>

    <!-- 创建/编辑工程对话框 -->
    <ProjectDialog
      v-model:visible="dialogVisible"
      :type="dialogType"
      :project="currentProject"
      :submitting="submitting"
      @submit="handleSubmitProject"
      @cancel="dialogVisible = false"
    />

    <!-- 文件上传对话框 -->
    <UploadDialog
      v-model:visible="uploadDialogVisible"
      :project-id="currentProject?.id || 0"
      :project-name="currentProject?.name || ''"
      :upload-headers="uploadHeaders"
      @success="handleUploadSuccess"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Grid, List } from '@element-plus/icons-vue'
import { getAuthHeader } from '@/utils/auth'
import type { ProjectVO } from '@/types/project'
import { getMyProjects, createProject, updateProject, deleteProject, getProjectFiles } from '@/api/project'

// 导入组件
import Navbar from '@/components/Navbar.vue'
import ProjectCard from '@/components/ProjectCard.vue'
import ProjectList from '@/components/ProjectList.vue'
import ProjectDialog from '@/components/ProjectDialog.vue'
import UploadDialog from '@/components/UploadDialog.vue'

const store = useStore()
const router = useRouter()

const loading = ref(false)
const projects = ref<ProjectVO[]>([])
const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitting = ref(false)
const uploadDialogVisible = ref(false)
const currentProject = ref<ProjectVO | null>(null)
const viewMode = ref('card') // 'card' 或 'list'

// 添加柔和的背景色数组
const softColors = [
  { light: 'rgb(237, 239, 250)', dark: 'rgb(227, 229, 245)' },
  { light: 'rgb(242, 242, 232)', dark: 'rgb(232, 232, 222)' },
  { light: 'rgb(242, 239, 233)', dark: 'rgb(232, 229, 223)' },
  { light: 'rgb(240, 244, 241)', dark: 'rgb(230, 234, 231)' },
  { light: 'rgb(243, 237, 241)', dark: 'rgb(233, 227, 231)' },
  { light: 'rgb(235, 242, 244)', dark: 'rgb(225, 232, 234)' },
]

// 获取随机颜色的函数
const getRandomColorIndex = () => Math.floor(Math.random() * softColors.length)

// 为每个项目分配一个随机颜色索引
const projectColorIndices = ref<{[key: number]: number}>({})

// 加载工程列表
const loadProjects = async () => {
  try {
    loading.value = true
    const res = await getMyProjects()
    projects.value = res.data
    // 为每个项目分配随机颜色
    projects.value.forEach(project => {
      if (!projectColorIndices.value[project.id]) {
        projectColorIndices.value[project.id] = getRandomColorIndex()
      }
    })
  } catch (error) {
    console.error('Failed to load projects:', error)
  } finally {
    loading.value = false
  }
}

// 创建工程
const handleCreateProject = () => {
  dialogType.value = 'create'
  currentProject.value = null
  dialogVisible.value = true
}

// 编辑工程
const handleEditProject = (project: ProjectVO) => {
  dialogType.value = 'edit'
  currentProject.value = project
  dialogVisible.value = true
}

// 删除工程
const handleDeleteProject = async (project: ProjectVO) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除该工程吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteProject(project.id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}

// 提交工程表单
const handleSubmitProject = async (form: { id?: number, name: string, description: string }) => {
  try {
    submitting.value = true
    if (dialogType.value === 'create') {
      await createProject(form)
      ElMessage.success('创建成功')
    } else {
      await updateProject(form.id!, form)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    loadProjects()
  } catch (error) {
    console.error('Failed to submit project:', error)
  } finally {
    submitting.value = false
  }
}

// 上传相关的 headers
const uploadHeaders = computed(() => ({
  Authorization: getAuthHeader()
}))

// 点击卡片处理
const handleCardClick = async (project: ProjectVO) => {
  try {
    const res = await getProjectFiles(project.id)
    if (res.data && res.data.length > 0) {
      // 有文件，跳转到项目详情页
      router.push(`/project/${project.id}`)
    } else {
      // 无文件，显示上传对话框
      currentProject.value = project
      uploadDialogVisible.value = true
    }
  } catch (error) {
    console.error('Failed to get project files:', error)
    ElMessage.error('获取项目文件失败')
  }
}

// 上传成功的回调
const handleUploadSuccess = () => {
  // 上传成功后跳转到项目详情页
  if (currentProject.value) {
    router.push(`/project/${currentProject.value.id}`)
  }
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@600&display=swap');

.home-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.navbar) {
  background-color: #ffffff;
}

.main-content {
  flex: 1;
  width: 100%;
  overflow-y: auto;
  background-color: #ffffff;
  padding: 24px;
}

.content-container {
  width: 80%;
  height: 100%;
  margin: 0 auto;
  padding-top: 20px;
}

.welcome-section {
  margin-bottom: 40px;
  text-align: left;
}

.welcome-section h1 {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 60px 0;
  padding: 40px 0;
  color: #000;
  text-align: left;
  letter-spacing: -1px;
  font-family: 'Playfair Display', 'Times New Roman', Georgia, serif;
}

.section-divider {
  padding-bottom: 20px;
  border-bottom: 2px solid #ebeef5;
  margin-bottom: 20px;
}

.section-divider h2 {
  font-size: 24px;
  font-weight: 500;
  color: #303133;
  margin: 0;
}

.action-bar {
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-left {
  display: flex;
  align-items: center;
}

.action-right {
  display: flex;
  align-items: center;
}

.action-bar :deep(.el-button--primary) {
  background: #000;
  border: none;
  padding: 10px 24px;
  height: auto;
  transition: all 0.3s;
  border-radius: 24px;
  color: white;
}

.action-bar :deep(.el-button--primary:hover) {
  background: #333;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.projects-grid {
  min-height: 200px;
}

.projects-grid :deep(.el-row) {
  margin: 0;
  width: 100%;
}

.projects-grid :deep(.el-col) {
  padding: 16px;
  width: 20%;
  flex: 0 0 20%;
}

.action-right :deep(.el-button-group) {
  border: 1px solid #dcdfe6;
  border-radius: 24px;
  overflow: hidden;
  display: flex;
  align-items: stretch;
  height: 40px;
}

.action-right :deep(.el-button-group .el-button) {
  margin: 0;
  border: none;
  padding: 0 20px;
  border-radius: 0;
  color: #606266;
  background: #ffffff;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, color 0.3s;
  transform: none !important;
  min-width: 100px;
  position: relative;
}

.action-right :deep(.el-button-group .el-button.el-button--primary) {
  background: #000;
  color: #ffffff;
}

.action-right :deep(.el-button-group .el-button.el-button--primary::before) {
  content: "✓";
  position: absolute;
  left: 12px;
  opacity: 1;
  transition: opacity 0.3s;
}

.action-right :deep(.el-button-group .el-button::before) {
  content: "✓";
  position: absolute;
  left: 12px;
  opacity: 0;
}

.action-right :deep(.el-button-group .el-button:hover) {
  transform: none !important;
}

.action-right :deep(.el-button-group .el-button .el-icon) {
  margin: 0;
}
</style> 