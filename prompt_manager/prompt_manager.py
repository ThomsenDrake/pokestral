import json
from typing import List, Dict, Any

class PromptManager:
    def __init__(self):
        self.action_history = []
        self.summarized_history = []
        self.current_location = None
        self.party_summary = None
        self.items = None
        self.money = 0
        self.badges = []
        self.goals = []
        self.recent_actions = []

    def update_state(self, current_location: str, party_summary: Dict[str, Any],
                    items: Dict[str, int], money: int, badges: List[str],
                    goals: List[str]):
        """Update the game state information."""
        self.current_location = current_location
        self.party_summary = party_summary
        self.items = items
        self.money = money
        self.badges = badges
        self.goals = goals

    def add_action(self, action: str, reason: str):
        """Add a new action to the history."""
        self.action_history.append({"action": action, "reason": reason})
        self.recent_actions.append({"action": action, "reason": reason})

        # Keep only the last 10 actions for recent actions
        if len(self.recent_actions) > 10:
            self.recent_actions.pop(0)

        # Summarize every 100 actions
        if len(self.action_history) % 100 == 0:
            self._summarize_actions()

        # Compress every 1000 actions
        if len(self.action_history) % 1000 == 0:
            self._compress_history()

    def _summarize_actions(self):
        """Summarize the last 100 actions."""
        if len(self.action_history) >= 100:
            last_100 = self.action_history[-100:]
            summary = self._create_summary(last_100)
            self.summarized_history.append(summary)
            # Keep action history manageable
            self.action_history = self.action_history[-100:]

    def _compress_history(self):
        """Compress the summarized history."""
        if len(self.summarized_history) >= 10:
            # Simple compression: keep only the most recent summaries
            self.summarized_history = self.summarized_history[-10:]

    def _create_summary(self, actions: List[Dict[str, str]]) -> str:
        """Create a summary from a list of actions."""
        # Simple summary: count actions by type
        action_counts = {}
        for action in actions:
            act = action['action']
            action_counts[act] = action_counts.get(act, 0) + 1

        summary_parts = [f"{count} x {action}" for action, count in action_counts.items()]
        return ", ".join(summary_parts)

    def construct_prompt(self) -> str:
        """Construct the prompt for the AI agent."""
        # Build the prompt components
        prompt_parts = []

        # Add current state information
        prompt_parts.append(f"Current Location: {self.current_location}")
        prompt_parts.append(f"Party: {json.dumps(self.party_summary)}")
        prompt_parts.append(f"Items: {json.dumps(self.items)}")
        prompt_parts.append(f"Money: {self.money}")
        prompt_parts.append(f"Badges: {json.dumps(self.badges)}")
        prompt_parts.append(f"Goals: {json.dumps(self.goals)}")

        # Add recent actions
        prompt_parts.append("Recent Actions:")
        for action in self.recent_actions[-5:]:  # Show last 5 actions
            prompt_parts.append(f"- {action['action']}: {action['reason']}")

        # Add summarized history
        if self.summarized_history:
            prompt_parts.append("History Summary:")
            for i, summary in enumerate(self.summarized_history[-3:], 1):  # Show last 3 summaries
                prompt_parts.append(f"{i}. {summary}")

        # Add instructions for output format
        prompt_parts.append("\nInstructions for Mistral:")
        prompt_parts.append("Please output your response in JSON format with fields 'action' and 'reason'")
        prompt_parts.append("Example: {'action': 'move_north', 'reason': 'To reach the next town'}")

        # Add tool invocation support
        prompt_parts.append("\nTool Invocation:")
        prompt_parts.append("If you need to use a tool, format your action as 'tool_name:parameters'")
        prompt_parts.append("Example: 'use_item:potion' to use a potion item")

        # Join all parts with newlines
        prompt = "\n".join(prompt_parts)

        # Ensure prompt is under 10k tokens (rough estimate: 1 token ≈ 4 chars)
        max_length = 40000  # 10k tokens * 4 chars per token
        if len(prompt) > max_length:
            # Truncate from the history summary if needed
            while len(prompt) > max_length and len(self.summarized_history) > 1:
                self.summarized_history.pop(0)
                prompt = self.construct_prompt()

        return prompt

    def detect_tool_invocation(self, action: str) -> Dict[str, str]:
        """Detect if an action is a tool invocation."""
        if ':' in action:
            tool_name, params = action.split(':', 1)
            return {"tool": tool_name, "parameters": params}
        return {"tool": None, "parameters": None}