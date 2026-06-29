import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO


class TestSetupLogger:

    def test_setup_logger_returns_logger_instance(self):
        """测试 setup_logger 返回 logger 实例"""
        # 重新导入以避免之前已初始化
        with patch.dict(sys.modules, {"app.core.config": MagicMock()}):
            with patch("app.core.logger.logger") as mock_logger:
                mock_logger.remove.return_value = None
                mock_logger.add.return_value = None

                # 动态导入
                from importlib import reload
                import app.core.logger as logger_module
                reload(logger_module)

                # 验证 logger.add 被调用了两次（stdout 和 file）
                assert mock_logger.add.call_count == 2

    def test_setup_logger_removes_existing_handlers(self):
        """测试 setup_logger 移除已有的 handlers"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            setup_logger()

            mock_logger.remove.assert_called_once()

    def test_setup_logger_adds_stdout_handler(self):
        """测试 setup_logger 添加 stdout handler"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            setup_logger()

            # 验证 stdout handler
            calls = mock_logger.add.call_args_list
            stdout_call = calls[0]
            assert stdout_call.kwargs.get("sink") == sys.stdout or stdout_call.args[0] == sys.stdout

    def test_setup_logger_adds_file_handler(self):
        """测试 setup_logger 添加文件 handler"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            setup_logger()

            # 验证 file handler
            calls = mock_logger.add.call_args_list
            file_call = calls[1]
            assert file_call.kwargs.get("sink") == "logs/app.log" or file_call.args[0] == "logs/app.log"

    def test_setup_logger_with_debug_level(self):
        """测试 setup_logger 使用 DEBUG 级别"""
        with patch("app.core.logger.logger") as mock_logger:
            with patch("app.core.logger.settings") as mock_settings:
                mock_settings.LOG_LEVEL = "DEBUG"
                mock_logger.remove.return_value = None
                mock_logger.add.return_value = None

                from app.core.logger import setup_logger
                setup_logger()

                # 验证所有 handler 都使用了 DEBUG 级别
                for call in mock_logger.add.call_args_list:
                    kwargs = call.kwargs
                    if "level" in kwargs:
                        assert kwargs["level"] == "DEBUG"

    def test_setup_logger_with_error_level(self):
        """测试 setup_logger 使用 ERROR 级别"""
        with patch("app.core.logger.logger") as mock_logger:
            with patch("app.core.logger.settings") as mock_settings:
                mock_settings.LOG_LEVEL = "ERROR"
                mock_logger.remove.return_value = None
                mock_logger.add.return_value = None

                from app.core.logger import setup_logger
                setup_logger()

                for call in mock_logger.add.call_args_list:
                    kwargs = call.kwargs
                    if "level" in kwargs:
                        assert kwargs["level"] == "ERROR"

    def test_setup_logger_file_rotation_config(self):
        """测试 setup_logger 文件 handler 的 rotation 配置"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            setup_logger()

            # 验证 file handler 的 rotation 和 retention 配置
            file_call = mock_logger.add.call_args_list[1]
            kwargs = file_call.kwargs
            assert kwargs.get("rotation") == "10 MB"
            assert kwargs.get("retention") == "7 days"

    def test_setup_logger_stdout_format(self):
        """测试 setup_logger stdout handler 的 format 配置"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            setup_logger()

            # 验证 stdout handler 的 format
            stdout_call = mock_logger.add.call_args_list[0]
            kwargs = stdout_call.kwargs
            expected_format = "<green>{time}</green> | <level>{level}</level> | {message}"
            assert kwargs.get("format") == expected_format

    def test_setup_logger_returns_logger(self):
        """测试 setup_logger 返回 logger 对象"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            result = setup_logger()

            assert result == mock_logger

    def test_setup_logger_multiple_calls(self):
        """测试多次调用 setup_logger"""
        with patch("app.core.logger.logger") as mock_logger:
            mock_logger.remove.return_value = None
            mock_logger.add.return_value = None

            from app.core.logger import setup_logger
            setup_logger()
            setup_logger()

            # 每次调用都会 remove 一次
            assert mock_logger.remove.call_count == 2
            # 每次调用会添加两个 handler
            assert mock_logger.add.call_count == 4