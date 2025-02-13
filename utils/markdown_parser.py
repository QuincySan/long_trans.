"""
This module provides utilities for parsing and formatting Markdown text.
"""
from typing import List, Dict, Any
from markdown_it import MarkdownIt

class MarkdownParser:
    def __init__(self):
        """Initialize the Markdown parser."""
        self.md = MarkdownIt()

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse Markdown text into a structured format.
        
        Args:
            text: Input text in Markdown format
            
        Returns:
            List of dictionaries containing parsed tokens
        """
        return self.md.parse(text)

    def render(self, tokens: List[Dict[str, Any]]) -> str:
        """
        Render parsed tokens back to Markdown text.
        
        Args:
            tokens: List of parsed Markdown tokens
            
        Returns:
            Rendered Markdown text
        """
        return self.md.renderer.render(tokens, self.md.options, {})

    def get_headers(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all headers from Markdown text with their levels.
        
        Args:
            text: Input text in Markdown format
            
        Returns:
            List of dictionaries containing header information
        """
        tokens = self.parse(text)
        headers = []
        
        for token in tokens:
            if token.type == 'heading_open':
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
                content = tokens[tokens.index(token) + 1].content
                headers.append({
                    'level': level,
                    'content': content,
                    'position': tokens.index(token)
                })
        
        return headers

    def get_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Extract all code blocks from Markdown text.
        
        Args:
            text: Input text in Markdown format
            
        Returns:
            List of dictionaries containing code block information
        """
        tokens = self.parse(text)
        code_blocks = []
        
        for token in tokens:
            if token.type == 'fence':
                code_blocks.append({
                    'language': token.info,
                    'content': token.content
                })
        
        return code_blocks 