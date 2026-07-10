import re

try:
    from prompt_toolkit.completion import WordCompleter, Completer, Completion
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

if HAS_PROMPT_TOOLKIT:
    # Pattern to match slash commands as a single word in prompt-toolkit
    _PATTERN_CMD = re.compile(r'/[a-zA-Z0-9_-]*')

    class CommandCompleter(WordCompleter):
        """Custom WordCompleter that triggers only when the word before cursor starts with a slash '/'."""
        def get_completions(self, document, complete_event):
            word_before_cursor = ""
            if self.pattern:
                matches = list(self.pattern.finditer(document.text_before_cursor))
                if matches:
                    match = matches[-1]
                    if match.end() == len(document.text_before_cursor):
                        word_before_cursor = match.group()
            
            if not word_before_cursor.startswith('/'):
                return
                
            yield from super().get_completions(document, complete_event)

    class AntCompleter(Completer):
        """Unified completer for slash commands, at-sign file suggestions, and colon subagent suggestions."""
        def __init__(self, command_suggestions: list[str], file_suggestions: list[str], subagent_suggestions: list[str] = None):
            self.command_suggestions = command_suggestions
            self.file_suggestions = file_suggestions
            self.subagent_suggestions = subagent_suggestions or []
            self._pattern_cmd = re.compile(r'/[a-zA-Z0-9_-]*')
            self._pattern_file = re.compile(r'@[a-zA-Z0-9_\-\./\\]*')
            self._pattern_subagent = re.compile(r':[a-zA-Z0-9_-]*')

        def get_completions(self, document, complete_event):
            text_before = document.text_before_cursor

            # 1. Command completion (starts with /)
            cmd_matches = list(self._pattern_cmd.finditer(text_before))
            if cmd_matches and cmd_matches[-1].end() == len(text_before):
                match = cmd_matches[-1]
                word = match.group()
                for suggestion in self.command_suggestions:
                    if suggestion.lower().startswith(word.lower()):
                        yield Completion(suggestion, start_position=-len(word))
                return

            # 2. File and folder completion (starts with @)
            file_matches = list(self._pattern_file.finditer(text_before))
            if file_matches and file_matches[-1].end() == len(text_before):
                match = file_matches[-1]
                word = match.group()
                prefix = word[1:] # strip the '@'
                prefix_lower = prefix.lower()
                # Yield prefix matches first
                for suggestion in self.file_suggestions:
                    if suggestion.lower().startswith(prefix_lower):
                        yield Completion(f"@{suggestion}", start_position=-len(word))
                # Yield substring/middle matches next
                for suggestion in self.file_suggestions:
                    if prefix_lower in suggestion.lower() and not suggestion.lower().startswith(prefix_lower):
                        yield Completion(f"@{suggestion}", start_position=-len(word))
                return

            # 3. Subagent completion (starts with :)
            subagent_matches = list(self._pattern_subagent.finditer(text_before))
            if subagent_matches and subagent_matches[-1].end() == len(text_before):
                match = subagent_matches[-1]
                word = match.group()
                prefix = word[1:] # strip the ':'
                prefix_lower = prefix.lower()
                # Yield prefix matches first
                for suggestion in self.subagent_suggestions:
                    if suggestion.lower().startswith(prefix_lower):
                        yield Completion(f":{suggestion}", start_position=-len(word))
                # Yield substring/middle matches next
                for suggestion in self.subagent_suggestions:
                    if prefix_lower in suggestion.lower() and not suggestion.lower().startswith(prefix_lower):
                        yield Completion(f":{suggestion}", start_position=-len(word))
                return
else:
    _PATTERN_CMD = None
    class CommandCompleter:
        pass
    class AntCompleter:
        def __init__(self, **kwargs):
            pass
