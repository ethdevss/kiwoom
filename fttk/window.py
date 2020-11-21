from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import *


class Window(QMainWindow):
    def __init__(self, hts):
        super().__init__()
        self.hts = hts
        self.init_window()

    def init_window(self):
        self.init_ui()

    def create_label(self):
        self.set_title_label()
        self.ma_label()
        self.code_name_label()
        self.tick_time_label()
        self.time_label()
        self.program_exit_time_label()
        self.profit_tick_label()
        self.loss_tick_label()
        self.quantity_label()
        self.maximum_profit_label()
        self.maximum_loss_label()
        self.skip_candle_label()
        self.start_time_label()
        self.switching_strategy_label()
        self.stop_loss_candle_count_label()

    def create_text_box(self):
        self.ma_diff_box = self.set_diff_text_box()
        self.code_text_box = self.set_code_text_box()
        self.tick_text_box = self.set_tick_text_box()
        self.time_text_box = self.set_time_text_box()
        self.exit_time_box = self.set_exit_time_box()
        self.profit_tick_box = self.set_profit_tick_box()
        self.loss_tick_box = self.set_loss_tick_box()
        self.quantity_box = self.set_quantity_box()
        self.skip_candle_box = self.set_skip_candle_box()
        self.start_time_box = self.set_start_time_box()
        self.maximum_profit_box = self.set_maximum_profit_box()
        self.maximum_loss_box = self.set_maximum_loss_tick()
        self.switching_strategy_box = self.set_switching_strategy_box()
        self.stop_loss_candle_count_box = self.set_stop_loss_candle_count_box()

    def set_event_driven(self):
        self.ma_diff_box.textChanged.connect(self.set_ma_diff)
        self.code_text_box.textChanged.connect(self.set_code)
        self.tick_text_box.textChanged.connect(self.set_tick_unit)
        self.time_text_box.textChanged.connect(self.set_time_unit)
        self.exit_time_box.textChanged.connect(self.set_exit_time)
        self.profit_tick_box.textChanged.connect(self.set_profit_tick)
        self.loss_tick_box.textChanged.connect(self.set_loss_tick)
        self.quantity_box.textChanged.connect(self.set_quantity)
        self.skip_candle_box.textChanged.connect(self.set_skip_candle)
        self.start_time_box.textChanged.connect(self.set_start_time)
        self.maximum_profit_box.textChanged.connect(self.set_maximum_profit)
        self.maximum_loss_box.textChanged.connect(self.set_maximum_loss)
        self.switching_strategy_box.textChanged.connect(self.set_switching_strategy)
        self.stop_loss_candle_count_box.textChanged.connect(self.set_stop_loss_candle_count)

    def set_ma_diff(self):
        try:
            ma = self.ma_diff_box.text()
            self.hts.set_basis_ma(float(ma))
        except ValueError:
            pass

    def set_code(self):
        symbol = self.code_text_box.text()
        self.hts.set_code_symbol(symbol)

    def set_tick_unit(self):
        try:
            tick_unit = self.tick_text_box.text()
            self.hts.set_tick_unit(int(tick_unit))
        except ValueError:
            pass

    def set_time_unit(self):
        try:
            time_unit = self.time_text_box.text()
            self.hts.set_time_unit(int(time_unit))
        except ValueError:
            pass

    def set_exit_time(self):
        try:
            exit_time = self.exit_time_box.text()
            self.hts.set_exit_time(exit_time)
        except ValueError:
            pass

    def set_profit_tick(self):
        try:
            profit_tick = self.profit_tick_box.text()
            self.hts.set_profit_tick(int(profit_tick))
        except ValueError:
            pass

    def set_loss_tick(self):
        try:
            loss_tick = self.loss_tick_box.text()
            self.hts.set_loss_tick(int(loss_tick))
        except ValueError:
            pass

    def set_quantity(self):
        try:
            quantity = self.quantity_box.text()
            self.hts.set_quantity(int(quantity))
        except ValueError:
            pass

    def set_skip_candle(self):
        try:
            skip_candle = self.skip_candle_box.text()
            self.hts.set_skip_candle(int(skip_candle))
        except ValueError:
            pass

    def set_start_time(self):
        try:
            start_time = self.start_time_box.text()
            self.hts.set_start_time(start_time)
        except ValueError:
            pass

    def set_maximum_profit(self):
        try:
            maximum_profit = self.maximum_profit_box.text()
            self.hts.set_maximum_profit(int(maximum_profit))
        except ValueError:
            pass

    def set_maximum_loss(self):
        try:
            maximum_loss = self.maximum_loss_box.text()
            self.hts.set_maximum_loss(int(maximum_loss))
        except ValueError:
            pass

    def set_switching_strategy(self):
        try:
            switching_strategy = self.switching_strategy_box.text()
            self.hts.set_switching_strategy(int(switching_strategy))
        except ValueError:
            pass

    def set_stop_loss_candle_count(self):
        try:
            stop_loss_candle_count = self.stop_loss_candle_count_box.text()
            self.hts.set_stop_loss_candle_count(int(stop_loss_candle_count))
        except ValueError:
            pass

    def create_button(self):
        self.start_trade_button()
        self.stop_trade_button()

    def init_ui(self):
        self.setMinimumSize(QSize(640, 580))
        self.create_label()
        self.create_text_box()
        self.create_button()
        self.set_event_driven()

    def set_title_label(self):
        label = QLabel(self)
        label.move(10, 10)
        label.resize(500, 50)
        label.setText("키움증권 선물 자동매매 프로그램")
        return label

    def set_code_text_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 70)
        textbox.resize(150, 40)
        return textbox

    def set_diff_text_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 120)
        textbox.resize(150, 40)
        return textbox

    def set_tick_text_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 170)
        textbox.resize(150, 40)
        return textbox

    def set_time_text_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 220)
        textbox.resize(150, 40)
        return textbox

    def set_skip_candle_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 270)
        textbox.resize(150, 40)
        return textbox

    def set_start_time_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 320)
        textbox.resize(150, 40)
        return textbox

    def set_quantity_box(self):
        textbox = QLineEdit(self)
        textbox.move(440, 220)
        textbox.resize(150, 40)
        return textbox

    def set_maximum_profit_box(self):
        textbox = QLineEdit(self)
        textbox.move(440, 270)
        textbox.resize(150, 40)
        return textbox

    def set_maximum_loss_tick(self):
        textbox = QLineEdit(self)
        textbox.move(440, 320)
        textbox.resize(150, 40)
        return textbox

    def set_switching_strategy_box(self):
        textbox = QLineEdit(self)
        textbox.move(120, 370)
        textbox.resize(150, 40)
        return textbox

    def set_stop_loss_candle_count_box(self):
        textbox = QLineEdit(self)
        textbox.move(440, 370)
        textbox.resize(150, 40)
        return textbox

    def set_exit_time_box(self):
        exit_time_box = QLineEdit(self)
        exit_time_box.move(440, 70)
        exit_time_box.resize(150, 40)
        return exit_time_box

    def set_profit_tick_box(self):
        textbox = QLineEdit(self)
        textbox.move(440, 120)
        textbox.resize(150, 40)
        return textbox

    def set_loss_tick_box(self):
        textbox = QLineEdit(self)
        textbox.move(440, 170)
        textbox.resize(150, 40)
        return textbox

    def code_name_label(self):
        label = QLabel(self)
        label.move(10, 70)
        label.resize(120, 40)
        label.setText("종목코드")
        return label

    def program_exit_time_label(self):
        label = QLabel(self)
        label.move(340, 70)
        label.resize(230, 40)
        label.setText('종료 시간')
        return label

    def profit_tick_label(self):
        label = QLabel(self)
        label.move(340, 120)
        label.resize(230, 40)
        label.setText('익절 틱')
        return label

    def loss_tick_label(self):
        label = QLabel(self)
        label.move(340, 170)
        label.resize(230, 40)
        label.setText('손절 틱')
        return label

    def quantity_label(self):
        label = QLabel(self)
        label.move(340, 220)
        label.resize(230, 40)
        label.setText('수량')
        return label

    def maximum_profit_label(self):
        label = QLabel(self)
        label.move(340, 270)
        label.resize(230, 40)
        label.setText('최대 익절 금액')
        return label

    def maximum_loss_label(self):
        label = QLabel(self)
        label.move(340, 320)
        label.resize(230, 40)
        label.setText('최대 손절 금액')
        return label

    def ma_label(self):
        label = QLabel(self)
        label.move(10, 120)
        label.resize(120, 40)
        label.setText("MA 기울기")
        return label

    def tick_time_label(self):
        label = QLabel(self)
        label.move(10, 170)
        label.resize(120, 40)
        label.setText("틱봉 단위")
        return label

    def time_label(self):
        label = QLabel(self)
        label.move(10, 220)
        label.resize(120, 40)
        label.setText("분봉 단위")
        return label

    def skip_candle_label(self):
        label = QLabel(self)
        label.move(10, 270)
        label.resize(120, 40)
        label.setText('건너뛰는 봉 개수: ')
        return label

    def start_time_label(self):
        label = QLabel(self)
        label.move(10, 320)
        label.resize(120, 40)
        label.setText('시작 시간: ')
        return label

    def switching_strategy_label(self):
        label = QLabel(self)
        label.move(10, 370)
        label.resize(120, 40)
        label.setText('스위칭 전략 사용: ')
        return label

    def stop_loss_candle_count_label(self):
        label = QLabel(self)
        label.move(340, 370)
        label.resize(230, 40)
        label.setText('손절 봉 개수: ')
        return label

    def start_trade_button(self):
        start_trade_button = QPushButton('START', self)
        start_trade_button.move(200, 470)
        start_trade_button.resize(120, 40)
        start_trade_button.clicked.connect(self.hts.start_trade)
        return start_trade_button

    def stop_trade_button(self):
        stop_trade_button = QPushButton('STOP', self)
        stop_trade_button.move(470, 470)
        stop_trade_button.resize(120, 40)
        stop_trade_button.clicked.connect(self.hts.stop_trade)
        return stop_trade_button
