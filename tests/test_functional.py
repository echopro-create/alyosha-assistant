
import unittest
import sys
import os

from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from src.tools_def import execute_bash
from src.assistant import Assistant, AssistantState

class TestAlyoshaFunctional(unittest.TestCase):
    
    def test_execute_bash_success(self):
        """Test successful bash execution"""
        result = execute_bash("echo 'Hello Alyosha'")
        self.assertIn("Success", result)
        self.assertIn("Hello Alyosha", result)

    def test_execute_bash_error(self):
        """Test failing bash execution"""
        result = execute_bash("ls /nonexistent/file/path")
        self.assertIn("Error", result)
        self.assertIn("Exit code", result)
        
    def test_execute_bash_complex(self):
        """Test complex piped command"""
        result = execute_bash("echo 'test' | grep 'test'")
        self.assertIn("test", result)
        
    @patch('src.audio.StreamPlayer')
    @patch('src.live_client.GeminiLiveClient')
    def test_assistant_live_mode_state(self, MockLiveClient, MockPlayer):
        """Test Assistant state transitions for Live Mode"""
        # Mock QApplication requirement
        app = MagicMock()
        with patch('PyQt6.QtWidgets.QApplication.instance', return_value=app):
            assistant = Assistant()
            
            # Initial state
            self.assertEqual(assistant.state, AssistantState.IDLE)
            
            # Start Live
            assistant.start_live_session()
            self.assertEqual(assistant.state, AssistantState.REALTIME_SESSION)
            
            # Stop Live
            assistant.stop_live_session()
            self.assertEqual(assistant.state, AssistantState.IDLE)

if __name__ == '__main__':
    unittest.main()
