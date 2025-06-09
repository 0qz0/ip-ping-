#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import ping3
from queue import Queue
import logging

@dataclass
class IPStatus:
    ip: str
    is_online: bool
    response_time: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    group: str

class PingMonitor:
    def __init__(self, 
                 timeout: float = 1.0,
                 interval: float = 5.0,
                 failure_threshold: int = 3):
        self.timeout = timeout
        self.interval = interval
        self.failure_threshold = failure_threshold
        self.monitored_ips: Dict[str, IPStatus] = {}
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._status_queue = Queue()
        self._callbacks: List[Callable[[str, IPStatus], None]] = []
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def add_ip(self, ip: str, group: str = "默认") -> None:
        """添加要监控的IP地址"""
        if ip not in self.monitored_ips:
            self.monitored_ips[ip] = IPStatus(
                ip=ip,
                is_online=False,
                response_time=0.0,
                last_success=None,
                last_failure=None,
                consecutive_failures=0,
                group=group
            )
            self.logger.info(f"添加IP地址: {ip} (组: {group})")

    def remove_ip(self, ip: str) -> None:
        """移除监控的IP地址"""
        if ip in self.monitored_ips:
            del self.monitored_ips[ip]
            self.logger.info(f"移除IP地址: {ip}")

    def register_callback(self, callback: Callable[[str, IPStatus], None]) -> None:
        """注册状态更新回调函数"""
        self._callbacks.append(callback)

    def _ping_ip(self, ip: str) -> None:
        """对单个IP执行ping操作"""
        try:
            response_time = ping3.ping(ip, timeout=self.timeout)
            status = self.monitored_ips[ip]
            
            if response_time is not None:
                status.is_online = True
                status.response_time = response_time * 1000  # 转换为毫秒
                status.last_success = datetime.now()
                status.consecutive_failures = 0
            else:
                status.is_online = False
                status.response_time = 0.0
                status.last_failure = datetime.now()
                status.consecutive_failures += 1
                
                if status.consecutive_failures >= self.failure_threshold:
                    self.logger.warning(f"IP {ip} 连续失败 {status.consecutive_failures} 次")
            
            # 通知所有回调
            for callback in self._callbacks:
                callback(ip, status)
                
        except Exception as e:
            self.logger.error(f"Ping {ip} 时发生错误: {str(e)}")

    def _monitor_loop(self) -> None:
        """监控循环"""
        while not self._stop_event.is_set():
            for ip in list(self.monitored_ips.keys()):
                if self._stop_event.is_set():
                    break
                self._ping_ip(ip)
            time.sleep(self.interval)

    def start(self) -> None:
        """启动监控"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_loop)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            self.logger.info("监控已启动")

    def stop(self) -> None:
        """停止监控"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()
            self._monitor_thread = None
        self.logger.info("监控已停止")

    def get_status(self, ip: str) -> Optional[IPStatus]:
        """获取指定IP的状态"""
        return self.monitored_ips.get(ip)

    def get_all_status(self) -> Dict[str, IPStatus]:
        """获取所有IP的状态"""
        return self.monitored_ips.copy() 