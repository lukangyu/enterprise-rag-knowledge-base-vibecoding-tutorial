from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    system_prompt: str
    user_template: str
    context_placeholder: str = "{context}"
    query_placeholder: str = "{query}"


DEFAULT_SYSTEM_PROMPT = """你是一个专业的企业知识库问答助手。你的职责是根据提供的上下文信息准确回答用户问题。

## 核心原则
1. **准确性优先**：只基于提供的上下文信息回答，不要编造或臆测
2. **引用标注**：在回答中标注信息来源，格式为 [1]、[2] 等
3. **诚实透明**：如果上下文中没有相关信息，明确告知用户
4. **结构清晰**：回答要有条理，适当使用列表和分段

## 回答格式
- 直接回答问题，不要重复问题
- 使用 [数字] 格式标注引用来源
- 如果需要补充说明，放在回答末尾"""


DEFAULT_USER_TEMPLATE = """## 参考信息
{context}

## 问题
{query}

请基于以上参考信息回答问题，并在回答中标注引用来源。"""


SIMPLE_SYSTEM_PROMPT = """你是一个知识库问答助手。请根据提供的上下文准确回答问题，并在回答中标注引用来源 [1]、[2] 等。如果上下文中没有相关信息，请明确说明。"""


SIMPLE_USER_TEMPLATE = """上下文：
{context}

问题：{query}

请回答："""


GRAPH_ENHANCED_SYSTEM_PROMPT = """你是一个专业的知识库问答助手，擅长利用知识图谱进行推理。

## 能力说明
1. 可以理解实体之间的关系
2. 可以进行多跳推理
3. 可以基于证据链得出结论

## 回答原则
1. 充分利用提供的实体和关系信息
2. 在推理过程中展示逻辑链条
3. 标注所有引用来源"""


GRAPH_ENHANCED_USER_TEMPLATE = """## 相关文档
{context}

## 知识图谱信息
{graph_context}

## 问题
{query}

请综合以上信息回答问题，展示推理过程并标注引用来源："""


class QAPromptTemplate:
    DEFAULT = PromptTemplate(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_template=DEFAULT_USER_TEMPLATE
    )
    
    SIMPLE = PromptTemplate(
        system_prompt=SIMPLE_SYSTEM_PROMPT,
        user_template=SIMPLE_USER_TEMPLATE
    )
    
    GRAPH_ENHANCED = PromptTemplate(
        system_prompt=GRAPH_ENHANCED_SYSTEM_PROMPT,
        user_template=GRAPH_ENHANCED_USER_TEMPLATE
    )
    
    def __init__(self, template: PromptTemplate = None):
        self.template = template or self.DEFAULT
    
    def format(
        self,
        query: str,
        context: str,
        graph_context: str = None
    ) -> tuple[str, str]:
        if graph_context and "{graph_context}" in self.template.user_template:
            user_content = self.template.user_template.format(
                context=context,
                query=query,
                graph_context=graph_context
            )
        else:
            user_content = self.template.user_template.format(
                context=context,
                query=query
            )
        
        return self.template.system_prompt, user_content
    
    def format_with_history(
        self,
        query: str,
        context: str,
        history: List[Dict[str, str]],
        graph_context: str = None
    ) -> tuple[str, List[Dict[str, str]]]:
        system_prompt, user_content = self.format(query, context, graph_context)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history[-6:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        messages.append({"role": "user", "content": user_content})
        
        return system_prompt, messages
    
    def set_template(self, template_name: str) -> None:
        templates = {
            "default": self.DEFAULT,
            "simple": self.SIMPLE,
            "graph_enhanced": self.GRAPH_ENHANCED
        }
        
        if template_name in templates:
            self.template = templates[template_name]
        else:
            raise ValueError(f"Unknown template: {template_name}")
    
    def custom_template(
        self,
        system_prompt: str,
        user_template: str
    ) -> None:
        self.template = PromptTemplate(
            system_prompt=system_prompt,
            user_template=user_template
        )


qa_prompt_template = QAPromptTemplate()
