"""
专业智能体的名称和描述配置文件

这个文件定义了系统中所有专业智能体的名称和描述，便于统一管理和引用。
使用这些名称替代代码中的硬编码字符串，可以提高代码的可维护性。
"""

# 智能体名称常量
class AgentNames:
    # 协调器智能体
    COORDINATOR = "COORDINATOR"

    # 问题回答智能体
    QUESTIONER = "QUESTIONER"
    
    # 笔记智能体
    NOTE_AGENT = "NOTE_AGENT"


# 智能体描述
AGENT_DESCRIPTIONS = {
    AgentNames.COORDINATOR: "负责分析用户需求并协调调度其他专业智能体，合理安排工作流程",
    AgentNames.QUESTIONER: "专注于回答用户问题，善于从文档中检索相关信息提供精准解答",
    AgentNames.NOTE_AGENT: "专注于处理文档笔记和内容摘要，提供智能笔记管理和关键信息提取服务",
}

def is_agent_name(name: str) -> bool:
    """
    判断给定的字符串是否为有效的智能体名称

    Args:
        name: 要判断的字符串

    Returns:
        bool: 如果给定的字符串为有效的智能体名称，则返回True，否则返回False
    """
    return name in get_all_agent_names()

# 获取所有可用的智能体名称列表
def get_all_agent_names():
    """
    获取所有可用的智能体名称列表
    
    Returns:
        list: 智能体名称列表
    """
    return [getattr(AgentNames, attr) for attr in dir(AgentNames) 
            if not attr.startswith('__') and isinstance(getattr(AgentNames, attr), str)]

# 获取智能体描述
def get_agent_description(agent_name):
    """
    获取指定智能体的描述
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        str: 智能体描述，如果找不到则返回默认描述
    """
    return AGENT_DESCRIPTIONS.get(agent_name, "未提供描述的专业智能体") 