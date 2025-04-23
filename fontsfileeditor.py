#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QLabel, 
                            QVBoxLayout, QHBoxLayout, QFileDialog, QTextEdit, 
                            QLineEdit, QGroupBox, QCheckBox, QMessageBox, QProgressBar,
                            QRadioButton, QButtonGroup, QGridLayout, QScrollArea, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QFontDatabase
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

def load_embedded_font():
    font_path = ""
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        font_path = os.path.join(application_path, "HMOSSSC.ttf")
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(application_path, "HMOSSSC.ttf")
    
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                return font_families[0]
    return ""

class FontSubsetWorker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, font_path, output_path, chars_to_keep, options):
        super().__init__()
        self.font_path = font_path
        self.output_path = output_path
        self.chars_to_keep = chars_to_keep
        self.options = options

    def run(self):
        try:
            all_chars_to_keep = set()
            
            if self.chars_to_keep:
                all_chars_to_keep.update(self.chars_to_keep)
            
            if self.options.get('ascii_half', False):
                all_chars_to_keep.update(chr(i) for i in range(32, 127))
            
            if self.options.get('ascii_full', False):
                all_chars_to_keep.update(chr(i) for i in range(0xFF01, 0xFF5F))
                all_chars_to_keep.update(chr(i) for i in range(0xFF61, 0xFFDC))
            
            if self.options.get('punctuation', False):
                punctuations = '，。！？、：；''""「」【】《》（）…—～·'
                all_chars_to_keep.update(punctuations)
            
            if self.options.get('numbers', False):
                all_chars_to_keep.update('0123456789')
            
            font = TTFont(self.font_path)
            self.progress_updated.emit(20)
            
            options = Options()
            options.layout_features = ["*"]
            options.name_IDs = ["*"]
            options.notdef_outline = True
            options.recalc_bounds = True
            options.recalc_timestamp = True
            
            subsetter = Subsetter(options=options)
            
            unicodes = [ord(char) for char in all_chars_to_keep]
            subsetter.populate(unicodes=unicodes)
            
            self.progress_updated.emit(50)
            
            subsetter.subset(font)
            
            self.progress_updated.emit(80)
            
            font.save(self.output_path)
            
            self.progress_updated.emit(100)
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(f"处理字体时发生错误: {str(e)}")


class FontSubsetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("字体文件裁剪工具")
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_style()
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        top_group = QGroupBox("选择字体文件")
        top_layout = QHBoxLayout()
        
        self.font_path_edit = QLineEdit()
        self.font_path_edit.setPlaceholderText("请选择字体文件...")
        self.font_path_edit.setReadOnly(True)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_font)
        
        top_layout.addWidget(self.font_path_edit, 7)
        top_layout.addWidget(browse_btn, 1)
        top_group.setLayout(top_layout)
        
        middle_group = QGroupBox("字符选择")
        middle_layout = QVBoxLayout()
        
        options_layout = QGridLayout()
        
        self.ascii_half_check = QCheckBox("半角ASCII字符")
        self.ascii_half_check.setChecked(True)
        
        self.ascii_full_check = QCheckBox("全角ASCII字符")
        self.ascii_full_check.setChecked(True)
        
        self.punctuation_check = QCheckBox("中文标点符号")
        self.punctuation_check.setChecked(True)
        
        self.numbers_check = QCheckBox("数字0-9")
        self.numbers_check.setChecked(True)
        
        options_layout.addWidget(self.ascii_half_check, 0, 0)
        options_layout.addWidget(self.ascii_full_check, 0, 1)
        options_layout.addWidget(self.punctuation_check, 1, 0)
        options_layout.addWidget(self.numbers_check, 1, 1)
        
        custom_layout = QVBoxLayout()
        
        custom_label = QLabel("自定义中文字符:")
        self.custom_chars_edit = QTextEdit()
        self.custom_chars_edit.setPlaceholderText("在此输入需要保留的中文字符...")
        
        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(self.custom_chars_edit)
        
        middle_layout.addLayout(options_layout)
        middle_layout.addLayout(custom_layout)
        middle_group.setLayout(middle_layout)
        
        bottom_group = QGroupBox("输出选项")
        bottom_layout = QVBoxLayout()
        
        output_layout = QHBoxLayout()
        output_label = QLabel("输出路径:")
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("选择输出路径...")
        
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self.browse_output)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit, 7)
        output_layout.addWidget(output_browse_btn, 1)
        
        progress_layout = QHBoxLayout()
        progress_label = QLabel("进度:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始裁剪")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_subset)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_subset)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        bottom_layout.addLayout(output_layout)
        bottom_layout.addLayout(progress_layout)
        bottom_layout.addLayout(buttons_layout)
        
        bottom_group.setLayout(bottom_layout)
        
        main_layout.addWidget(top_group)
        main_layout.addWidget(middle_group, 3)
        main_layout.addWidget(bottom_group)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.statusBar().showMessage("准备就绪")
        
    def setup_style(self):
        app = QApplication.instance()
        
        embedded_font = load_embedded_font()
        font_family = embedded_font if embedded_font else "HarmonyOS Sans SC"
        
        font = QFont()
        font.setFamily(font_family)
        font.setPointSize(10)
        app.setFont(font)
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(20, 20, 20))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(20, 20, 20))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(20, 20, 20))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        
        self.setStyleSheet(f"""
            * {{
                font-family: "{font_family}", "微软雅黑", "黑体", "宋体";
            }}
            QGroupBox {{
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 0.5ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }}
            QPushButton {{
                background-color: #4A86E8;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: #3B78DE;
            }}
            QPushButton:pressed {{
                background-color: #2D6CD3;
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #666666;
            }}
            QLineEdit, QTextEdit {{
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-size: 9pt;
            }}
            QProgressBar {{
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: #4A86E8;
                width: 10px;
                margin: 0.5px;
            }}
            QLabel {{
                font-size: 9pt;
            }}
            QCheckBox {{
                font-size: 9pt;
            }}
        """)
    
    def browse_font(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字体文件", "", 
            "字体文件 (*.ttf *.otf *.ttc *.otc);;所有文件 (*)", 
            options=options
        )
        
        if file_path:
            self.font_path_edit.setText(file_path)
            base_path = os.path.splitext(file_path)[0]
            self.output_path_edit.setText(f"{base_path}_subset.ttf")
            self.update_start_button_state()
    
    def browse_output(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出路径", "", 
            "TrueType 字体 (*.ttf);;OpenType 字体 (*.otf);;所有文件 (*)", 
            options=options
        )
        
        if file_path:
            self.output_path_edit.setText(file_path)
            self.update_start_button_state()
    
    def update_start_button_state(self):
        has_font = bool(self.font_path_edit.text().strip())
        has_output = bool(self.output_path_edit.text().strip())
        
        self.start_btn.setEnabled(has_font and has_output)
    
    def start_subset(self):
        font_path = self.font_path_edit.text()
        output_path = self.output_path_edit.text()
        
        custom_chars = self.custom_chars_edit.toPlainText()
        
        options = {
            'ascii_half': self.ascii_half_check.isChecked(),
            'ascii_full': self.ascii_full_check.isChecked(),
            'punctuation': self.punctuation_check.isChecked(),
            'numbers': self.numbers_check.isChecked()
        }
        
        if not any(options.values()) and not custom_chars:
            QMessageBox.warning(self, "警告", "请至少选择一种字符或输入自定义字符!")
            return
        
        self.worker = FontSubsetWorker(font_path, output_path, custom_chars, options)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.on_subset_finished)
        self.worker.error.connect(self.on_subset_error)
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("正在裁剪字体...")
        
        self.worker.start()
    
    def cancel_subset(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
            self.progress_bar.setValue(0)
            self.statusBar().showMessage("操作已取消")
            self.start_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def on_subset_finished(self, output_path):
        self.progress_bar.setValue(100)
        self.statusBar().showMessage(f"字体裁剪完成: {output_path}")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        QMessageBox.information(self, "完成", f"字体裁剪完成!\n输出文件: {output_path}")
    
    def on_subset_error(self, error_msg):
        self.progress_bar.setValue(0)
        self.statusBar().showMessage(f"错误: {error_msg}")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        QMessageBox.critical(self, "错误", f"字体裁剪过程中发生错误:\n{error_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FontSubsetApp()
    window.show()
    sys.exit(app.exec_())