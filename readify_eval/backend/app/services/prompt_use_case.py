"""
Prompt Use Case service
"""
import re
from typing import Optional, Dict, Any, Tuple, List, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.prompt_use_case import PromptUseCaseRepository
from app.repositories.prompt_template import PromptTemplateRepository
from app.schemas.prompt_use_case import (
    PromptUseCaseCreate, 
    PromptUseCaseUpdate, 
    PromptUseCaseResponse, 
    PromptUseCaseListResponse
)


class PromptUseCaseService:
    """
    Business logic for Prompt Use Case operations
    """
    
    def __init__(self, db: Session):
        self.repository = PromptUseCaseRepository(db)
        self.template_repository = PromptTemplateRepository(db)
        self.db = db
    
    @staticmethod
    def extract_variables(template_text: Optional[str]) -> Set[str]:
        """
        从模板文本中提取所有变量名
        
        Args:
            template_text: 模板文本
            
        Returns:
            变量名集合
        """
        if not template_text:
            return set()
        
        # 匹配所有 <$variable_name> 格式的变量
        # 变量名只能包含英文字母、数字和下划线
        variables = re.findall(r'<\$([a-zA-Z0-9_]+)>', template_text)
        return set(variables)
    
    @staticmethod
    def validate_variables(template_text: Optional[str], variables: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        验证所有模板变量是否都已提供且有效
        
        变量有效的条件：
        1. 变量存在于variables字典中
        2. 变量值转换为字符串后，去掉头尾空白字符不为空串
        
        Args:
            template_text: 模板文本
            variables: 变量字典
            
        Returns:
            (是否验证通过, 缺失或无效的变量列表)
        """
        if not template_text:
            return True, []
        
        # 提取模板中的所有变量
        required_vars = PromptUseCaseService.extract_variables(template_text)
        
        if not required_vars:
            return True, []
        
        # 检查哪些变量未提供或值为空
        invalid_vars = []
        for var_name in required_vars:
            # 检查变量是否存在
            if var_name not in (variables or {}):
                invalid_vars.append(var_name)
                continue
            
            # 检查变量值是否为空（转为字符串后去掉头尾空白）
            var_value = variables[var_name]
            if var_value is None:
                invalid_vars.append(var_name)
                continue
            
            # 转换为字符串并去除首尾空白
            str_value = str(var_value).strip()
            if not str_value:
                invalid_vars.append(var_name)
        
        return len(invalid_vars) == 0, sorted(invalid_vars)
    
    @staticmethod
    def render_template(template_text: Optional[str], variables: Optional[Dict[str, Any]], validate: bool = True) -> Optional[str]:
        """
        渲染模板文本，替换变量
        支持 <$variable_name> 格式的变量
        
        Args:
            template_text: 模板文本
            variables: 变量字典
            validate: 是否验证变量完整性（目前不再触发异常，仅保留参数兼容性）
            
        Returns:
            渲染后的文本
        """
        if not template_text:
            return template_text
        
        if not variables:
            variables = {}
        
        # 使用正则表达式匹配 <$variable_name> 格式的变量
        # 变量名只能包含英文字母、数字和下划线
        def replace_variable(match):
            var_name = match.group(1)
            # 如果变量不存在或值为空/仅空白，则使用空串
            if var_name not in variables or variables[var_name] is None:
                return ""
            value = str(variables[var_name])
            if not value.strip():
                return ""
            return value
        
        # 匹配 <$variable_name> 格式（变量名只能是英文字母、数字、下划线）
        rendered_text = re.sub(r'<\$([a-zA-Z0-9_]+)>', replace_variable, template_text)
        
        return rendered_text
    
    def create_use_case(self, use_case_in: PromptUseCaseCreate) -> PromptUseCaseResponse:
        """
        Create a new prompt use case
        
        Args:
            use_case_in: Prompt use case creation data
            
        Returns:
            Created prompt use case with rendered prompts
            
        Raises:
            HTTPException: If template not found
        """
        # 检查模板是否存在
        template = self.template_repository.get(use_case_in.template_id)
        if not template:
            raise HTTPException(
                status_code=404, 
                detail=f"找不到 ID 为 '{use_case_in.template_id}' 的模板"
            )
        
        # 渲染系统提示词和用户提示词
        rendered_system_prompt = self.render_template(
            template.system_prompt, 
            use_case_in.template_variables
        )
        rendered_user_prompt = self.render_template(
            template.user_prompt, 
            use_case_in.template_variables
        )
        
        # 创建用例数据
        use_case_dict = use_case_in.model_dump()
        use_case_dict['rendered_system_prompt'] = rendered_system_prompt
        use_case_dict['rendered_user_prompt'] = rendered_user_prompt
        
        use_case = self.repository.create(use_case_dict)
        return PromptUseCaseResponse.model_validate(use_case)
    
    def get_use_case(self, use_case_id: str) -> Optional[PromptUseCaseResponse]:
        """
        Get prompt use case by ID
        
        Args:
            use_case_id: Prompt use case ID
            
        Returns:
            Prompt use case or None
        """
        use_case = self.repository.get(use_case_id)
        if use_case:
            return PromptUseCaseResponse.model_validate(use_case)
        return None
    
    def get_use_cases(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        keyword: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> PromptUseCaseListResponse:
        """
        Get all prompt use cases with pagination and optional filters
        
        Supports filtering by template_id and keyword simultaneously.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            keyword: Keyword to search across multiple fields (use_case_name, remarks)
            template_id: Filter by template ID
            
        Returns:
            List of prompt use cases with total count
        """
        # 使用统一的get_all方法，支持同时使用template_id和keyword过滤
        use_cases = self.repository.get_all(
            skip=skip, 
            limit=limit, 
            keyword=keyword,
            template_id=template_id
        )
        
        # 使用count_filtered方法单独查询总数，传入相同的过滤条件
        total = self.repository.count_filtered(
            keyword=keyword,
            template_id=template_id
        )
        
        return PromptUseCaseListResponse(
            total=total,
            items=[PromptUseCaseResponse.model_validate(u) for u in use_cases]
        )
    
    def get_all_use_cases(self) -> PromptUseCaseListResponse:
        """
        Get all prompt use cases without pagination
        
        Returns:
            List of all prompt use cases ordered by updated_at desc
        """
        use_cases = self.repository.get_all(skip=0, limit=10000)
        
        return PromptUseCaseListResponse(
            total=len(use_cases),
            items=[PromptUseCaseResponse.model_validate(u) for u in use_cases]
        )
    
    def update_use_case(
        self, 
        use_case_id: str, 
        use_case_in: PromptUseCaseUpdate
    ) -> Optional[PromptUseCaseResponse]:
        """
        Update a prompt use case
        
        Args:
            use_case_id: Prompt use case ID
            use_case_in: Updated prompt use case data
            
        Returns:
            Updated prompt use case or None
            
        Raises:
            HTTPException: If template not found when template_id is being updated
        """
        # 获取现有用例
        existing_use_case = self.repository.get(use_case_id)
        if not existing_use_case:
            return None
        
        # 如果更新了template_id，检查新模板是否存在
        template_id_to_use = use_case_in.template_id if use_case_in.template_id else existing_use_case.template_id
        template = self.template_repository.get(template_id_to_use)
        if not template:
            raise HTTPException(
                status_code=404, 
                detail=f"找不到 ID 为 '{template_id_to_use}' 的模板"
            )
        
        # 准备更新数据
        use_case_dict = use_case_in.model_dump(exclude_unset=True)
        
        # 如果template_id或template_variables发生变化，重新渲染
        if use_case_in.template_id or use_case_in.template_variables is not None:
            # 确定要使用的变量
            variables_to_use = (
                use_case_in.template_variables 
                if use_case_in.template_variables is not None 
                else existing_use_case.template_variables
            )
            
            # 重新渲染
            use_case_dict['rendered_system_prompt'] = self.render_template(
                template.system_prompt, 
                variables_to_use
            )
            use_case_dict['rendered_user_prompt'] = self.render_template(
                template.user_prompt, 
                variables_to_use
            )
        
        use_case = self.repository.update(use_case_id, use_case_dict)
        if use_case:
            return PromptUseCaseResponse.model_validate(use_case)
        return None
    
    def delete_use_case(self, use_case_id: str) -> bool:
        """
        Delete a prompt use case
        
        Args:
            use_case_id: Prompt use case ID
            
        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(use_case_id)

