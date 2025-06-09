#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QComboBox, QMessageBox,
    QFileDialog, QMenu, QStatusBar, QDialog,
    QSpinBox, QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QAction, QIcon
import yaml

from core.ping_monitor import PingMonitor, IPStatus
from core.alert_manager import AlertManager, AlertConfig
from gui.admin_window import AdminWindow

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Ping设置
        ping_group = QWidget()
        ping_layout = QVBoxLayout()
        
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("超时时间(秒):"))
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 10.0)
        self.timeout_spin.setSingleStep(0.1)
        timeout_layout.addWidget(self.timeout_spin)
        ping_layout.addLayout(timeout_layout)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("检测间隔(秒):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(1.0, 300.0)
        self.interval_spin.setSingleStep(1.0)
        interval_layout.addWidget(self.interval_spin)
        ping_layout.addLayout(interval_layout)

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("失败阈值:"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 10)
        threshold_layout.addWidget(self.threshold_spin)
        ping_layout.addLayout(threshold_layout)

        ping_group.setLayout(ping_layout)
        layout.addWidget(QLabel("Ping设置"))
        layout.addWidget(ping_group)

        # 报警设置
        alert_group = QWidget()
        alert_layout = QVBoxLayout()

        self.desktop_notify = QCheckBox("启用桌面通知")
        alert_layout.addWidget(self.desktop_notify)

        self.sound_alert = QCheckBox("启用声音报警")
        alert_layout.addWidget(self.sound_alert)

        email_group = QWidget()
        email_layout = QVBoxLayout()
        self.email_enabled = QCheckBox("启用邮件报警")
        email_layout.addWidget(self.email_enabled)

        smtp_layout = QHBoxLayout()
        smtp_layout.addWidget(QLabel("SMTP服务器:"))
        self.smtp_server = QLineEdit()
        smtp_layout.addWidget(self.smtp_server)
        email_layout.addLayout(smtp_layout)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("SMTP端口:"))
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        port_layout.addWidget(self.smtp_port)
        email_layout.addLayout(port_layout)

        email_group.setLayout(email_layout)
        alert_layout.addWidget(email_group)

        alert_group.setLayout(alert_layout)
        layout.addWidget(QLabel("报警设置"))
        layout.addWidget(alert_group)

        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_settings(self):
        try:
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
            self.timeout_spin.setValue(config["ping"]["timeout"])
            self.interval_spin.setValue(config["ping"]["interval"])
            self.threshold_spin.setValue(config["ping"]["failure_threshold"])
            
            self.desktop_notify.setChecked(config["alert"]["desktop_notification"])
            self.sound_alert.setChecked(config["alert"]["sound_alert"])
            self.email_enabled.setChecked(config["alert"]["email"]["enabled"])
            self.smtp_server.setText(config["alert"]["email"]["smtp_server"])
            self.smtp_port.setValue(config["alert"]["email"]["smtp_port"])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败: {str(e)}")

    def get_settings(self) -> dict:
        return {
            "ping": {
                "timeout": self.timeout_spin.value(),
                "interval": self.interval_spin.value(),
                "failure_threshold": self.threshold_spin.value()
            },
            "alert": {
                "desktop_notification": self.desktop_notify.isChecked(),
                "sound_alert": self.sound_alert.isChecked(),
                "email": {
                    "enabled": self.email_enabled.isChecked(),
                    "smtp_server": self.smtp_server.text(),
                    "smtp_port": self.smtp_port.value()
                }
            }
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP Ping 监控工具")
        self.setup_ui()
        self.setup_monitor()
        self.load_config()
        self.setup_menu()
        
        # 启动定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(1000)  # 每秒刷新一次

    def setup_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 工具栏
        toolbar = QHBoxLayout()
        
        # IP输入
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("输入IP地址")
        toolbar.addWidget(self.ip_input)
        
        # 分组选择
        self.group_combo = QComboBox()
        self.group_combo.addItem("默认")
        self.group_combo.setEditable(True)
        toolbar.addWidget(self.group_combo)
        
        # 添加按钮
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_ip)
        toolbar.addWidget(add_btn)
        
        # 导入按钮
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_ips)
        toolbar.addWidget(import_btn)
        
        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_btn)
        
        layout.addLayout(toolbar)

        # 状态表格
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(6)
        self.status_table.setHorizontalHeaderLabels([
            "IP地址", "状态", "响应时间(ms)", "最后成功时间",
            "最后失败时间", "连续失败次数"
        ])
        self.status_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.status_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.status_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.status_table)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")

    def setup_monitor(self):
        self.monitor = PingMonitor()
        self.monitor.register_callback(self.on_status_update)
        
        self.alert_manager = AlertManager()
        
        # 创建必要的目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

    def setup_menu(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入IP列表", self)
        import_action.triggered.connect(self.import_ips)
        file_menu.addAction(import_action)
        
        export_action = QAction("导出IP列表", self)
        export_action.triggered.connect(self.export_ips)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_status)
        view_menu.addAction(refresh_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # 添加管理员界面入口
        admin_action = QAction("管理界面", self)
        admin_action.triggered.connect(self.show_admin_window)
        tools_menu.addAction(admin_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_config(self):
        try:
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
                
            # 更新监控器设置
            self.monitor.timeout = self.config["ping"]["timeout"]
            self.monitor.interval = self.config["ping"]["interval"]
            self.monitor.failure_threshold = self.config["ping"]["failure_threshold"]
            
            # 更新报警设置
            alert_config = AlertConfig(
                email_enabled=self.config["alert"]["email"]["enabled"],
                email_smtp_server=self.config["alert"]["email"]["smtp_server"],
                email_smtp_port=self.config["alert"]["email"]["smtp_port"],
                desktop_notification=self.config["alert"]["desktop_notification"],
                sound_alert=self.config["alert"]["sound_alert"],
                sound_file=self.config["alert"]["sound_file"]
            )
            self.alert_manager = AlertManager(alert_config)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置文件失败: {str(e)}")

    @pyqtSlot(str, IPStatus)
    def on_status_update(self, ip: str, status: IPStatus):
        """处理状态更新"""
        if status.consecutive_failures >= self.monitor.failure_threshold:
            self.alert_manager.send_alert(
                ip,
                f"IP {ip} 连续失败 {status.consecutive_failures} 次"
            )

    def add_ip(self):
        ip = self.ip_input.text().strip()
        group = self.group_combo.currentText().strip()
        
        if not ip:
            QMessageBox.warning(self, "警告", "请输入IP地址")
            return
            
        try:
            self.monitor.add_ip(ip, group)
            self.ip_input.clear()
            self.refresh_status()
            
            # 如果是新分组，添加到下拉框
            if group not in [self.group_combo.itemText(i) for i in range(self.group_combo.count())]:
                self.group_combo.addItem(group)
                
        except Exception as e:
            QMessageBox.warning(self, "警告", f"添加IP失败: {str(e)}")

    def import_ips(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "选择IP列表文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        ip = line.strip()
                        if ip and not ip.startswith("#"):
                            self.monitor.add_ip(ip)
                self.refresh_status()
                QMessageBox.information(self, "成功", "IP列表导入成功")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"导入IP列表失败: {str(e)}")

    def export_ips(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存IP列表",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    for ip, status in self.monitor.get_all_status().items():
                        f.write(f"{ip} # {status.group}\n")
                QMessageBox.information(self, "成功", "IP列表导出成功")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"导出IP列表失败: {str(e)}")

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = dialog.get_settings()
            
            # 更新配置文件
            self.config.update(settings)
            with open("config/config.yaml", "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True)
            
            # 更新监控器设置
            self.monitor.timeout = settings["ping"]["timeout"]
            self.monitor.interval = settings["ping"]["interval"]
            self.monitor.failure_threshold = settings["ping"]["failure_threshold"]
            
            # 更新报警设置
            alert_config = AlertConfig(
                email_enabled=settings["alert"]["email"]["enabled"],
                email_smtp_server=settings["alert"]["email"]["smtp_server"],
                email_smtp_port=settings["alert"]["email"]["smtp_port"],
                desktop_notification=settings["alert"]["desktop_notification"],
                sound_alert=settings["alert"]["sound_alert"]
            )
            self.alert_manager = AlertManager(alert_config)

    def show_context_menu(self, pos):
        menu = QMenu()
        
        remove_action = QAction("删除", self)
        remove_action.triggered.connect(self.remove_selected_ip)
        menu.addAction(remove_action)
        
        menu.exec(self.status_table.mapToGlobal(pos))

    def remove_selected_ip(self):
        selected_rows = self.status_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            ip = self.status_table.item(row, 0).text()
            self.monitor.remove_ip(ip)
            self.refresh_status()

    def refresh_status(self):
        """刷新状态表格"""
        self.status_table.setRowCount(0)
        
        for ip, status in self.monitor.get_all_status().items():
            row = self.status_table.rowCount()
            self.status_table.insertRow(row)
            
            # IP地址
            self.status_table.setItem(row, 0, QTableWidgetItem(ip))
            
            # 状态
            status_item = QTableWidgetItem("在线" if status.is_online else "离线")
            status_item.setForeground(
                QColor(self.config["ui"]["status_colors"]["online"] if status.is_online
                      else self.config["ui"]["status_colors"]["offline"])
            )
            self.status_table.setItem(row, 1, status_item)
            
            # 响应时间
            self.status_table.setItem(row, 2, QTableWidgetItem(
                f"{status.response_time:.1f}" if status.response_time > 0 else "-"
            ))
            
            # 最后成功时间
            self.status_table.setItem(row, 3, QTableWidgetItem(
                status.last_success.strftime("%Y-%m-%d %H:%M:%S")
                if status.last_success else "-"
            ))
            
            # 最后失败时间
            self.status_table.setItem(row, 4, QTableWidgetItem(
                status.last_failure.strftime("%Y-%m-%d %H:%M:%S")
                if status.last_failure else "-"
            ))
            
            # 连续失败次数
            failure_item = QTableWidgetItem(str(status.consecutive_failures))
            if status.consecutive_failures >= self.monitor.failure_threshold:
                failure_item.setForeground(QColor(self.config["ui"]["status_colors"]["warning"]))
            self.status_table.setItem(row, 5, failure_item)
        
        # 调整列宽
        self.status_table.resizeColumnsToContents()
        
        # 更新状态栏
        total = len(self.monitor.get_all_status())
        online = sum(1 for status in self.monitor.get_all_status().values() if status.is_online)
        self.statusBar.showMessage(f"总计: {total} | 在线: {online} | 离线: {total - online}")

    def show_about(self):
        QMessageBox.about(
            self,
            "关于",
            "IP Ping 监控工具\n\n"
            "版本: 1.0.0\n"
            "一个用于监控IP地址连通性的工具\n\n"
            "支持功能：\n"
            "- 多IP监控\n"
            "- 实时状态显示\n"
            "- 多种报警方式\n"
            "- 分组管理"
        )

    def show_admin_window(self):
        """显示管理员界面"""
        dialog = AdminWindow(self.monitor, self.alert_manager)
        dialog.exec()

    def closeEvent(self, event):
        """关闭窗口时停止监控"""
        self.monitor.stop()
        event.accept() 