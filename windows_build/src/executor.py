"""
Alyosha Command Executor (Windows)
Агентное выполнение команд с контролем безопасности
"""
import subprocess
import shlex
import re
import os
import datetime
import logging
import config

logger = logging.getLogger(__name__)

# Windows dangerous patterns
DANGEROUS_PATTERNS = [
    r'\bdel\b\s+/s',          # Recursive delete
    r'\brmdir\b\s+/s',        # Recursive remove dir
    r'\brd\b\s+/s',           # Recursive remove dir shorthand
    r'\bformat\b',            # Format disk
    r'\bwinget\b\s+uninstall',# Uninstall software
    r'\bshutdown\b',          # Shutdown
    r'\btaskkill\b',          # Kill process
]

# Blocked patterns (system destruction)
BLOCKED_PATTERNS = [
    r'\bformat\b\s+c:',       # Format C:
    r'\bdel\b\s+c:\\windows', # Delete Windows
    r'\brd\b\s+/s\s+/q\s+c:\\', # Silent recursive remove C:
]

class CommandExecutor:
    """Агентное выполнение команд (Windows)"""
    
    def __init__(self):
        self.last_command = ""
        self.last_result = ""
        self.pending_command = None
        self.confirmed_commands = set()
        self.audit_file = config.LOG_DIR / "audit.log"
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _log_audit(self, command: str, success: bool, output: str):
        """Записать команду в аудит"""
        timestamp = datetime.datetime.now().isoformat()
        status = "SUCCESS" if success else "FAILURE"
        
        if isinstance(output, bytes):
            output = output.decode('cp866', errors='replace') # Windows CMD uses cp866/cp1251
        output = str(output)
        
        log_entry = f"[{timestamp}] {status}: {command}\nOutput: {output[:500]}...\n"
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    def is_dangerous(self, command: str) -> bool:
        cmd_base = command.split()[0] if command.split() else ""
        if cmd_base in self.confirmed_commands:
            return False
            
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
    
    def is_blocked(self, command: str) -> bool:
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
    
    def validate(self, command: str) -> tuple[bool, str]:
        if not command or not command.strip():
            return True, ""
        
        command = command.strip()
        
        if self.is_blocked(command):
            return False, "Эта команда заблокирована (критически опасна)."
        
        if self.is_dangerous(command):
            self.pending_command = command
            return False, f"⚠️ Опасная команда: {command}\nПодтвердить выполнение?"
        
        return True, ""
    
    def execute(self, command: str, force: bool = False, timeout: int = 120) -> tuple[bool, str]:
        if not command or not command.strip():
            return True, ""
        
        command = command.strip()
        
        if self.is_blocked(command):
            return False, "Команда заблокирована."
        
        if self.is_dangerous(command) and not force:
            self.pending_command = command
            return False, "Требуется подтверждение."
        
        try:
            # On Windows, simple commands often need shell
            use_shell = True
            
            # Windows cwd
            cwd = os.path.expanduser("~")
            
            result = subprocess.run(
                command,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                encoding='cp866', # Or 'mbcs' or 'utf-8' depending on system
                errors='replace'
            )
            
            if result.returncode == 0:
                self._log_audit(command, True, result.stdout)
                output = result.stdout.strip() if result.stdout else "Команда выполнена успешно."
            else:
                self._log_audit(command, False, result.stderr)
                output = f"Ошибка (код {result.returncode}): {result.stderr.strip()}"
            
            return result.returncode == 0, output
                
        except subprocess.TimeoutExpired:
            return False, "Таймаут выполнения команды."
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def confirm_pending(self) -> tuple[bool, str]:
        if self.pending_command:
            command = self.pending_command
            self.pending_command = None
            return self.execute(command, force=True)
        return False, "Нет команды для подтверждения."
    
    def cancel_pending(self):
        self.pending_command = None
