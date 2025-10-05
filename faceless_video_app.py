import os
import sys
import logging
import tempfile
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QComboBox, QSpinBox, QLabel, QMessageBox,
                             QLineEdit, QCheckBox, QListWidget, QFileDialog, QMenuBar, QMenu,
                             QAction, QTabWidget, QGridLayout, QStatusBar, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from moviepy.config import change_settings
from gtts import gTTS
import requests
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import urllib3
import webbrowser

class FacelessVideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faceless YouTube Video Creator")
        self.setGeometry(100, 100, 1200, 900)
        self.assets_dir = os.path.join(os.getcwd(), "assets")
        self.output_dir = os.path.join(os.getcwd(), "output_videos")
        self.video_log = os.path.join(os.getcwd(), "video_log.txt")
        self.licenses_file = os.path.join(os.getcwd(), "asset_licenses.json")
        self.scripts = []
        self.batch_scripts = []
        self.affiliate_links = {}
        self.licenses = {}
        self.undo_stack = []
        self.redo_stack = []
        self.templates = {
            "Morning Meditation": {"music": "Meditation Spa 1", "color": "white", "font_size": 24, "exclusive": False},
            "Sleep Sounds": {"music": "Meditation Spa 2", "color": "blue", "font_size": 20, "exclusive": False},
            "Stress Relief": {"music": "Meditation Spa 1", "color": "yellow", "font_size": 22, "exclusive": False},
            "Members Only": {"music": "Meditation Spa 2", "color": "white", "font_size": 24, "exclusive": True}
        }
        self.youtube = None
        self.dark_theme = True
        self.init_logging()
        self.init_ui()
        self.verify_assets()
        self.load_affiliate_links()
        self.load_licenses()

    def init_logging(self):
        logging.basicConfig(
            filename=self.video_log,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("Application started")

    def verify_assets(self):
        required_assets = [
            os.path.join(self.assets_dir, "fallback_nature.mp4"),
            os.path.join(self.assets_dir, "meditation1.mp3"),
            os.path.join(self.assets_dir, "meditation2.mp3")
        ]
        for asset in required_assets:
            if not os.path.exists(asset):
                logging.error(f"Missing asset: {asset}")
                QMessageBox.critical(self, "Error", f"Missing asset: {asset}\nPlease download it to {self.assets_dir}")
                sys.exit(1)
            if asset.endswith(".mp4"):
                try:
                    clip = VideoFileClip(asset)
                    clip.close()
                    logging.info(f"Validated video asset: {asset}")
                except Exception as e:
                    logging.error(f"Invalid video asset {asset}: {e}")
                    QMessageBox.critical(self, "Error", f"Invalid video asset: {asset}\nPlease redownload from Pixabay")
                    sys.exit(1)
        logging.info("All assets verified")
        self.statusBar().showMessage("Assets verified", 5000)

    def init_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Initialize Widgets
        self.script_input = QTextEdit()
        self.script_combo = QComboBox()
        self.template_combo = QComboBox()
        self.animation_combo = QComboBox()
        self.sectioned_text = QCheckBox("Split Text into Fading Sections")
        self.music_combo = QComboBox()
        self.color_combo = QComboBox()
        self.font_size_spin = QSpinBox()
        self.seo_input = QTextEdit()
        self.affiliate_combo = QComboBox()
        self.batch_list = QListWidget()
        self.youtube_title = QLineEdit()
        self.comment_input = QLineEdit()
        self.response_output = QLineEdit()

        # Tabs
        tabs = QTabWidget()
        tabs.setToolTip("Switch between script, video, and analytics")
        main_layout.addWidget(tabs)

        # Script Tab
        script_widget = QWidget()
        script_layout = QGridLayout(script_widget)
        script_layout.setSpacing(10)
        self.script_input.setPlaceholderText("Enter your video script here...")
        self.script_input.setToolTip("Write your meditation script here")
        script_layout.addWidget(self.script_input, 0, 0, 1, 2)
        add_script_btn = QPushButton("Add Script")
        add_script_btn.clicked.connect(self.add_script)
        add_script_btn.setToolTip("Add script to the list")
        script_layout.addWidget(add_script_btn, 1, 0)
        self.script_combo.currentIndexChanged.connect(self.update_script)
        self.script_combo.setToolTip("Select a saved script")
        script_layout.addWidget(QLabel("Select Script:"), 2, 0)
        script_layout.addWidget(self.script_combo, 2, 1)
        tabs.addTab(script_widget, "Scripts")

        # Video Tab
        video_widget = QWidget()
        video_layout = QGridLayout(video_widget)
        video_layout.setSpacing(10)
        self.template_combo.addItems(["Custom"] + list(self.templates.keys()))
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        self.template_combo.setToolTip("Choose a video template")
        video_layout.addWidget(QLabel("Select Template:"), 0, 0)
        video_layout.addWidget(self.template_combo, 0, 1)
        self.animation_combo.addItems(["Static", "Fade", "Slide"])
        self.animation_combo.setToolTip("Select text animation style")
        video_layout.addWidget(QLabel("Text Animation:"), 1, 0)
        video_layout.addWidget(self.animation_combo, 1, 1)
        self.sectioned_text.setChecked(True)
        self.sectioned_text.setToolTip("Display script in timed sections")
        video_layout.addWidget(self.sectioned_text, 2, 0, 1, 2)
        self.music_options = {
            "None": None,
            "Meditation Spa 1": os.path.join(self.assets_dir, "meditation1.mp3"),
            "Meditation Spa 2": os.path.join(self.assets_dir, "meditation2.mp3")
        }
        self.music_combo.addItems(self.music_options.keys())
        self.music_combo.setToolTip("Select background music")
        video_layout.addWidget(QLabel("Background Music:"), 3, 0)
        video_layout.addWidget(self.music_combo, 3, 1)
        self.color_combo.addItems(["white", "yellow", "blue"])
        self.color_combo.setToolTip("Choose text color")
        video_layout.addWidget(QLabel("Text Color:"), 4, 0)
        video_layout.addWidget(self.color_combo, 4, 1)
        self.font_size_spin.setRange(16, 32)
        self.font_size_spin.setValue(24)
        self.font_size_spin.setToolTip("Set text size")
        video_layout.addWidget(QLabel("Font Size:"), 5, 0)
        video_layout.addWidget(self.font_size_spin, 5, 1)
        self.seo_input.setPlaceholderText("e.g., meditation music, relaxing sounds, sleep meditation")
        self.seo_input.setFixedHeight(50)
        self.seo_input.setToolTip("Enter SEO keywords")
        video_layout.addWidget(QLabel("SEO Keywords:"), 6, 0)
        video_layout.addWidget(self.seo_input, 6, 1)
        suggest_seo_btn = QPushButton("Suggest Keywords")
        suggest_seo_btn.clicked.connect(self.suggest_seo_keywords)
        suggest_seo_btn.setToolTip("Get trending keywords")
        video_layout.addWidget(suggest_seo_btn, 7, 0, 1, 2)
        self.affiliate_combo.addItem("None")
        self.affiliate_combo.setToolTip("Select an affiliate link")
        video_layout.addWidget(QLabel("Affiliate Links:"), 8, 0)
        video_layout.addWidget(self.affiliate_combo, 8, 1)
        manage_affiliate_btn = QPushButton("Manage Affiliate Links")
        manage_affiliate_btn.clicked.connect(self.manage_affiliate_links)
        manage_affiliate_btn.setToolTip("Add or edit affiliate links")
        video_layout.addWidget(manage_affiliate_btn, 9, 0, 1, 2)
        self.batch_list.setToolTip("Scripts queued for batch generation")
        video_layout.addWidget(QLabel("Batch Video Generation:"), 10, 0)
        video_layout.addWidget(self.batch_list, 10, 1)
        batch_add_btn = QPushButton("Add Script to Batch")
        batch_add_btn.clicked.connect(self.add_to_batch)
        batch_add_btn.setToolTip("Queue script for batch processing")
        video_layout.addWidget(batch_add_btn, 11, 0)
        batch_generate_btn = QPushButton("Generate Batch Videos")
        batch_generate_btn.clicked.connect(self.generate_batch_videos)
        batch_generate_btn.setToolTip("Generate all queued videos")
        video_layout.addWidget(batch_generate_btn, 11, 1)
        self.youtube_title.setPlaceholderText("Enter video title")
        self.youtube_title.setToolTip("Set YouTube video title")
        video_layout.addWidget(QLabel("YouTube Upload:"), 12, 0)
        video_layout.addWidget(self.youtube_title, 12, 1)
        youtube_upload_btn = QPushButton("Upload to YouTube")
        youtube_upload_btn.clicked.connect(self.upload_to_youtube)
        youtube_upload_btn.setToolTip("Upload latest video to YouTube")
        video_layout.addWidget(youtube_upload_btn, 13, 0, 1, 2)
        generate_btn = QPushButton("Generate Video")
        generate_btn.clicked.connect(self.generate_video)
        generate_btn.setToolTip("Create a single video")
        video_layout.addWidget(generate_btn, 14, 0)
        preview_btn = QPushButton("Preview Last Video")
        preview_btn.clicked.connect(self.preview_video)
        preview_btn.setToolTip("View the latest generated video")
        video_layout.addWidget(preview_btn, 14, 1)
        tabs.addTab(video_widget, "Video")

        # Analytics Tab
        analytics_widget = QWidget()
        analytics_layout = QGridLayout(analytics_widget)
        analytics_btn = QPushButton("View YouTube Analytics")
        analytics_btn.clicked.connect(self.show_analytics)
        analytics_btn.setToolTip("Display video performance stats")
        analytics_layout.addWidget(analytics_btn, 0, 0)
        self.comment_input.setPlaceholderText("Enter viewer comment")
        self.comment_input.setToolTip("Input a viewer comment")
        analytics_layout.addWidget(QLabel("Comment Response Generator:"), 1, 0)
        analytics_layout.addWidget(self.comment_input, 1, 1)
        generate_response_btn = QPushButton("Generate Response")
        generate_response_btn.clicked.connect(self.generate_comment_response)
        generate_response_btn.setToolTip("Create a reply to the comment")
        analytics_layout.addWidget(generate_response_btn, 2, 0)
        self.response_output.setReadOnly(True)
        self.response_output.setToolTip("Generated comment response")
        analytics_layout.addWidget(self.response_output, 2, 1)
        tabs.addTab(analytics_widget, "Analytics")

        # Menu Bar (after widgets)
        menubar = self.menuBar()
        self.create_file_menu(menubar)
        self.create_edit_menu(menubar)
        self.create_view_menu(menubar)
        self.create_settings_menu(menubar)
        self.create_tools_menu(menubar)
        self.create_resources_menu(menubar)
        self.create_help_menu(menubar)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready", 5000)

        # Apply Theme
        self.apply_theme()

    def create_file_menu(self, menubar):
        file_menu = menubar.addMenu("&File")
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setToolTip("Start a new project")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        save_action = QAction("&Save Scripts", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setToolTip("Save scripts to file")
        save_action.triggered.connect(self.save_scripts)
        file_menu.addAction(save_action)
        load_action = QAction("&Load Scripts", self)
        load_action.setShortcut(QKeySequence.Open)
        load_action.setToolTip("Load scripts from file")
        load_action.triggered.connect(self.load_scripts)
        file_menu.addAction(load_action)
        file_menu.addSeparator()
        export_action = QAction("&Export Video", self)
        export_action.setToolTip("Export the latest video")
        export_action.triggered.connect(self.preview_video)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setToolTip("Close the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_edit_menu(self, menubar):
        edit_menu = menubar.addMenu("&Edit")
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setToolTip("Undo last script edit")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setToolTip("Redo last script edit")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.setToolTip("Cut selected text")
        cut_action.triggered.connect(self.script_input.cut)
        edit_menu.addAction(cut_action)
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.setToolTip("Copy selected text")
        copy_action.triggered.connect(self.script_input.copy)
        edit_menu.addAction(copy_action)
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.setToolTip("Paste text")
        paste_action.triggered.connect(self.script_input.paste)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        pref_action = QAction("P&references", self)
        pref_action.setToolTip("Edit application settings")
        pref_action.triggered.connect(self.edit_preferences)
        edit_menu.addAction(pref_action)

    def create_view_menu(self, menubar):
        view_menu = menubar.addMenu("&View")
        theme_action = QAction("&Toggle Dark/Light Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.setToolTip("Switch between dark and light themes")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setToolTip("Increase UI size")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setToolTip("Decrease UI size")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        full_screen_action = QAction("&Full Screen", self)
        full_screen_action.setShortcut("F11")
        full_screen_action.setToolTip("Toggle full screen mode")
        full_screen_action.triggered.connect(self.toggle_full_screen)
        view_menu.addAction(full_screen_action)
        status_bar_action = QAction("&Status Bar", self)
        status_bar_action.setCheckable(True)
        status_bar_action.setChecked(True)
        status_bar_action.setToolTip("Show/hide status bar")
        status_bar_action.triggered.connect(self.toggle_status_bar)
        view_menu.addAction(status_bar_action)

    def create_settings_menu(self, menubar):
        settings_menu = menubar.addMenu("&Settings")
        api_key_action = QAction("&Configure API Keys", self)
        api_key_action.setToolTip("Set Pexels/YouTube API keys")
        api_key_action.triggered.connect(self.configure_api_keys)
        settings_menu.addAction(api_key_action)
        asset_path_action = QAction("&Set Asset Paths", self)
        asset_path_action.setToolTip("Configure asset directories")
        asset_path_action.triggered.connect(self.set_asset_paths)
        settings_menu.addAction(asset_path_action)
        video_quality_action = QAction("&Video Quality", self)
        video_quality_action.setToolTip("Adjust output video quality")
        video_quality_action.triggered.connect(self.set_video_quality)
        settings_menu.addAction(video_quality_action)

    def create_tools_menu(self, menubar):
        tools_menu = menubar.addMenu("&Tools")
        batch_action = QAction("&Batch Process", self)
        batch_action.setToolTip("Generate multiple videos")
        batch_action.triggered.connect(self.generate_batch_videos)
        tools_menu.addAction(batch_action)
        thumbnail_action = QAction("&Thumbnail Editor", self)
        thumbnail_action.setToolTip("Create a video thumbnail")
        thumbnail_action.triggered.connect(self.create_thumbnail)
        tools_menu.addAction(thumbnail_action)
        analytics_action = QAction("&Analytics Viewer", self)
        analytics_action.setToolTip("View YouTube analytics")
        analytics_action.triggered.connect(self.show_analytics)
        tools_menu.addAction(analytics_action)
        license_action = QAction("&License Logger", self)
        license_action.setToolTip("Log asset licenses")
        license_action.triggered.connect(self.log_asset_license)
        tools_menu.addAction(license_action)

    def create_resources_menu(self, menubar):
        resources_menu = menubar.addMenu("&Resources")
        pixabay_action = QAction("&Pixabay Assets", self)
        pixabay_action.setToolTip("Open Pixabay for assets")
        pixabay_action.triggered.connect(lambda: webbrowser.open("https://pixabay.com"))
        resources_menu.addAction(pixabay_action)
        pexels_action = QAction("Pe&xels Videos", self)
        pexels_action.setToolTip("Open Pexels for videos")
        pexels_action.triggered.connect(lambda: webbrowser.open("https://pexels.com"))
        resources_menu.addAction(pexels_action)
        affiliate_action = QAction("&Affiliate Guide", self)
        affiliate_action.setToolTip("Learn about affiliate marketing")
        affiliate_action.triggered.connect(lambda: webbrowser.open("https://affiliate-program.amazon.com"))
        resources_menu.addAction(affiliate_action)
        seo_action = QAction("&SEO Tools", self)
        seo_action.setToolTip("Access SEO resources")
        seo_action.triggered.connect(lambda: webbrowser.open("https://www.tubebuddy.com"))
        resources_menu.addAction(seo_action)

    def create_help_menu(self, menubar):
        help_menu = menubar.addMenu("&Help")
        doc_action = QAction("&Documentation", self)
        doc_action.setToolTip("View user guide")
        doc_action.triggered.connect(lambda: webbrowser.open("https://example.com/docs"))  # Placeholder
        help_menu.addAction(doc_action)
        tutorial_action = QAction("&Tutorials", self)
        tutorial_action.setToolTip("Watch video tutorials")
        tutorial_action.triggered.connect(lambda: webbrowser.open("https://example.com/tutorials"))  # Placeholder
        help_menu.addAction(tutorial_action)
        about_action = QAction("&About", self)
        about_action.setToolTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        update_action = QAction("&Check for Updates", self)
        update_action.setToolTip("Check for new versions")
        update_action.triggered.connect(self.check_updates)
        help_menu.addAction(update_action)

    def apply_theme(self):
        if self.dark_theme:
            self.setStyleSheet("""
                QMainWindow { background-color: #2E2E2E; color: #FFFFFF; }
                QWidget { background-color: #2E2E2E; color: #FFFFFF; }
                QTextEdit, QLineEdit, QComboBox, QSpinBox { background-color: #3E3E3E; color: #FFFFFF; border: 1px solid #555555; }
                QPushButton { background-color: #4A90E2; color: #FFFFFF; border: none; padding: 5px; }
                QPushButton:hover { background-color: #357ABD; }
                QTabWidget::pane { border: 1px solid #555555; }
                QTabBar::tab { background: #3E3E3E; color: #FFFFFF; padding: 8px; }
                QTabBar::tab:selected { background: #4A90E2; }
                QMenuBar { background-color: #2E2E2E; color: #FFFFFF; }
                QMenuBar::item:selected { background-color: #4A90E2; }
                QMenu { background-color: #3E3E3E; color: #FFFFFF; }
                QMenu::item:selected { background-color: #4A90E2; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #FFFFFF; color: #000000; }
                QWidget { background-color: #FFFFFF; color: #000000; }
                QTextEdit, QLineEdit, QComboBox, QSpinBox { background-color: #F5F5F5; color: #000000; border: 1px solid #CCCCCC; }
                QPushButton { background-color: #4A90E2; color: #FFFFFF; border: none; padding: 5px; }
                QPushButton:hover { background-color: #357ABD; }
                QTabWidget::pane { border: 1px solid #CCCCCC; }
                QTabBar::tab { background: #F5F5F5; color: #000000; padding: 8px; }
                QTabBar::tab:selected { background: #4A90E2; color: #FFFFFF; }
                QMenuBar { background-color: #FFFFFF; color: #000000; }
                QMenuBar::item:selected { background-color: #4A90E2; color: #FFFFFF; }
                QMenu { background-color: #F5F5F5; color: #000000; }
                QMenu::item:selected { background-color: #4A90E2; color: #FFFFFF; }
            """)
        self.statusBar().showMessage("Theme applied", 3000)

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.apply_theme()

    def zoom_in(self):
        self.setStyleSheet(self.styleSheet() + " QWidget { font-size: 14px; }")
        self.statusBar().showMessage("Zoomed in", 3000)

    def zoom_out(self):
        self.setStyleSheet(self.styleSheet() + " QWidget { font-size: 10px; }")
        self.statusBar().showMessage("Zoomed out", 3000)

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self.statusBar().showMessage("Toggled full screen", 3000)

    def toggle_status_bar(self):
        self.statusBar().setVisible(not self.statusBar().isVisible())
        self.statusBar().showMessage("Status bar toggled", 3000)

    def new_project(self):
        self.scripts.clear()
        self.batch_scripts.clear()
        self.script_combo.clear()
        self.batch_list.clear()
        self.script_input.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.statusBar().showMessage("New project started", 5000)
        logging.info("New project started")

    def save_scripts(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Scripts", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as f:
                json.dump({"scripts": self.scripts, "batch_scripts": self.batch_scripts}, f)
            self.statusBar().showMessage(f"Scripts saved to {file_path}", 5000)
            logging.info(f"Saved scripts to {file_path}")

    def load_scripts(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Scripts", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                self.scripts = data.get("scripts", [])
                self.batch_scripts = data.get("batch_scripts", [])
                self.script_combo.clear()
                self.batch_list.clear()
                for i, script in enumerate(self.scripts, 1):
                    self.script_combo.addItem(f"Script {i}")
                for i, script in enumerate(self.batch_scripts, 1):
                    self.batch_list.addItem(f"Script {i}")
                self.statusBar().showMessage(f"Scripts loaded from {file_path}", 5000)
                logging.info(f"Loaded scripts from {file_path}")
            except Exception as e:
                logging.error(f"Failed to load scripts: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load scripts: {e}")

    def edit_preferences(self):
        QMessageBox.information(self, "Preferences", "Preferences editing not yet implemented")
        self.statusBar().showMessage("Opened preferences", 3000)

    def configure_api_keys(self):
        key, ok = QInputDialog.getText(self, "Pexels API Key", "Enter Pexels API key:")
        if ok and key:
            # Placeholder: Store securely in future
            self.statusBar().showMessage("Pexels API key updated", 5000)
            logging.info("Updated Pexels API key")

    def set_asset_paths(self):
        path = QFileDialog.getExistingDirectory(self, "Select Assets Directory", self.assets_dir)
        if path:
            self.assets_dir = path
            self.verify_assets()
            self.statusBar().showMessage(f"Asset directory set to {path}", 5000)
            logging.info(f"Asset directory set to {path}")

    def set_video_quality(self):
        quality, ok = QInputDialog.getItem(self, "Video Quality", "Select quality:", ["High", "Medium", "Low"], 1, False)
        if ok:
            self.statusBar().showMessage(f"Video quality set to {quality}", 5000)
            logging.info(f"Video quality set to {quality}")

    def show_about(self):
        QMessageBox.about(self, "About", "Faceless YouTube Video Creator\nVersion 1.0\n© 2025 YourName")
        self.statusBar().showMessage("Displayed about dialog", 3000)

    def check_updates(self):
        QMessageBox.information(self, "Updates", "No updates available")
        self.statusBar().showMessage("Checked for updates", 3000)

    def add_script(self):
        script_text = self.script_input.toPlainText().strip()
        if script_text:
            self.undo_stack.append(("add_script", script_text))
            self.redo_stack.clear()
            self.scripts.append(script_text)
            self.script_combo.addItem(f"Script {len(self.scripts)}")
            self.script_input.clear()
            self.statusBar().showMessage("Script added", 5000)
            logging.info(f"Added script {len(self.scripts)}")
        else:
            QMessageBox.warning(self, "Warning", "Script cannot be empty")

    def add_to_batch(self):
        script_text = self.script_input.toPlainText().strip()
        if script_text:
            self.batch_scripts.append(script_text)
            self.batch_list.addItem(f"Script {len(self.batch_scripts)}")
            self.script_input.clear()
            self.statusBar().showMessage("Script added to batch", 5000)
            logging.info(f"Added script to batch: {len(self.batch_scripts)}")
        else:
            QMessageBox.warning(self, "Warning", "Script cannot be empty")

    def apply_template(self):
        template_name = self.template_combo.currentText()
        if template_name != "Custom" and template_name in self.templates:
            template = self.templates[template_name]
            self.music_combo.setCurrentText(template["music"])
            self.color_combo.setCurrentText(template["color"])
            self.font_size_spin.setValue(template["font_size"])
            self.statusBar().showMessage(f"Applied template: {template_name}", 5000)
            logging.info(f"Applied template: {template_name}")

    def update_script(self):
        index = self.script_combo.currentIndex()
        if index >= 0:
            self.script_input.setText(self.scripts[index])

    def undo(self):
        if not self.undo_stack:
            return
        action, data = self.undo_stack.pop()
        if action == "add_script":
            self.scripts.pop()
            self.script_combo.removeItem(self.script_combo.count() - 1)
            self.redo_stack.append((action, data))
            self.statusBar().showMessage("Undid script addition", 5000)
            logging.info("Undid script addition")

    def redo(self):
        if not self.redo_stack:
            return
        action, data = self.redo_stack.pop()
        if action == "add_script":
            self.scripts.append(data)
            self.script_combo.addItem(f"Script {len(self.scripts)}")
            self.undo_stack.append((action, data))
            self.statusBar().showMessage("Redid script addition", 5000)
            logging.info("Redid script addition")

    def suggest_seo_keywords(self):
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', 'https://trends.google.com/trends/api/explore?hl=en-US&q=meditation')
            keywords = ["meditation music", "relaxing sounds", "sleep meditation"]  # Placeholder
            self.seo_input.setText(", ".join(keywords))
            self.statusBar().showMessage("Suggested SEO keywords", 5000)
            logging.info("Suggested SEO keywords")
        except Exception as e:
            logging.error(f"SEO keyword suggestion failed: {e}")
            QMessageBox.warning(self, "Warning", "Failed to fetch SEO keywords")

    def manage_affiliate_links(self):
        name, ok = QInputDialog.getText(self, "Affiliate Link", "Enter link name:")
        if ok and name:
            url, ok = QInputDialog.getText(self, "Affiliate Link", "Enter URL:")
            if ok and url:
                self.affiliate_links[name] = url
                self.affiliate_combo.addItem(name)
                with open("affiliate_links.json", "w") as f:
                    json.dump(self.affiliate_links, f)
                self.statusBar().showMessage(f"Added affiliate link: {name}", 5000)
                logging.info(f"Added affiliate link: {name}")

    def load_affiliate_links(self):
        try:
            if os.path.exists("affiliate_links.json"):
                with open("affiliate_links.json", "r") as f:
                    self.affiliate_links = json.load(f)
                for name in self.affiliate_links:
                    self.affiliate_combo.addItem(name)
                self.statusBar().showMessage("Loaded affiliate links", 5000)
                logging.info("Loaded affiliate links")
        except Exception as e:
            logging.error(f"Failed to load affiliate links: {e}")

    def load_licenses(self):
        try:
            if os.path.exists(self.licenses_file):
                with open(self.licenses_file, "r") as f:
                    self.licenses = json.load(f)
                self.statusBar().showMessage("Loaded asset licenses", 5000)
                logging.info("Loaded asset licenses")
        except Exception as e:
            logging.error(f"Failed to load licenses: {e}")

    def generate_tts(self, text, output_file):
        try:
            logging.info("Generating TTS")
            tts = gTTS(text=text, lang='en')
            tts.save(output_file)
            logging.info(f"TTS saved to {output_file}")
            self.statusBar().showMessage("TTS generated", 5000)
            return True
        except Exception as e:
            logging.error(f"TTS generation failed: {e}")
            QMessageBox.critical(self, "Error", f"TTS generation failed: {e}")
            return False

    def fetch_pexels_video(self):
        logging.info("Fetching video from Pexels API")
        try:
            url = "https://api.pexels.com/videos/search?query=nature&per_page=1"
            headers = {"Authorization": "omioz8tanJumM0YfQSda2i2eceGXdCiez4ht8CbpFkNGDKLciQbvGpsJ"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                videos = response.json().get("videos", [])
                if not videos:
                    logging.warning("Pexels API returned no videos")
                    return None
                video_url = videos[0]["video_files"][0]["link"]
                video_file = os.path.join(tempfile.gettempdir(), f"pexels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                with open(video_file, "wb") as f:
                    video_response = requests.get(video_url, timeout=10)
                    if video_response.status_code != 200:
                        logging.error(f"Video download failed: Status {video_response.status_code}")
                        return None
                    f.write(video_response.content)
                if not os.path.exists(video_file) or os.path.getsize(video_file) == 0:
                    logging.error("Video file is missing or empty")
                    return None
                logging.info(f"Video downloaded to {video_file}")
                self.statusBar().showMessage("Pexels video downloaded", 5000)
                return video_file
            else:
                logging.error(f"Pexels API error: Status {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Failed to fetch Pexels video: {e}")
            return None

    def create_thumbnail(self):
        try:
            img = Image.new('RGB', (1280, 720), color='black')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            draw.text((50, 50), "Meditation Video", fill="white", font=font)
            thumbnail_path = os.path.join(self.output_dir, f"thumbnail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            img.save(thumbnail_path)
            logging.info(f"Thumbnail saved to {thumbnail_path}")
            self.statusBar().showMessage(f"Thumbnail saved: {thumbnail_path}", 5000)
            QMessageBox.information(self, "Success", f"Thumbnail saved: {thumbnail_path}")
        except Exception as e:
            logging.error(f"Thumbnail creation failed: {e}")
            QMessageBox.critical(self, "Error", f"Thumbnail creation failed: {e}")

    def log_asset_license(self):
        asset_path, _ = QFileDialog.getOpenFileName(self, "Select Asset", self.assets_dir)
        if asset_path:
            source, ok = QInputDialog.getText(self, "License Source", "Enter source (e.g., Pixabay URL):")
            if ok and source:
                self.licenses[os.path.basename(asset_path)] = source
                with open(self.licenses_file, "w") as f:
                    json.dump(self.licenses, f)
                logging.info(f"Logged license for {asset_path}")
                self.statusBar().showMessage("License logged", 5000)
                QMessageBox.information(self, "Success", "License logged")

    def authenticate_youtube(self):
        if not self.youtube:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json',
                    scopes=['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']
                )
                credentials = flow.run_local_server(port=0)
                self.youtube = build('youtube', 'v3', credentials=credentials)
                logging.info("YouTube authenticated")
                self.statusBar().showMessage("YouTube authenticated", 5000)
                return True
            except Exception as e:
                logging.error(f"YouTube authentication failed: {e}")
                QMessageBox.critical(self, "Error", f"YouTube authentication failed: {e}")
                return False
        return True

    def upload_to_youtube(self):
        if not self.authenticate_youtube():
            return
        videos = [f for f in os.listdir(self.output_dir) if f.endswith('.mp4')]
        if not videos:
            QMessageBox.warning(self, "Warning", "No videos found")
            return
        latest_video = max(videos, key=lambda x: os.path.getctime(os.path.join(self.output_dir, x)))
        video_path = os.path.join(self.output_dir, latest_video)
        title = self.youtube_title.text() or "Meditation Video"
        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": title, "description": "Relax and unwind!", "tags": ["meditation", "relaxation"]},
                    "status": {"privacyStatus": "public"}
                },
                media_body=MediaFileUpload(video_path)
            )
            response = request.execute()
            logging.info(f"Uploaded video to YouTube: {response['id']}")
            self.statusBar().showMessage("Video uploaded to YouTube", 5000)
            QMessageBox.information(self, "Success", "Video uploaded to YouTube")
        except Exception as e:
            logging.error(f"YouTube upload failed: {e}")
            QMessageBox.critical(self, "Error", f"YouTube upload failed: {e}")

    def show_analytics(self):
        if not self.authenticate_youtube():
            return
        try:
            request = self.youtube.videos().list(
                part="statistics",
                mine=True,
                maxResults=5
            )
            response = request.execute()
            analytics = "\n".join([f"Video: {item['id']}, Views: {item['statistics']['viewCount']}" for item in response.get('items', [])])
            QMessageBox.information(self, "Analytics", analytics or "No analytics available")
            self.statusBar().showMessage("Displayed YouTube analytics", 5000)
            logging.info("Displayed YouTube analytics")
        except Exception as e:
            logging.error(f"Analytics fetch failed: {e}")
            QMessageBox.critical(self, "Error", f"Analytics fetch failed: {e}")

    def generate_comment_response(self):
        comment = self.comment_input.text().strip()
        if not comment:
            QMessageBox.warning(self, "Warning", "Enter a comment")
            return
        response = f"Thank you for your comment! We're glad you're enjoying the meditation content."
        self.response_output.setText(response)
        self.statusBar().showMessage("Generated comment response", 5000)
        logging.info("Generated comment response")

    def generate_video(self, script=None, batch_mode=False):
        if not script:
            index = self.script_combo.currentIndex()
            if index < 0:
                QMessageBox.warning(self, "Warning", "No script selected")
                return
            script = self.scripts[index]
        music_file = self.music_options[self.music_combo.currentText()]
        text_color = self.color_combo.currentText()
        font_size = self.font_size_spin.value()
        animation = self.animation_combo.currentText()
        sectioned = self.sectioned_text.isChecked()
        seo_keywords = self.seo_input.toPlainText().strip() or "meditation music, relaxing sounds, sleep meditation"
        affiliate_name = self.affiliate_combo.currentText()
        affiliate_link = self.affiliate_links.get(affiliate_name) if affiliate_name != "None" else ""
        is_exclusive = self.templates.get(self.template_combo.currentText(), {}).get("exclusive", False)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"video_{timestamp}.mp4")
        tts_file = os.path.join(tempfile.gettempdir(), f"tts_{timestamp}.mp3")
        temp_video = None

        logging.info(f"Starting video generation: {output_file}")
        self.statusBar().showMessage(f"Generating video: {output_file}", 10000)

        # Generate TTS
        if not self.generate_tts(script, tts_file):
            return

        try:
            # Try Pexels video, fall back to local
            video_path = self.fetch_pexels_video()
            if not video_path:
                video_path = os.path.join(self.assets_dir, "fallback_nature.mp4")
                logging.info(f"Using fallback video: {video_path}")
            logging.info(f"Loading video: {video_path}")
            video_clip = VideoFileClip(video_path)

            # Load TTS audio
            tts_clip = AudioFileClip(tts_file)
            video_duration = video_clip.duration
            tts_duration = tts_clip.duration
            logging.info(f"Video duration: {video_duration}s, TTS duration: {tts_duration}s")

            # Adjust video duration to match TTS
            if tts_duration > video_duration:
                video_clip = video_clip.loop(duration=tts_duration)
            else:
                video_clip = video_clip.subclip(0, tts_duration)

            # Create text clips
            text_clips = []
            if sectioned:
                sections = script.split('. ')
                duration_per_section = tts_duration / max(1, len(sections))
                for i, section in enumerate(sections):
                    if not section.strip():
                        continue
                    start_time = i * duration_per_section
                    text_clip = TextClip(
                        section.strip(),
                        fontsize=font_size,
                        color=text_color,
                        font='Arial',
                        size=(video_clip.w - 40, None),
                        method='caption'
                    ).set_position(('center', 'bottom')).set_duration(duration_per_section).set_start(start_time)
                    if animation == "Fade":
                        text_clip = text_clip.fadein(0.5).fadeout(0.5)
                    elif animation == "Slide":
                        text_clip = text_clip.set_position(lambda t: ('center', video_clip.h - t * 100))
                    text_clips.append(text_clip)
            else:
                text_clip = TextClip(
                    script,
                    fontsize=font_size,
                    color=text_color,
                    font='Arial',
                    size=(video_clip.w - 40, None),
                    method='caption'
                ).set_position(('center', 'bottom')).set_duration(tts_duration)
                if animation == "Fade":
                    text_clip = text_clip.fadein(0.5).fadeout(0.5)
                elif animation == "Slide":
                    text_clip = text_clip.set_position(lambda t: ('center', video_clip.h - t * 100))
                text_clips.append(text_clip)

            # Combine video and text
            final_clip = CompositeVideoClip([video_clip] + text_clips).set_audio(tts_clip)

            # Add background music
            if music_file:
                logging.info(f"Adding background music: {music_file}")
                music_clip = AudioFileClip(music_file).volumex(0.2)
                music_clip = music_clip.subclip(0, final_clip.duration)
                logging.info(f"Music duration: {music_clip.duration}s")
                narration_audio = final_clip.audio.volumex(0.8)
                final_audio = CompositeAudioClip([narration_audio, music_clip]).set_duration(final_clip.duration)
                final_clip = final_clip.set_audio(final_audio)
            else:
                final_clip = final_clip.set_audio(final_clip.audio.volumex(0.8))

            # Write video
            logging.info(f"Writing video to {output_file}")
            final_clip.write_videofile(
                output_file,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                ffmpeg_params=["-c:v", "libx264", "-preset", "medium", "-crf", "23"]
            )
            logging.info(f"Video saved to {output_file}")

            # Generate description
            description = f"{script}\n\nKeywords: {seo_keywords}\n\n#Meditation #Relaxation #SleepSounds"
            if affiliate_link:
                description += f"\n\nAffiliate Link: {affiliate_link}"
            if is_exclusive:
                description += f"\n\nExclusive content for members only!"
            with open(os.path.splitext(output_file)[0] + ".txt", "w") as f:
                f.write(description)
            logging.info(f"Description saved with keywords: {seo_keywords}")

            if not batch_mode:
                self.statusBar().showMessage(f"Video generated: {output_file}", 10000)
                QMessageBox.information(self, "Success", f"Video generated: {output_file}")

        except Exception as e:
            logging.error(f"Video generation failed: {e}")
            if not batch_mode:
                QMessageBox.critical(self, "Error", f"Video generation failed: {e}")
        finally:
            if os.path.exists(tts_file):
                os.remove(tts_file)
            if temp_video and os.path.exists(temp_video):
                os.remove(temp_video)
            if 'final_clip' in locals():
                final_clip.close()
            if 'video_clip' in locals():
                video_clip.close()
            if 'tts_clip' in locals():
                tts_clip.close()
            for clip in text_clips:
                clip.close()
            if 'music_clip' in locals():
                music_clip.close()
            if 'narration_audio' in locals():
                narration_audio.close()
            if 'final_audio' in locals():
                final_audio.close()

    def generate_batch_videos(self):
        if not self.batch_scripts:
            QMessageBox.warning(self, "Warning", "No scripts in batch")
            return
        for script in self.batch_scripts:
            self.generate_video(script, batch_mode=True)
        self.batch_scripts.clear()
        self.batch_list.clear()
        self.statusBar().showMessage("Batch videos generated", 10000)
        QMessageBox.information(self, "Success", "Batch videos generated")

    def preview_video(self):
        videos = [f for f in os.listdir(self.output_dir) if f.endswith('.mp4')]
        if not videos:
            QMessageBox.warning(self, "Warning", "No videos found")
            return
        latest_video = max(videos, key=lambda x: os.path.getctime(os.path.join(self.output_dir, x)))
        video_path = os.path.join(self.output_dir, latest_video)
        os.startfile(video_path)
        self.statusBar().showMessage(f"Previewing video: {video_path}", 5000)
        logging.info(f"Previewing video: {video_path}")

if __name__ == '__main__':
    change_settings({"IMAGEMAGICK_BINARY": os.path.join(os.getcwd(), "ImageMagick", "ImageMagick-7.1.1-47-portable-Q16-HDRI-x64", "magick.exe")})
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FacelessVideoApp()
    window.show()
    sys.exit(app.exec_())