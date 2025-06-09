#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QMessageBox,
    QDialog, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QAction
import yaml
import json
import logging
from pathlib import Path

class AlertHistoryDialog(QDialog):
    def __init__(self, alert_manager, parent=None):
        super().__init__(parent)
        self.alert_manager = alert_manager
        self.setWindowTitle("报警历史记录")
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()
        
        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_history)
        toolbar.addWidget(export_btn)
        
        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_history)
        toolbar.addWidget(clear_btn)
        
        layout.addLayout(toolbar)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels([
            "时间", "IP地址", "报警信息", "类型"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.history_table)

        self.setLayout(layout)
        self.resize(800, 600)

    def load_history(self):
        self.history_table.setRowCount(0)
        for alert in self.alert_manager.get_alert_history():
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # 时间
            timestamp = datetime.fromisoformat(alert["timestamp"])
            self.history_table.setItem(row, 0, QTableWidgetItem(
                timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            # IP地址
            self.history_table.setItem(row, 1, QTableWidgetItem(alert["ip"]))
            
            # 报警信息
            self.history_table.setItem(row, 2, QTableWidgetItem(alert["message"]))
            
            # 类型
            type_item = QTableWidgetItem(alert["type"])
            type_item.setForeground(
                QColor("#F44336" if alert["type"] == "error" else "#FFC107")
            )
            self.history_table.setItem(row, 3, type_item)

    def export_history(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出报警历史",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if filepath:
            try:
                self.alert_manager.save_alert_history(filepath)
                QMessageBox.information(self, "成功", "报警历史导出成功")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"导出报警历史失败: {str(e)}")

    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清除所有报警历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.alert_manager.clear_alert_history()
            self.load_history()

class SystemLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志")
        self.setup_ui()
        self.load_logs()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 工具栏
        toolbar = QHBoxLayout()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_logs)
        toolbar.addWidget(refresh_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_logs)
        toolbar.addWidget(export_btn)
        
        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_logs)
        toolbar.addWidget(clear_btn)
        
        layout.addLayout(toolbar)

        # 日志表格
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels([
            "时间", "级别", "消息"
        ])
        self.log_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.log_table)

        self.setLayout(layout)
        self.resize(800, 600)

    def load_logs(self):
        self.log_table.setRowCount(0)
        try:
            with open("logs/ping_monitor.log", "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # 解析日志行
                        parts = line.strip().split(" - ")
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            level = parts[1]
                            message = " - ".join(parts[2:])
                            
                            row = self.log_table.rowCount()
                            self.log_table.insertRow(row)
                            
                            # 时间
                            self.log_table.setItem(row, 0, QTableWidgetItem(timestamp))
                            
                            # 级别
                            level_item = QTableWidgetItem(level)
                            if level == "ERROR":
                                level_item.setForeground(QColor("#F44336"))
                            elif level == "WARNING":
                                level_item.setForeground(QColor("#FFC107"))
                            elif level == "INFO":
                                level_item.setForeground(QColor("#4CAF50"))
                            self.log_table.setItem(row, 1, level_item)
                            
                            # 消息
                            self.log_table.setItem(row, 2, QTableWidgetItem(message))
                    except Exception as e:
                        print(f"解析日志行失败: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载日志失败: {str(e)}")

    def export_logs(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出系统日志",
            "",
            "日志文件 (*.log);;所有文件 (*.*)"
        )
        
        if filepath:
            try:
                with open("logs/ping_monitor.log", "r", encoding="utf-8") as src:
                    with open(filepath, "w", encoding="utf-8") as dst:
                        dst.write(src.read())
                QMessageBox.information(self, "成功", "系统日志导出成功")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"导出系统日志失败: {str(e)}")

    def clear_logs(self):
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清除所有系统日志吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open("logs/ping_monitor.log", "w", encoding="utf-8") as f:
                    f.write("")
                self.load_logs()
                QMessageBox.information(self, "成功", "系统日志已清除")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"清除系统日志失败: {str(e)}")

class AdminWindow(QMainWindow):
    def __init__(self, monitor, alert_manager):
        super().__init__()
        self.monitor = monitor
        self.alert_manager = alert_manager
        self.setWindowTitle("IP监控工具 - 管理界面")
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 标签页
        tab_widget = QTabWidget()
        
        # 系统状态标签页
        status_tab = QWidget()
        status_layout = QVBoxLayout()
        
        # 监控状态
        monitor_group = QWidget()
        monitor_layout = QVBoxLayout()
        
        self.status_label = QLabel("监控状态: 未启动")
        monitor_layout.addWidget(self.status_label)
        
        self.start_btn = QPushButton("启动监控")
        self.start_btn.clicked.connect(self.start_monitor)
        monitor_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止监控")
        self.stop_btn.clicked.connect(self.stop_monitor)
        self.stop_btn.setEnabled(False)
        monitor_layout.addWidget(self.stop_btn)
        
        monitor_group.setLayout(monitor_layout)
        status_layout.addWidget(monitor_group)
        
        # 统计信息
        stats_group = QWidget()
        stats_layout = QVBoxLayout()
        
        self.total_ips_label = QLabel("监控IP总数: 0")
        stats_layout.addWidget(self.total_ips_label)
        
        self.online_ips_label = QLabel("在线IP数: 0")
        stats_layout.addWidget(self.online_ips_label)
        
        self.offline_ips_label = QLabel("离线IP数: 0")
        stats_layout.addWidget(self.offline_ips_label)
        
        self.alert_count_label = QLabel("今日报警次数: 0")
        stats_layout.addWidget(self.alert_count_label)
        
        stats_group.setLayout(stats_layout)
        status_layout.addWidget(stats_group)
        
        status_tab.setLayout(status_layout)
        tab_widget.addTab(status_tab, "系统状态")
        
        # 报警历史标签页
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        history_btn = QPushButton("查看报警历史")
        history_btn.clicked.connect(self.show_alert_history)
        history_layout.addWidget(history_btn)
        
        history_tab.setLayout(history_layout)
        tab_widget.addTab(history_tab, "报警历史")
        
        # 系统日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        
        log_btn = QPushButton("查看系统日志")
        log_btn.clicked.connect(self.show_system_log)
        log_layout.addWidget(log_btn)
        
        log_tab.setLayout(log_layout)
        tab_widget.addTab(log_tab, "系统日志")
        
        # 配置管理标签页
        config_tab = QWidget()
        config_layout = QVBoxLayout()
        
        # 备份配置
        backup_btn = QPushButton("备份配置")
        backup_btn.clicked.connect(self.backup_config)
        config_layout.addWidget(backup_btn)
        
        # 恢复配置
        restore_btn = QPushButton("恢复配置")
        restore_btn.clicked.connect(self.restore_config)
        config_layout.addWidget(restore_btn)
        
        config_tab.setLayout(config_layout)
        tab_widget.addTab(config_tab, "配置管理")
        
        layout.addWidget(tab_widget)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

        # 设置窗口大小
        self.resize(600, 400)

        # 启动定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(1000)  # 每秒刷新一次

    def load_config(self):
        try:
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置文件失败: {str(e)}")

    def start_monitor(self):
        try:
            self.monitor.start()
            self.status_label.setText("监控状态: 运行中")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.statusBar.showMessage("监控已启动")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"启动监控失败: {str(e)}")

    def stop_monitor(self):
        try:
            self.monitor.stop()
            self.status_label.setText("监控状态: 已停止")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.statusBar.showMessage("监控已停止")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"停止监控失败: {str(e)}")

    def refresh_status(self):
        # 更新统计信息
        all_status = self.monitor.get_all_status()
        total = len(all_status)
        online = sum(1 for status in all_status.values() if status.is_online)
        
        self.total_ips_label.setText(f"监控IP总数: {total}")
        self.online_ips_label.setText(f"在线IP数: {online}")
        self.offline_ips_label.setText(f"离线IP数: {total - online}")
        
        # 更新今日报警次数
        today = datetime.now().date()
        today_alerts = sum(
            1 for alert in self.alert_manager.get_alert_history()
            if datetime.fromisoformat(alert["timestamp"]).date() == today
        )
        self.alert_count_label.setText(f"今日报警次数: {today_alerts}")

    def show_alert_history(self):
        dialog = AlertHistoryDialog(self.alert_manager, self)
        dialog.exec()

    def show_system_log(self):
        dialog = SystemLogDialog(self)
        dialog.exec()

    def backup_config(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "备份配置",
            "",
            "YAML文件 (*.yaml);;所有文件 (*.*)"
        )
        
        if filepath:
            try:
                # 备份配置文件
                with open("config/config.yaml", "r", encoding="utf-8") as src:
                    with open(filepath, "w", encoding="utf-8") as dst:
                        dst.write(src.read())
                
                # 备份IP列表
                ip_list_path = Path(filepath).with_suffix(".txt")
                with open(ip_list_path, "w", encoding="utf-8") as f:
                    for ip, status in self.monitor.get_all_status().items():
                        f.write(f"{ip} # {status.group}\n")
                
                QMessageBox.information(
                    self,
                    "成功",
                    f"配置已备份到:\n{filepath}\n{ip_list_path}"
                )
            except Exception as e:
                QMessageBox.warning(self, "警告", f"备份配置失败: {str(e)}")

    def restore_config(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "恢复配置",
            "",
            "YAML文件 (*.yaml);;所有文件 (*.*)"
        )
        
        if filepath:
            reply = QMessageBox.question(
                self,
                "确认",
                "恢复配置将覆盖当前设置，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # 恢复配置文件
                    with open(filepath, "r", encoding="utf-8") as src:
                        with open("config/config.yaml", "w", encoding="utf-8") as dst:
                            dst.write(src.read())
                    
                    # 恢复IP列表
                    ip_list_path = Path(filepath).with_suffix(".txt")
                    if ip_list_path.exists():
                        self.monitor.monitored_ips.clear()
                        with open(ip_list_path, "r", encoding="utf-8") as f:
                            for line in f:
                                ip = line.strip().split("#")[0].strip()
                                if ip:
                                    self.monitor.add_ip(ip)
                    
                    # 重新加载配置
                    self.load_config()
                    
                    QMessageBox.information(self, "成功", "配置已恢复")
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"恢复配置失败: {str(e)}")

    def closeEvent(self, event):
        """关闭窗口时停止监控"""
        if self.monitor._monitor_thread and self.monitor._monitor_thread.is_alive():
            reply = QMessageBox.question(
                self,
                "确认",
                "监控正在运行，确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.monitor.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 