from .base_agent import BaseAgent
class LineEditorAgent(BaseAgent):
    def get_prompt(self): return "Line Editor - Placeholder"
    def process(self, data): return data
