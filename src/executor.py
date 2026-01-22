"""
Alyosha Command Executor
Агентное выполнение системных команд с минимальными ограничениями
"""
import subprocess
import shlex
import re


# Only truly destructive commands require confirmation
# Most commands are now allowed without confirmation
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf?\s+(/[^/\s]*){0,2}\s*$',  # rm -rf on root-level dirs only
    r'\bdd\b.*of=/dev/sd',    # Writing to raw disks
    r'\bmkfs\b',              # File system creation
    r'\bfdisk\b',             # Disk partitioning
    r'\bparted\b',            # Disk partitioning
    r'\breboot\b',            # System reboot
    r'\bshutdown\b',          # System shutdown  
    r'\bpoweroff\b',          # System poweroff
    r'\bapt\s+(remove|purge)\b',  # Only remove/purge, not autoremove
]

# Commands that are always blocked (system destruction)
BLOCKED_PATTERNS = [
    r':\(\)\{:\|:&\};:',      # Fork bomb
    r'>\s*/dev/sda\b',        # Direct overwrite of disk
    r'rm\s+-rf?\s+/\s*$',     # rm -rf /
    r'rm\s+-rf?\s+/\*',       # rm -rf /*
    r'mv\s+/\s+',             # mv / somewhere
    r'chmod\s+-R\s+777\s+/',  # Recursive 777 on root
]


import datetime
import config

class CommandExecutor:
    """Агентное выполнение команд с полным контролем системы"""
    
    def __init__(self):
        self.last_command = ""
        self.last_result = ""
        self.pending_command = None
        self.confirmed_commands = set()  # Commands that were previously confirmed
        self.audit_file = config.LOG_DIR / "audit.log"
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _log_audit(self, command: str, success: bool, output: str):
        """Записать команду в аудит"""
        timestamp = datetime.datetime.now().isoformat()
        status = "SUCCESS" if success else "FAILURE"
        
        # Ensure output is string
        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='replace')
        output = str(output)
        
        log_entry = f"[{timestamp}] {status}: {command}\nOutput: {output[:500]}...\n"
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    def is_dangerous(self, command: str) -> bool:
        """Проверка на опасную команду (требует подтверждения)"""
        # Check if this command type was previously confirmed
        cmd_base = command.split()[0] if command.split() else ""
        if cmd_base in self.confirmed_commands:
            return False
            
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
    
    def is_blocked(self, command: str) -> bool:
        """Проверка на заблокированную команду"""
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
    
    def validate(self, command: str) -> tuple[bool, str]:
        """
        Валидация команды
        
        Returns:
            (is_valid, message)
        """
        if not command or not command.strip():
            return True, ""
        
        command = command.strip()
        
        if self.is_blocked(command):
            return False, "Эта команда заблокирована (критически опасна для системы)."
        
        if self.is_dangerous(command):
            self.pending_command = command
            return False, f"⚠️ Опасная команда: {command}\nПодтвердить выполнение?"
        
        return True, ""
    
    def execute(self, command: str, force: bool = False, timeout: int = 300) -> tuple[bool, str]:
        """
        Выполнить команду
        
        Args:
            command: Команда для выполнения
            force: Принудительное выполнение (после подтверждения)
            timeout: Таймаут в секундах (по умолчанию 120)
        
        Returns:
            (success, output)
        """
        if not command or not command.strip():
            return True, ""
        
        command = command.strip()
        
        # Check if blocked
        if self.is_blocked(command):
            return False, "Команда заблокирована (критически опасна)."
        
        # Check if dangerous and not forced
        if self.is_dangerous(command) and not force:
            self.pending_command = command
            return False, "Требуется подтверждение."
        
        try:
            # Check for shell features
            shell_features = ['|', '>', '<', '&', ';', '*', '$', '`', '(', ')']
            use_shell = any(feature in command for feature in shell_features)
            
            if use_shell:
                args = command
            else:
                args = shlex.split(command)
            
            # Execute with extended timeout
            result = subprocess.run(
                args,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/home",
                env=None  # Inherit environment (including PATH for sudo)
            )
            
            if result.returncode == 0:
                self._log_audit(command, True, result.stdout)
                output = result.stdout.strip() if result.stdout else "Команда выполнена успешно."
            else:
                self._log_audit(command, False, result.stderr)
                output = f"Ошибка (код {result.returncode}): {result.stderr.strip()}"
            
            # Strip ANSI escape codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            output = ansi_escape.sub('', output)
            
            return result.returncode == 0, output
                
        except subprocess.TimeoutExpired as e:
            import random
            TIMEOUT_PHRASES = [
                "Я пердолю! Эта команда зависла, как твой мозг в пятницу вечером. Таймаут.",
                "Слишком долго, курва! У меня нет вечности ждать этот 'шедевр'. Отрубаю.",
                "Твой процессор впал в кому от такой наглости. Таймаут.",
                "Она не отвечает. Как и твоя бывшая. Отмена.",
                "Команда выполняется вечность. Я столько не живу. Вырубай шарманку."
            ]
            
            # Extract partial output
            partial_out = ""
            if e.stdout:
                partial_out += e.stdout.decode('utf-8', errors='replace')
            if e.stderr:
                partial_out += e.stderr.decode('utf-8', errors='replace')
            
            result_msg = random.choice(TIMEOUT_PHRASES)
            if partial_out.strip():
                result_msg += f"\n\n(Успел сказать перед смертью):\n{partial_out.strip()[:200]}..."
                
            return False, result_msg
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def confirm_pending(self) -> tuple[bool, str]:
        """Подтвердить и выполнить отложенную команду"""
        if self.pending_command:
            command = self.pending_command
            self.pending_command = None
            return self.execute(command, force=True)
        return False, "Нет команды для подтверждения."
    
    def cancel_pending(self):
        """Отменить отложенную команду"""
        self.pending_command = None
