import json
import logging
from typing import Any, Type, TypeVar, Optional, Dict, Union, Callable, List

from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser, BaseOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

def _create_parser(parser_type: Type[BaseOutputParser], pydantic: Type[T]) -> BaseOutputParser:
    """
    创建指定类型的解析器
    
    Args:
        parser_type: 解析器类型(JsonOutputParser或PydanticOutputParser)
        pydantic: Pydantic模型类
        
    Returns:
        解析器实例
    """
    return parser_type(pydantic_object=pydantic)

def _parse_with_llm(
    instruction: str,
    source_text: str,
    parser: BaseOutputParser,
    model: str = "gpt-4o-mini"
) -> Any:
    """
    使用LLM进行解析的核心逻辑
    
    Args:
        instruction: 提取指令
        source_text: 提取源文本
        parser: 解析器实例
        model: 模型名称
        
    Returns:
        解析结果
        
    Raises:
        ValueError: 当解析失败且无法修复时抛出
    """
    # 创建LLM
    llm = ChatOpenAI(model=model)
    
    # 创建提示模板
    prompt = PromptTemplate(
        template="{instruction}\n提取文本：{source_text}\n{format_instructions}",
        input_variables=["instruction", "source_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # 调用LLM
    input_prompt = prompt.format_prompt(instruction=instruction, source_text=source_text)
    output = llm.invoke(input_prompt)
    
    try:
        # 尝试解析
        return parser.invoke(output.content)
    except (json.JSONDecodeError, ValueError) as e:
        # 解析失败，尝试使用修复解析器
        logger.warning("初次解析失败，尝试修复: %s", str(e))
        fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)
        return fixing_parser.invoke(output.content)

def parse_to_json(instruction: str, source_text: str, pydantic: Type[T], model: str = "gpt-4o-mini") -> str:
    """
    将文本解析为JSON字符串
    
    本函数使用LLM从源文本中提取信息,并按照指定的Pydantic模型格式输出JSON字符串。
    如果解析失败，会自动尝试修复。
    
    Args:
        instruction: 提取指令,告诉LLM如何解析文本
        source_text: 需要提取信息的源文本
        pydantic: 定义输出格式的Pydantic模型类
        model: 使用的LLM模型名称,默认为"gpt-4o-mini"
        
    Returns:
        符合Pydantic模型格式的JSON字符串
        
    Examples:
        >>> class DateTime(BaseModel):
        ...     year: int
        ...     month: int
        ...     day: int
        >>> result = parse_to_json(
        ...     "提取日期",
        ...     "2024年2月24日",
        ...     DateTime
        ... )
        >>> print(result)
        {"year": 2024, "month": 2, "day": 24}
    """
    parser = _create_parser(JsonOutputParser, pydantic)
    result = _parse_with_llm(instruction, source_text, parser, model)
    return json.dumps(result, ensure_ascii=False)
def parse_to_type(instruction: str, source_text: str, pydantic: Type[T], model: str = "gpt-4o-mini") -> T:
    """
    将文本解析为指定的Pydantic模型实例
    
    本函数使用LLM从源文本中提取信息,并实例化为指定的Pydantic模型。
    如果解析失败，会自动尝试修复。
    
    Args:
        instruction: 提取指令,告诉LLM如何解析文本
        source_text: 需要提取信息的源文本
        pydantic: 定义输出类型的Pydantic模型类
        model: 使用的LLM模型名称,默认为"gpt-4o-mini"
        
    Returns:
        Pydantic模型实例
        
    Examples:
        >>> class DateTime(BaseModel):
        ...     year: int
        ...     month: int
        ...     day: int
        >>> result = parse_to_type(
        ...     "提取日期",
        ...     "2024年2月24日",
        ...     DateTime
        ... )
        >>> print(f"{result.year}年{result.month}月{result.day}日")
        2024年2月24日
    """
    parser = _create_parser(PydanticOutputParser, pydantic)
    return _parse_with_llm(instruction, source_text, parser, model)