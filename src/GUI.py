import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDockWidget, QStatusBar, QAction, QDoubleSpinBox, QRadioButton, QStackedWidget, QComboBox, QCheckBox
from PyQt5.QtGui import QPainter, QFont, QPixmap, QImage, QDesktopServices
from PyQt5.QtCore import Qt, QRect, QEvent, pyqtSignal, QThread, QTimer, QUrl
from PyQt5.QtWidgets import QFileDialog
import random
import pickle



class GridWidget(QWidget):
    # 定义信号
    data_updated = pyqtSignal(int, float, float, float, float, float, float)
    setting_updated = pyqtSignal(int, float, float, bool, bool)
    # 初始化
    def __init__(self, n, parent=None):
        super().__init__(parent)
        self.n = n
        self.grid_size = 800  # 固定区域的大小
        self.cell_size = self.grid_size // self.n
        self.spins = np.ones((self.n, self.n))
        self.is_black = True  # 初始状态为黑色
        self.start_simulation = False
        self.update_option = True  # 默认连续更新
        self.bound_option = True  # 默认周期边界条件

        # 数据初始化
        self.steps = 0
        self.temperature = 0.01
        self.magnetic = 0.00
        self.J_interaction = np.random.normal(0, 1, size=(self.n, self.n, 4))  # 初始化随机相互作用 J_{ij} (高斯分布) 4个近邻相互作用
        self.energy = -0.5 * np.sum(self.spins * (self.J_interaction[:, :, 0] * np.roll(self.spins, 1, axis=0) + \
                                                    self.J_interaction[:, :, 1] * np.roll(self.spins, -1, axis=0) + \
                                                    self.J_interaction[:, :, 2] * np.roll(self.spins, 1, axis=1) + \
                                                    self.J_interaction[:, :, 3] * np.roll(self.spins, -1, axis=1))) - self.magnetic * np.sum(self.spins)
        self.magnetization = np.sum(self.spins) / self.n**2
        self.magnetizations = []  # 记录总磁化强度
        self.energies = [] # 记录总能量

         # 定时器每秒更新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_period)
        self.timer.start(500)

    def paintEvent(self, event):
        painter = QPainter(self)
        for i in range(self.n):
            for j in range(self.n):
                if self.spins[i, j] == 1:
                    color = Qt.black
                else:
                    color = Qt.white
                painter.fillRect(QRect(j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size), color)
            

    # 更新 n 值
    def set_grid_size(self, n):
        self.n = n
        self.cell_size = self.grid_size // self.n
        self.spins = np.ones((self.n, self.n))
        self.J_interaction = np.random.normal(0, 1, size=(self.n, self.n, 4))  # 初始化随机相互作用 J_{ij} (高斯分布) 4个近邻相互作用
        self.energy = -0.5 * np.sum(self.spins * (self.J_interaction[:, :, 0] * np.roll(self.spins, 1, axis=0) + \
                                                    self.J_interaction[:, :, 1] * np.roll(self.spins, -1, axis=0) + \
                                                    self.J_interaction[:, :, 2] * np.roll(self.spins, 1, axis=1) + \
                                                    self.J_interaction[:, :, 3] * np.roll(self.spins, -1, axis=1))) - self.magnetic * np.sum(self.spins)
        self.magnetization = np.sum(self.spins) / self.n**2
        self.steps = 0
        self.magnetizations = []  # 记录总磁化强度
        self.energies = [] # 记录总能量
        self.data_updated.emit(0, self.energy, 0.0000, 0.0000, self.magnetization, 0.0000, 0.0000)
        # 触发重绘
        self.update()
        

    # 更新 temperature 值
    def set_temperature(self, temperature):
        self.temperature = temperature
        # print('temperature:', temperature)

    # 更新 magnetic 值
    def set_magnetic(self, magnetic):
        self.magnetic = magnetic
        # print('magnetic:', magnetic)
    
    # 更新选项
    def set_update_option(self, update_flag):
        self.update_option = update_flag

    # 更新边界条件
    def set_bound_option(self, bound_flag):
        self.bound_option = bound_flag
    
    # align按钮
    def align(self):
        self.is_black = not self.is_black
        self.spins = np.ones((self.n, self.n)) if self.is_black else -np.ones((self.n, self.n))
        self.energy = -0.5 * np.sum(self.spins * (self.J_interaction[:, :, 0] * np.roll(self.spins, 1, axis=0) + \
                                                    self.J_interaction[:, :, 1] * np.roll(self.spins, -1, axis=0) + \
                                                    self.J_interaction[:, :, 2] * np.roll(self.spins, 1, axis=1) + \
                                                    self.J_interaction[:, :, 3] * np.roll(self.spins, -1, axis=1))) - self.magnetic * np.sum(self.spins)
        self.magnetization = np.sum(self.spins) / self.n**2
        self.data_updated.emit(self.steps, self.energy, np.mean(self.energies), np.std(self.energies), self.magnetization, np.mean(self.magnetizations), np.std(self.magnetizations))
        # 触发重绘
        self.update()
        
    
    # randomize按钮
    def randomize(self):
        # 随机设置每个格点的颜色
        for i in range(self.n):
            for j in range(self.n):
                self.spins[i, j] = 1 if random.random() < 0.5 else -1
        self.energy = -0.5 * np.sum(self.spins * (self.J_interaction[:, :, 0] * np.roll(self.spins, 1, axis=0) + \
                                                    self.J_interaction[:, :, 1] * np.roll(self.spins, -1, axis=0) + \
                                                    self.J_interaction[:, :, 2] * np.roll(self.spins, 1, axis=1) + \
                                                    self.J_interaction[:, :, 3] * np.roll(self.spins, -1, axis=1))) - self.magnetic * np.sum(self.spins)
        self.magnetization = np.sum(self.spins) / self.n**2
        self.data_updated.emit(self.steps, self.energy, np.mean(self.energies), np.std(self.energies), self.magnetization, np.mean(self.magnetizations), np.std(self.magnetizations))
        # 触发重绘
        self.update()
    
    # 读取数据
    def load_data(self, data):
        self.set_grid_size(data["n"])
        self.spins = data["spins"]
        self.J_interaction = data["J_interaction"]
        self.set_temperature(data["temperature"])
        self.set_magnetic(data["magnetic"])
        self.bound_option = data["bound_option"]
        self.set_update_option(data["update_option"])
        self.steps = data["steps"]
        self.energy = data["energy"]
        self.energies = data["energies"]
        self.magnetization = data["magnetization"]
        self.magnetizations = data["magnetizations"]
        self.data_updated.emit(self.steps, self.energy, np.mean(self.energies), np.std(self.energies), self.magnetization, np.mean(self.magnetizations), np.std(self.magnetizations))
        self.setting_updated.emit(self.n, self.temperature, self.magnetic, self.update_option, self.bound_option)
        

    # 模拟
    def simulation_by_step(self):
        if not self.start_simulation:
            return  # 如果模拟未启动，直接返回

        # 随机选择一个结点
        i, j = np.random.randint(0, self.n, size=2)

        if self.bound_option:
            # 计算能量变化
            delta_E = 2 * self.spins[i, j] * \
                    (self.J_interaction[i, j, 0] * self.spins[(i + 1) % self.n, j] + \
                    self.J_interaction[i, j, 1] * self.spins[(i - 1) % self.n, j] + \
                    self.J_interaction[i, j, 2] * self.spins[i, (j + 1) % self.n] + \
                    self.J_interaction[i, j, 3] * self.spins[i, (j - 1) % self.n] + \
                    self.magnetic)
        else:
            delta_E = 0
            neighbors = [((i + 1) % self.n, j), ((i - 1) % self.n, j), (i, (j + 1) % self.n), (i, (j - 1) % self.n)]
            # 非周期性边界条件：检查邻居是否在网格内
            valid_neighbors = []
            for idx, (ni, nj) in enumerate(neighbors):
                if 0 <= ni < self.n and 0 <= nj < self.n:
                    valid_neighbors.append((ni, nj, idx))  # 记录有效邻居及其索引
            # 计算能量变化
            for ni, nj, idx in valid_neighbors:
                delta_E += self.J_interaction[i, j, idx] * self.spins[ni, nj]
            delta_E = 2 * self.spins[i, j] * (delta_E + self.magnetic)

        # Metropolis准则
        if delta_E < 0 or np.random.rand() < np.exp(-delta_E / self.temperature):
            self.spins[i, j] *= -1  # 翻转自旋
            self.steps += 1
        # 更新
        if self.steps % 300 == 0:
            # 计算总能量和总磁化强度
            self.energy = -0.5 * np.sum(self.spins * (self.J_interaction[:, :, 0] * np.roll(self.spins, 1, axis=0) + \
                                                    self.J_interaction[:, :, 1] * np.roll(self.spins, -1, axis=0) + \
                                                    self.J_interaction[:, :, 2] * np.roll(self.spins, 1, axis=1) + \
                                                    self.J_interaction[:, :, 3] * np.roll(self.spins, -1, axis=1))) - self.magnetic * np.sum(self.spins)
            self.magnetization = np.sum(self.spins) / self.n**2
            self.energies.append(self.energy)
            self.magnetizations.append(self.magnetization)
            if self.update_option:
                self.update()
                # 发射信号
                self.data_updated.emit(self.steps, self.energy, np.mean(self.energies), np.std(self.energies), self.magnetization, np.mean(self.magnetizations), np.std(self.magnetizations))

    # 定时更新
    def update_period(self):
        self.update()
        # 计算总能量和总磁化强度
        self.energy = -0.5 * np.sum(self.spins * (self.J_interaction[:, :, 0] * np.roll(self.spins, 1, axis=0) + \
                                                self.J_interaction[:, :, 1] * np.roll(self.spins, -1, axis=0) + \
                                                self.J_interaction[:, :, 2] * np.roll(self.spins, 1, axis=1) + \
                                                self.J_interaction[:, :, 3] * np.roll(self.spins, -1, axis=1))) - self.magnetic * np.sum(self.spins)
        self.magnetization = np.sum(self.spins) / self.n**2
        # 发射信号
        self.data_updated.emit(self.steps, self.energy, np.mean(self.energies), np.std(self.energies), self.magnetization, np.mean(self.magnetizations), np.std(self.magnetizations))
        
    # 清空记录
    def reset(self):
        self.steps = 0
        self.energies = []
        self.magnetizations = []

            
        
        


# 模拟线程
class SimulationThread(QThread):
    def __init__(self, grid_widget):
        super().__init__()
        self.grid_widget = grid_widget

    def run(self):
        while self.grid_widget.start_simulation:
            self.grid_widget.simulation_by_step()  # 每次只运行一步模拟



class SubWindow(QWidget):
    # 传递新的n值
    lattice_size_changed = pyqtSignal(int)
    # 传递新的temperature值
    temperature_changed = pyqtSignal(float)
    # 传递新的magnetic值
    magnetic_changed = pyqtSignal(float)
    # 传递align信号
    align_grid_requested = pyqtSignal()
    # 传递randomize信号
    randomize_grid_requested = pyqtSignal()
    # 传递start/stop信号
    start_simulation = pyqtSignal(bool)
    # 传递更新选项
    update_option = pyqtSignal(bool)
    # 传递边界条件选项
    bound_option = pyqtSignal(bool)
    # 传递reset信号
    reset_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")


        main_layout = QVBoxLayout()

        # 上半部分
        top_widget = QWidget()
        top_widget.setFixedSize(250, 300)
        top_widget.setStyleSheet("background-color: transparent;")
        top_layout = QGridLayout()


        # 按键
        self.button = QPushButton("Start", self)
        self.button.setStyleSheet("""
            QPushButton {
                border: 2px solid skyblue;  /* 设置边框为天蓝色 */
                border-radius: 10px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
            QPushButton:hover {
                border: 2px solid lightblue;  /* 鼠标悬停时边框变为更浅的蓝色 */
                background-color: #f0f8ff;    /* 鼠标悬停时背景颜色变为更浅的蓝色 */
            }
        """)

        self.button.setFixedSize(100,30)
        self.button.clicked.connect(self.toggle)


        # 温度标签
        self.templabel = QLabel("Temperature")
        font = QFont()
        font.setPointSize(9)
        self.templabel.setFont(font)
        self.templabel.setStyleSheet("background-color: transparent;")
        self.templabel.setFixedSize(100,30)
        # 温度数值
        self.temp_spin_box = QDoubleSpinBox()
        self.temp_spin_box.setFixedSize(100,30)
        self.temp_spin_box.setRange(0.01, 100.0)  # 设置最小值和最大值
        self.temp_spin_box.setSingleStep(0.02)      # 设置步长
        self.temp_spin_box.setValue(0.00)           # 设置默认值
        self.temp_spin_box.setDecimals(2)           # 保留2位小数
        self.temp_spin_box.setStyleSheet("QDoubleSpinBox { background-color: white; }")
        self.temp_spin_box.valueChanged.connect(self.on_temperature_changed)


        # 磁场标签
        self.magnlabel = QLabel("Magnetic")
        self.magnlabel.setFont(font)
        self.magnlabel.setStyleSheet("background-color: transparent;")
        self.magnlabel.setFixedSize(80,30)
        # 磁场数值
        self.magn_spin_box = QDoubleSpinBox()
        self.magn_spin_box.setFixedSize(100,30)
        self.magn_spin_box.setRange(-50.0, 50.0)  # 设置最小值和最大值
        self.magn_spin_box.setSingleStep(0.05)      # 设置步长
        self.magn_spin_box.setValue(0.00)           # 设置默认值
        self.magn_spin_box.setDecimals(2)           # 保留2位小数
        self.magn_spin_box.setStyleSheet("QDoubleSpinBox { background-color: white; }")
        self.magn_spin_box.valueChanged.connect(self.on_magnetic_changed)


        # 更新选项
        self.continuous_button = QRadioButton('Update continuously')
        self.continuous_button.setStyleSheet("background-color: transparent;")
        self.continuous_button.setChecked(True)
        self.periodic_button = QRadioButton('Update periodically')
        self.periodic_button.setStyleSheet("background-color: transparent;")
        self.continuous_button.toggled.connect(self.on_update_changed)


        top_layout.addWidget(self.button, 0, 0, 1, 2, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.templabel, 1, 0, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.temp_spin_box, 1, 1, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.magnlabel, 2, 0, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.magn_spin_box, 2, 1, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.continuous_button, 3, 0, 1, 2, alignment=Qt.AlignHCenter)
        top_layout.addWidget(self.periodic_button, 4, 0, 1, 2, alignment=Qt.AlignHCenter)
        top_widget.setLayout(top_layout)

        main_layout.addWidget(top_widget)
        


        # 下半部分
        self.bottom_widget = QStackedWidget()
        self.bottom_widget.setStyleSheet("background-color: transparent;")
        self.bottom_widget.setFixedSize(250, 200)


        # 设置界面
        settings_widget = QWidget()

        # 初始化
        self.Align_button = QPushButton("Align")
        self.Align_button.setFixedSize(100,30)
        self.Align_button.setStyleSheet("""
            QPushButton {
                border: 2px solid skyblue;  /* 设置边框为天蓝色 */
                border-radius: 10px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
            QPushButton:hover {
                border: 2px solid lightblue;  /* 鼠标悬停时边框变为更浅的蓝色 */
                background-color: #f0f8ff;    /* 鼠标悬停时背景颜色变为更浅的蓝色 */
            }
        """)
        self.Align_button.clicked.connect(self.align)

        self.Randomize_button = QPushButton("Randomize")
        self.Randomize_button.setFixedSize(100,30)
        self.Randomize_button.setStyleSheet("""
            QPushButton {
                border: 2px solid skyblue;  /* 设置边框为天蓝色 */
                border-radius: 10px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
            QPushButton:hover {
                border: 2px solid lightblue;  /* 鼠标悬停时边框变为更浅的蓝色 */
                background-color: #f0f8ff;    /* 鼠标悬停时背景颜色变为更浅的蓝色 */
            }
        """)
        self.Randomize_button.clicked.connect(self.randomize)


        # 大小选择
        self.Lattice_label = QLabel("Lattice size")
        
        font.setPointSize(9)
        self.Lattice_label.setFont(font)

        self.Lattice_choice = QComboBox()
        self.Lattice_choice.setFixedSize(80, 20)
        self.Lattice_choice.addItem('2')
        self.Lattice_choice.addItem('4')
        self.Lattice_choice.addItem('5')
        self.Lattice_choice.addItem('8')
        self.Lattice_choice.addItem('10')
        self.Lattice_choice.addItem('16')
        self.Lattice_choice.addItem('20')
        self.Lattice_choice.addItem('25')
        self.Lattice_choice.addItem('40')
        self.Lattice_choice.addItem('50')
        self.Lattice_choice.addItem('80')
        self.Lattice_choice.addItem('100')
        self.Lattice_choice.addItem('200')
        self.Lattice_choice.addItem('400')
        self.Lattice_choice.setStyleSheet("background-color: white;")
        self.Lattice_choice.setCurrentIndex(11)
        self.Lattice_choice.currentIndexChanged.connect(self.on_lattice_changed)

        # 边界条件选择
        self.bound_box = QCheckBox('Periodic boundaries')
        self.bound_box.setChecked(True)
        self.bound_box.stateChanged.connect(self.on_bound_changed)


        settings_layout = QGridLayout()
        settings_layout.addWidget(self.Align_button, 0, 0)
        settings_layout.addWidget(self.Randomize_button, 0, 1)
        settings_layout.addWidget(self.Lattice_label, 1, 0, alignment=Qt.AlignLeft)
        settings_layout.addWidget(self.Lattice_choice, 1, 1, alignment=Qt.AlignRight)
        settings_layout.addWidget(self.bound_box, 2, 0, 1, 2, alignment=Qt.AlignHCenter)


        settings_widget.setLayout(settings_layout)
        self.bottom_widget.addWidget(settings_widget)



        # 数据界面
        data_widget = QWidget()
        
        self.Steps_label = QLabel('Steps:')
        self.Steps_data = QLabel('0')
        self.Energy_label = QLabel('Energy:')
        self.Energy_data = QLabel(f'{self.parent().grid_widget.energy:.4f}')
        self.AverageE_label = QLabel('Average E:')
        self.AverageE_data = QLabel('0.0000')
        self.SigmaE_label = QLabel('Sigma E:')
        self.SigmaE_data = QLabel('0.0000')

        self.Magnetization_label = QLabel('Magnetization:')
        self.Magnetization_data = QLabel(f'{self.parent().grid_widget.magnetization:.4f}')
        self.AverageM_label = QLabel('Average M:')
        self.AverageM_data = QLabel('0.0000')
        self.SigmaM_label = QLabel('Sigma M:')
        self.SigmaM_data = QLabel('0.0000')

        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("""
            QPushButton {
                border: 2px solid skyblue;  /* 设置边框为天蓝色 */
                border-radius: 10px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
            QPushButton:hover {
                border: 2px solid lightblue;  /* 鼠标悬停时边框变为更浅的蓝色 */
                background-color: #f0f8ff;    /* 鼠标悬停时背景颜色变为更浅的蓝色 */
            }
        """)
        self.reset_button.setFixedSize(100,25)
        self.reset_button.clicked.connect(self.reset)


        data_layout = QGridLayout()
        data_layout.addWidget(self.Steps_label, 0, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.Steps_data, 0, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.Energy_label, 1, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.Energy_data, 1, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.AverageE_label, 2, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.AverageE_data, 2, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.SigmaE_label, 3, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.SigmaE_data, 3, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.Magnetization_label, 4, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.Magnetization_data, 4, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.AverageM_label, 5, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.AverageM_data, 5, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.SigmaM_label, 6, 0, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.SigmaM_data, 6, 1, alignment=Qt.AlignHCenter)
        data_layout.addWidget(self.reset_button, 7, 0, 1, 2, alignment=Qt.AlignHCenter)

        data_widget.setLayout(data_layout)

        self.bottom_widget.addWidget(data_widget)

        # 绑定信号
        self.parent().grid_widget.data_updated.connect(self.update_data_labels)

        self.bottom_widget.setCurrentIndex(0)

        main_layout.addWidget(self.bottom_widget)


        # 按钮布局
        button_layout = QHBoxLayout()
        # 添加statusbar
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet('background-color: transparent;')
        self.statusbar.setFixedSize(250,30)
        
        self.settings_button = QPushButton('Settings')
        self.settings_button.setFixedSize(100, 20)
        self.settings_button.clicked.connect(lambda: self.switch_page(0)) 
        self.settings_button.setStyleSheet("""
            QPushButton { 
                border-radius: 5px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
        """)
        self.statusbar.addWidget(self.settings_button)

        self.data_button = QPushButton('Data')
        self.data_button.setFixedSize(100, 20)
        self.data_button.clicked.connect(lambda: self.switch_page(1))
        self.data_button.setStyleSheet("""
            QPushButton { 
                border-radius: 5px;         /* 设置圆角 */
                background-color: transparent;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
        """)
        self.statusbar.addWidget(self.data_button)
        button_layout.addWidget(self.statusbar)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    

    # 开始/停止按钮
    def toggle(self):
        if self.button.text() == 'Start':
            self.start_simulation.emit(True)
            self.button.setText('Stop')
        else:
            self.start_simulation.emit(False)
            self.button.setText('Start')
    
    # lattice_size改变
    def on_lattice_changed(self):
        # 获取当前选择的 n 值
        n = int(self.Lattice_choice.currentText())
        # 发射信号
        self.lattice_size_changed.emit(n)
    
    # temperature改变
    def on_temperature_changed(self):
        temperature = self.temp_spin_box.value()
        self.temperature_changed.emit(temperature)
        # print('temperature:', temperature)

    # magnetic改变
    def on_magnetic_changed(self):
        magnetic = self.magn_spin_box.value()
        self.magnetic_changed.emit(magnetic)
        # print('magnetic:', magnetic)

    # 更新选项改变
    def on_update_changed(self):
        self.update_option.emit(self.continuous_button.isChecked())

    # 周期边界条件改变
    def on_bound_changed(self):
        self.bound_option.emit(self.bound_box.isChecked())
    
    # align按钮
    def align(self):
        self.align_grid_requested.emit()

    # randomize按钮
    def randomize(self):
        self.randomize_grid_requested.emit()

    # 更新数据界面的 label
    def update_data_labels(self, steps, energy, avg_energy, sigma_energy, magnetization, avg_magnetization, sigma_magnetization):
        self.Steps_data.setText(f'{steps}')
        self.Energy_data.setText(f'{energy:.4f}')
        self.AverageE_data.setText(f'{avg_energy:.4f}')
        self.SigmaE_data.setText(f'{sigma_energy:.4f}')
        self.Magnetization_data.setText(f'{magnetization:.4f}')
        self.AverageM_data.setText(f'{avg_magnetization:.4f}')
        self.SigmaM_data.setText(f'{sigma_magnetization:.4f}')
    
    # 重置按钮
    def reset(self):
        self.reset_signal.emit()
        self.Steps_data.setText('0')
        self.AverageE_data.setText('0.0000')
        self.SigmaE_data.setText('0.0000')
        self.AverageM_data.setText('0.0000')
        self.SigmaM_data.setText('0.0000')
        
    
    # 更新设置
    def update_settings(self, n, temperature, magnetic, update_option, bound_option):
        self.temp_spin_box.setValue(temperature)
        self.magn_spin_box.setValue(magnetic)
        self.continuous_button.setChecked(update_option)
        self.periodic_button.setChecked(not update_option)
        # 断开信号连接
        self.Lattice_choice.blockSignals(True)
        self.Lattice_choice.setCurrentIndex(self.Lattice_choice.findText(str(n)))
        # 重新连接信号
        self.Lattice_choice.blockSignals(False)
        self.bound_box.setChecked(bound_option)


    # 切换 QStackedWidget 界面，并更新按钮样式
    def switch_page(self, index):
        self.bottom_widget.setCurrentIndex(index)
        if index == 0:
            self.settings_button.setStyleSheet("""
            QPushButton { 
                border-radius: 5px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
        """)
            self.data_button.setStyleSheet("""
            QPushButton { 
                border-radius: 5px;         /* 设置圆角 */
                background-color: transparent;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
        """)
        else:
            self.settings_button.setStyleSheet("""
            QPushButton { 
                border-radius: 5px;         /* 设置圆角 */
                background-color: transparent;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
        """)
            self.data_button.setStyleSheet("""
            QPushButton { 
                border-radius: 5px;         /* 设置圆角 */
                background-color: white;    /* 设置背景颜色 */
                color: black;               /* 设置文字颜色 */
            }
        """)

           



class MainWindow(QMainWindow):
    def __init__(self, n):
        super().__init__()
        self.setWindowTitle("Spin Glass Model -- Yuxi_Qian(PB22020458)")
        self.setGeometry(150, 150, 800, 800)

        # 创建菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")

        # 创建 "打开文件" 动作
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open)
        file_menu.addAction(open_action)

        # 创建 "保存图片" 动作
        save_pic_action = QAction("Save picture", self)
        save_pic_action.triggered.connect(self.save_pic)
        file_menu.addAction(save_pic_action)

        # 创建 "保存数据" 动作
        save_data_action = QAction("Save Data", self)
        save_data_action.triggered.connect(self.save_data)
        file_menu.addAction(save_data_action)

        # 创建 "退出" 动作
        exit_action = QAction("Close", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 创建 "我的Github" 动作
        author_action = QAction("Author's GitHub", self)
        author_action.triggered.connect(self.open_author_url)
        edit_menu.addAction(author_action)

        # 主窗口中的网格
        self.grid_widget = GridWidget(n)
        self.setCentralWidget(self.grid_widget)

        # 创建 SubWindow 并作为 Dock 窗口
        self.sub_window = QDockWidget(self)     
        self.sub_window.setWidget(SubWindow(self))
        self.sub_window.setFloating(True)  # 使其可以拖动
        self.sub_window.setGeometry(1000, 250, 250, 600)  # 设置初始位置
        

        # 隐藏标题栏
        self.sub_window.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.sub_window)  # 让它停靠在右侧

        # 模拟线程
        self.simulation_thread = SimulationThread(self.grid_widget)

        # 绑定信号
        self.sub_window.widget().lattice_size_changed.connect(self.update_grid_size)
        self.sub_window.widget().temperature_changed.connect(self.update_temperature)
        self.sub_window.widget().magnetic_changed.connect(self.update_magnetic)
        self.sub_window.widget().align_grid_requested.connect(self.align_grid)
        self.sub_window.widget().randomize_grid_requested.connect(self.randomize_grid)
        self.sub_window.widget().start_simulation.connect(self.simulation)
        self.sub_window.widget().update_option.connect(self.update_option)
        self.sub_window.widget().bound_option.connect(self.update_bound)
        self.sub_window.widget().reset_signal.connect(self.reset)
        self.grid_widget.data_updated.connect(self.sub_window.widget().update_data_labels)
        self.grid_widget.setting_updated.connect(self.sub_window.widget().update_settings)
        

    # 更新 GridWidget 的 n 值
    def update_grid_size(self, n):
        self.grid_widget.set_grid_size(n)
    # 更新温度
    def update_temperature(self, temperature):
        self.grid_widget.set_temperature(temperature)
    # 更新磁场
    def update_magnetic(self, magnetic):
        self.grid_widget.set_magnetic(magnetic)
    # 更新选项
    def update_option(self, update_flag):
        self.grid_widget.set_update_option(update_flag)
    # 更新边界条件
    def update_bound(self, bound_flag):
        self.grid_widget.set_bound_option(bound_flag)

    # 调用 GridWidget 的方法将所有格子变色
    def align_grid(self):
        self.grid_widget.align()

    # 调用 GridWidget 的方法将所有格子随机变色
    def randomize_grid(self):
        self.grid_widget.randomize()
    
    # 开始/停止模拟
    def simulation(self, start_flag):
        if start_flag:
            self.grid_widget.start_simulation = True
            self.simulation_thread.start()  # 启动模拟线程
        else:
            self.grid_widget.start_simulation = False
            self.simulation_thread.quit()  # 停止线程
    
    # 重置
    def reset(self):
        self.grid_widget.reset()

    # 打开文件
    def open(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,  # 父窗口
            "Load Data",  # 对话框标题
            "",  # 默认路径
            "SpinGlass Files (*.spinglass);;All Files (*)"  # 文件过滤器
        )
        if file_path:
            # 从二进制文件加载数据
            with open(file_path, "rb") as file:
                data = pickle.load(file)
            # 恢复状态
            self.grid_widget.load_data(data)
            self.grid_widget.update()  # 触发重绘
            # print(f"Data loaded from {file_path}")

    # 保存图片
    def save_pic(self):
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,  # 父窗口
            "Save Image",  # 对话框标题
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"  # 文件过滤器
        )
        if file_path:
            # 创建QPixmap对象，用于保存图像
            pixmap = QPixmap(self.grid_widget.size())
            self.grid_widget.render(pixmap)  # 将 GridWidget 的内容渲染到 QPixmap
            pixmap.save(file_path)  # 保存为图片文件
            # print(f"Image saved to {file_path}")

    # 保存数据
    def save_data(self):
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,  # 父窗口
            "Save Data",  # 对话框标题
            "",  # 默认路径
            "SpinGlass Files (*.spinglass);;All Files (*)"  # 文件过滤器
        )
        if file_path:
            # 准备数据
            data = {
                "n": self.grid_widget.n,
                "spins": self.grid_widget.spins,
                "J_interaction": self.grid_widget.J_interaction,
                "temperature": self.grid_widget.temperature,
                "magnetic": self.grid_widget.magnetic,
                "bound_option": self.grid_widget.bound_option,
                "update_option": self.grid_widget.update_option,
                "steps": self.grid_widget.steps,
                "energy": self.grid_widget.energy,
                "energies": self.grid_widget.energies,
                "magnetization": self.grid_widget.magnetization,
                "magnetizations": self.grid_widget.magnetizations
            }
            # 保存为二进制文件
            with open(file_path, "wb") as file:
                pickle.dump(data, file)
            # print(f"Data saved to {file_path}")

    def open_author_url(self):
        url = QUrl("https://github.com/lkbrain/Spin_Glass")  # 替换为实际的作者网址
        QDesktopServices.openUrl(url)


    



if __name__ == "__main__":
    app = QApplication(sys.argv)
    n = 100  # 网格的大小
    mainwindow = MainWindow(n)
    mainwindow.show()

    sys.exit(app.exec_())
