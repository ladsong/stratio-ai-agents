"""Load nanobot skills into LangGraph context."""

from pathlib import Path


class SkillsManager:
    """Manages nanobot skills for backend."""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace = Path(workspace_path)
        self.loader = None
        self._initialize_loader()
    
    def _initialize_loader(self):
        """Initialize nanobot skills loader."""
        try:
            from nanobot.agent.skills import SkillsLoader
            self.loader = SkillsLoader(self.workspace)
        except ImportError:
            # Nanobot not installed yet
            self.loader = None
    
    def list_available_skills(self) -> list[dict]:
        """List all available skills."""
        if not self.loader:
            return []
        return self.loader.list_skills()
    
    def load_skill(self, skill_name: str) -> str:
        """Load a skill's content."""
        if not self.loader:
            return ""
        return self.loader.load_skill(skill_name) or ""
    
    def load_skills_for_context(self, skill_names: list[str]) -> str:
        """Load multiple skills for agent context."""
        if not self.loader:
            return ""
        return self.loader.load_skills_for_context(skill_names)
    
    def get_skill_metadata(self, skill_name: str) -> dict:
        """Get skill metadata."""
        if not self.loader:
            return {}
        try:
            return self.loader._get_skill_meta(skill_name)
        except Exception:
            return {}
