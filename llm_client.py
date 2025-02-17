"""
该模块提供了与大语言模型(LLM)交互的客户端实现。
支持不同的LLM提供商和模型，便于后续扩展和切换。
"""
import os
from typing import List, Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class LLMClient:
    """LLM客户端基类，定义通用接口"""
    
    def generate_text(self, prompt: str) -> str:
        """
        生成文本的抽象方法
        
        参数:
            prompt: 输入提示词
            
        返回:
            生成的文本
        """
        raise NotImplementedError

class FireworksClient(LLMClient):
    """Fireworks.ai API客户端实现"""
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化Fireworks客户端
        
        参数:
            api_key: API密钥，如果未提供则从环境变量获取
            api_base: API基础URL，如果未提供则使用默认值
        """
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        self.api_base = api_base or os.getenv("FIREWORKS_API_BASE", "https://api.fireworks.ai/inference/v1")
        
        if not self.api_key:
            raise ValueError("必须提供API密钥，可以直接传入或通过环境变量FIREWORKS_API_KEY设置")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        
    def generate_text(
        self, 
        prompt: str,
        model: str = "accounts/fireworks/models/deepseek-r1",
        temperature: float = 0.6,
        system_prompt: str = "",
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        使用Fireworks API生成文本
        
        参数:
            prompt: 输入提示词
            model: 使用的模型名称
            temperature: 温度参数，控制输出的随机性
            system_prompt: 系统提示词
            response_format: 响应格式设置
            
        返回:
            生成的文本
        """
        completion = self.client.chat.completions.create(
            model=model,
            stream=False,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format=response_format
        )
        
        return completion.choices[0].message.content

class ZetaClient(LLMClient):
    """Zeta API客户端实现"""
    
    # 添加模型配置映射
    SUPPORTED_MODELS = {
        "claude-3-5-sonnet-20241022": {
            "max_tokens": 4096,
            "default_temp": 0.6,
        },
        "deepseek-v3": {
            "max_tokens": 4096,
            "default_temp": 0.7,
        },
        "gemini-2.0-pro-exp-02-05": {
            "max_tokens": 4096,
            "default_temp": 0.7,
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化Zeta客户端
        
        参数:
            api_key: API密钥，如果未提供则从环境变量获取
            api_base: API基础URL，如果未提供则使用默认值
        """
        self.api_key = api_key or os.getenv("ZETA_API_KEY")
        self.api_base = api_base or os.getenv("ZETA_API_BASE", "https://api.zetatechs.com/v1")
        
        if not self.api_key:
            raise ValueError("必须提供API密钥，可以直接传入或通过环境变量ZETA_API_KEY设置")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        
    def generate_text(
        self, 
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: Optional[float] = None,
        system_prompt: str = "",
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        使用Zeta API生成文本
        
        参数:
            prompt: 输入提示词
            model: 使用的模型名称
            temperature: 温度参数，控制输出的随机性。如果未指定，使用模型默认值
            system_prompt: 系统提示词
            response_format: 响应格式设置
            
        返回:
            生成的文本
        """
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {model}。支持的模型包括: {', '.join(self.SUPPORTED_MODELS.keys())}")
            
        config = self.SUPPORTED_MODELS[model]
        temp = temperature if temperature is not None else config["default_temp"]
        
        completion = self.client.chat.completions.create(
            model=model,
            stream=False,
            temperature=temp,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format=response_format,
            max_tokens=config["max_tokens"]
        )
        
        return completion.choices[0].message.content

# 后续可以添加其他LLM提供商的实现，如OpenAI、Claude等 