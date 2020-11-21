import sys
import mongoengine
import numpy as np
import telegram

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from fttk.model.tick import Tick, Minute
from fttk.dataframe import DataFrame
from fttk.window import Window
from mongoengine.document import Document

#kei_id = "647993581"
kei_id = "784845620" # real kei


class GlobalKiwoom(QAxWidget, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setControl("KFOPENAPI.KFOpenAPICtrl.1")
        self.OnEventConnect.connect(self.on_event_connect)
        self.OnReceiveTrData.connect(self.on_receive_tr_data)
        self.OnReceiveRealData.connect(self.on_receive_real_data)
        self.OnReceiveMsg.connect(self.on_receive_msg)
        self.OnReceiveChejanData.connect(self.on_receive_chejan_data)
        self.future_item_list = []
        self.future_code_list = []
        self.tick_count = {}
        self.screen_number = 1000
        self.account_numbers = []
        self.current_position = {}
        self.stop_loss = {}
        self.basis_ma = 0
        self.code_symbol = ''
        self.basis_tick_unit = 0
        self.basis_time_unit = 0
        self.exit_time = ''
        self.start_time = ''
        self.profit_tick = 0
        self.loss_tick = 0
        self.tick_unit = {}
        self.quantity = 0

        self.is_starting_time = False
        self.is_just_position_close = False
        self.current_skip_candle = 0
        self.skip_candle = 0

        self.maximum_profit = 0
        self.maximum_loss = 0
        self.current_profit_loss = 0 # 실현손익이 +인 상황에서는 0보다 큰 +, -인 상황에서는 0보다 작은 -

        self.switching_strategy = 0

        self.stop_loss_candle_count = 0

        self.current_entry_price = {}

        self.current_tick_close = 0
        self.current_tick_high = 0
        self.current_tick_low = 0
        self.current_tick_open = 0

        self.current_minute_close = 0
        self.current_minute_high = 0
        self.current_minute_low = 0
        self.current_minute_open = 0

        self.target_minute_index = -1
        self.target_minutes = [1, 3, 5, 15, 30]
        self.minute_1_range = [str(minute).zfill(2) for minute in range(0, 60)]
        self.minute_3_range = [str(minute).zfill(2) for minute in range(0, 60, 3)]
        self.minute_5_range = [str(minute).zfill(2) for minute in range(0, 60, 5)]
        self.minute_15_range = [str(minute).zfill(2) for minute in range(0, 60, 15)]
        self.minute_30_range = [str(minute).zfill(2) for minute in range(0, 60, 30)]
        self.current_minute = None

        self.target_hour_index = -1
        self.target_hours = [60, 120, 180, 240, 360, 720]
        self.hour_1_range = [str(minute).zfill(2) for minute in range(0, 24)]
        self.hour_2_range = [str(minute).zfill(2) for minute in range(0, 24, 2)]
        self.hour_3_range = [str(minute).zfill(2) for minute in range(0, 24, 3)]
        self.hour_4_range = [str(minute).zfill(2) for minute in range(0, 24, 4)]
        self.hour_6_range = [str(minute).zfill(2) for minute in range(0, 24, 6)]
        self.hour_12_range = [str(minute).zfill(2) for minute in range(0, 24, 12)]
        self.current_hour = None

        self.login()
        mongoengine.connect(host='mongodb://localhost:27017/kiwoom?connect=false')
        db = Document._get_db()
        db.drop_collection('tick')
        db.drop_collection('minute')

    def login(self):
        self.dynamicCall('CommConnect(int)', 1)

    def on_event_connect(self, err_code):
        if err_code == 0:
            print('Successfully login')
            #self.get_global_future_code_list()
            self.get_login_info()
        else:
            print('Failed login')

    def get_login_info(self):
        self.account_numbers = self.dynamicCall('GetLoginInfo(QString)', 'ACCNO').split(';')

    def get_global_future_code_list(self):
        self.future_item_list = self.dynamicCall("GetGlobalFutureItemlist()").split(';')
        for future_item in self.future_item_list:
            future_codes = self.dynamicCall("GetGlobalFutureCodelist(QString)", future_item).split(';')
            for future_code in future_codes:
                self.future_code_list.append(future_code)
                code_info = self.dynamicCall("GetGlobalFutOpCodeInfoByCode(QString)", future_code)
                print(future_code)
                print(code_info)
                print('=========')

    def validate(self):
        if self.code_symbol == '':
            TelegramBot.send_message(kei_id, "종목코드가 입력되지 않았습니다.")
            raise Exception('종목코드를 입력해주세요')

        if self.basis_ma == 0:
            TelegramBot.send_message(kei_id, "기울기 정보가 입력되지 않았습니다.")
            raise Exception('Invalid Moving Average 기울기')

        if self.basis_tick_unit == 0 and self.basis_time_unit == 0:
            TelegramBot.send_message(kei_id, "틱, 분 단위 정보 둘다 입력되지 않았습니다.")
            raise Exception('Invalid Candle Unit value')

        if self.start_time == '':
            TelegramBot.send_message(kei_id, '시작 예정 시간 정보가 입력되지 않았습니다.')

        if self.exit_time == '':
            TelegramBot.send_message(kei_id, '종료 예정 시간 정보가 입력되지 않았습니다.')
            raise Exception('Invalid Program Exit Time')

        if self.quantity == 0:
            TelegramBot.send_message(kei_id, '수량 정보가 입력되지 않았습니다')
            raise Exception('Invalid Quantity')

        if self.profit_tick == 0 or self.loss_tick == 0:
            TelegramBot.send_message(kei_id, '익절, 손절 틱 정보가 입력되지 않았습니다.')

    def start_trade(self):
        self.validate()
        message = f'자동매매 프로그램을 시작합니다. 종목코드: {self.code_symbol}, 기울기: {self.basis_ma}, ' \
                  f'틱봉단위: {self.basis_tick_unit}, 분봉단위: {self.basis_time_unit}, ' \
                  f'시작 예정 시간: {self.start_time}, 종료 예정 시간: {self.exit_time}, ' \
                  f'익절 틱: {self.profit_tick}, 손절 틱: {self.loss_tick}, 진입 수량: {self.quantity}, ' \
                  f'재진입시 건너뛰는 봉 개수: {self.skip_candle}, ' \
                  f'최대 익절 금액: {self.maximum_profit}, 최대 손절 금액: {self.maximum_loss},' \
                  f'스위칭 전략 사용 여부: {self.switching_strategy}, 손절 봉 개수: {self.stop_loss_candle_count}'
        TelegramBot.send_message(kei_id, message)

        if self.basis_tick_unit > 0: # tick unit이 0인 경우에는 설정이 되지 않은 경우이다.
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", self.code_symbol)
            self.dynamicCall("SetInputValue(QString, QString)", "시간단위", self.basis_tick_unit)
            self.dynamicCall("CommRqData(QString, QString, QString, QString)", "해외선물옵션틱차트조회", "opc10001", '', "2000")
        elif self.basis_time_unit > 0:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", self.code_symbol)
            self.dynamicCall("SetInputValue(QString, QString)", "시간단위", self.basis_time_unit)
            self.dynamicCall("CommRqData(QString, QString, QString, QString)", "해외선물옵션분차트조회", "opc10002", '', "2001")
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", self.code_symbol)
        self.dynamicCall("CommRqData(QString, QString, QString, QString)", "종목정보조회", "opt10001", '', "2002")

    def stop_trade(self):
        message = f'프로그램이 종료됩니다.'
        TelegramBot.send_message(kei_id, message)
        sys.exit()

    def get_current_position(self):
        print('request get current position')
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_numbers[0])
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", '0000')
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체", '00')
        self.dynamicCall("SetInputValue(QString, QString)", "통화코드", 'USD')
        self.dynamicCall("CommRqData(QString, QString, QString, QString)", "미결제잔고내역조회", "opw30003", '', "2003")

    def on_receive_tr_data(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == '해외선물옵션틱차트조회':
            tick_count = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "최종틱갯수").strip()
            code_name = sPrevNext.split(' ')[0][2:] # code_name에서 F0은 제거한다.
            self.init_position(code_name)
            self.tick_count[code_name] = int(tick_count)
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            self.current_tick_close = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "현재가").strip()
            self.current_tick_close = round(float(self.current_tick_close), 2)

            self.current_tick_open = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "시가").strip()
            self.current_tick_open = round(float(self.current_tick_open), 2)

            self.current_tick_low = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "저가").strip()
            self.current_tick_low = round(float(self.current_tick_low), 2)

            self.current_tick_high = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "고가").strip()
            self.current_tick_high = round(float(self.current_tick_high), 2)

            for i in range(1, rows):
                close_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가").strip()
                close_price = round(float(close_price), 2)

                open_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가").strip()
                open_price = round(float(open_price), 2)

                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가").strip()
                low_price = round(float(low_price), 2)

                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가").strip()
                high_price = round(float(high_price), 2)

                time = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결시간").strip()

                try:
                    Tick(close_price=close_price, open_price=open_price, low_price=low_price,
                         high_price=high_price, name=code_name, time=time, tick_unit=self.basis_tick_unit).save()
                except Exception as e:
                    print(e)
        elif sRQName == '해외선물옵션분차트조회':
            code_name = sPrevNext.split(' ')[0][2:]
            self.init_position(code_name)

            self.current_minute_close = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       0, "현재가").strip()
            self.current_minute_close = round(float(self.current_minute_close), 2)

            self.current_minute_open = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                      0, "시가").strip()
            self.current_minute_open = round(float(self.current_minute_open), 2)

            self.current_minute_low = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                                     "저가").strip()
            self.current_minute_low = round(float(self.current_minute_low), 2)

            self.current_minute_high = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                      0, "고가").strip()
            self.current_minute_high = round(float(self.current_minute_high), 2)
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(1, rows):
                close_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                               "현재가").strip()
                close_price = round(float(close_price), 2)

                open_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                              "시가").strip()
                open_price = round(float(open_price), 2)

                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                             "저가").strip()
                low_price = round(float(low_price), 2)

                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                              "고가").strip()
                high_price = round(float(high_price), 2)

                time = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                        "체결시간").strip()
                try:
                    Minute(close_price=close_price, open_price=open_price, low_price=low_price,
                           high_price=high_price, name=code_name, time=time, minute_unit=self.basis_time_unit).save()
                except Exception as e:
                    print(e)

        elif sRQName == '미결제잔고내역조회':
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드").strip()
                buy_or_sell = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매도수구분").strip() # buy:2 , sell: 1
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수량").strip()
                self.set_position(code, int(buy_or_sell))
                print('current position: ' + str(self.current_position[code]))

        elif sRQName == '종목정보조회':
            self.tick_unit[self.code_symbol] = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                                sRQName, 0, "틱단위").strip()
            tick_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                                sRQName, 0, "틱가치").strip()
            start_time = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                                sRQName, 0, "시작시간").strip()
            end_time = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                                sRQName, 0, "종료시간").strip()

    def on_receive_real_data(self, sCode, sRealType, sRealData):
        if sRealType == '해외선물시세':
            if self.basis_tick_unit > 0:
                self.get_tick_data(sCode, sRealType, sRealData)
            elif self.basis_time_unit > 0:
                self.get_time_data(sCode, sRealType, sRealData)

    def is_skip_trade(self):
        if self.is_just_position_close and self.skip_candle > 0:
            self.current_skip_candle = self.current_skip_candle + 1
            if self.current_skip_candle > self.skip_candle:
                self.current_skip_candle = 0
                self.is_just_position_close = False
                return False
            else:
                return True
        else:
            return False

    def is_reach_maximum_profit(self, code):
        if 0 < self.maximum_profit <= self.current_profit_loss:
            self.liquidate_position_if_have_position(code)
            message = f'최대 익절 금액에 도달하여 프로그램이 종료됩니다. 익절 금액: {self.current_profit_loss}'
            TelegramBot.send_message(kei_id, message)
            sys.exit()

    def is_reach_maximum_loss(self, code):
        if 0 < self.maximum_loss and (self.current_profit_loss < 0 and abs(self.current_profit_loss) > self.maximum_loss):
            self.liquidate_position_if_have_position(code)
            message = f'최대 손절 금액에 도달하여 프로그램이 종료됩니다. 손절 금액: {self.current_profit_loss}'
            TelegramBot.send_message(kei_id, message)
            sys.exit()

    def get_tick_data(self, sCode, sRealType, sRealData):
        trade_time = self.dynamicCall("GetCommRealData(QString, int)", sCode, 20)  # 체결 시간
        trade_date = self.dynamicCall("GetCommRealData(QString, int)", sCode, 22)  # 체결 일자
        time = trade_date + trade_time

        current_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, 10)  # 현재가(체결가)
        current_price = abs(float(current_price))

        if self.current_tick_high < current_price:
            self.current_tick_high = current_price

        if self.current_tick_low > current_price:
            self.current_tick_low = current_price

        self.running_or_exit(sCode, trade_time)
        self.holding_or_liquid_position(sCode, current_price)
        self.is_reach_maximum_profit(sCode)
        self.is_reach_maximum_loss(sCode)

        self.tick_count[sCode] = self.tick_count[sCode] + 1
        if self.basis_tick_unit == self.tick_count[sCode]:
            last_tick = Tick.objects().order_by('-time').first()
            open_price = last_tick.close_price

            if self.stop_loss_candle_count > 0:
                stop_loss_ticks = Tick.objects().order_by('-time')[:self.stop_loss_candle_count]
            elif self.stop_loss_candle_count == 0: # default stop loss candle if stop_loss_canlde_count is zero
                stop_loss_ticks = Tick.objects().order_by('-time')[:1]
            else:
                raise Exception('Invalid Stop loss candle count')

            tick = Tick(close_price=current_price, open_price=open_price, low_price=self.current_tick_low,
                        high_price=self.current_tick_high, name=sCode, time=time, tick_unit=self.basis_tick_unit).save()

            self.tick_count[sCode] = 0

            self.current_tick_high = 0
            self.current_tick_low = 100000

            if self.is_starting_time is False:
                if self.check_is_starting_time(sCode, trade_time) is False:
                    return

            if self.is_skip_trade() is False:
                self.trade(code=sCode, quantity=self.quantity, candle=tick, stop_loss_basis_candles=stop_loss_ticks)

    def get_time_data(self, sCode, sRealType, sRealData):
        trade_time = self.dynamicCall("GetCommRealData(QString, int)", sCode, 20)  # 체결 시간
        trade_date = self.dynamicCall("GetCommRealData(QString, int)", sCode, 22)  # 체결 일자
        time = trade_date + trade_time

        current_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, 10)  # 현재가(체결가)
        current_price = abs(float(current_price))

        if self.current_minute_high < current_price:
            self.current_minute_high = current_price

        if self.current_minute_low > current_price:
            self.current_minute_low = current_price

        self.running_or_exit(sCode, trade_time)
        self.holding_or_liquid_position(sCode, current_price)
        self.is_reach_maximum_profit(sCode)
        self.is_reach_maximum_loss(sCode)

        if self.is_minute_candle_close(self.basis_time_unit, trade_time):
            last_candle = Minute.objects().order_by('-time').first()
            if self.stop_loss_candle_count > 0:
                stop_loss_candles = Minute.objects().order_by('-time')[:self.stop_loss_candle_count]
            elif self.stop_loss_candle_count == 0:
                stop_loss_candles = Minute.objects().order_by('-time')[:1]
            else:
                raise Exception('Invalid Stop Loss Count')
            open_price = last_candle.close_price

            minute_candle = Minute(close_price=current_price, open_price=open_price, low_price=self.current_minute_low,
                                   high_price=self.current_minute_high, name=sCode, time=time, minute_unit=self.basis_time_unit).save()
            message = f'현재 만들어진 분봉 캔들 정보 => 종가: {minute_candle.close_price}, 시가: {minute_candle.open_price},' \
                      f'저가: {minute_candle.low_price}, 고가: {minute_candle.high_price}, 분봉 타입: {self.basis_time_unit}봉'
            #TelegramBot.send_message(kei_id, message)

            # initialize
            self.current_minute_high = 0
            self.current_minute_low = 10000000

            if self.is_starting_time is False:
                if self.check_is_starting_time(sCode, trade_time) is False:
                    return

            if self.is_skip_trade() is False:
                self.trade(code=sCode, quantity=self.quantity, candle=minute_candle,
                           stop_loss_basis_candles=stop_loss_candles)

    def is_minute_candle_close(self, basis_minute_unit, current_time):
        current_hour = current_time[:2]
        current_minute = current_time[2:4]

        if basis_minute_unit in self.target_minutes:
            if basis_minute_unit == 1:
                if self.current_minute is not None and self.current_minute != current_minute and current_minute in self.minute_1_range:
                    self.current_minute = current_minute
                    return True
                self.current_minute = current_minute

            elif basis_minute_unit == 3:
                if self.current_minute is not None and self.current_minute != current_minute and current_minute in self.minute_3_range:
                    self.current_minute = current_minute
                    return True
                self.current_minute = current_minute

            elif basis_minute_unit == 5:
                if self.current_minute is not None and self.current_minute != current_minute and current_minute in self.minute_5_range:
                    self.current_minute = current_minute
                    return True
                self.current_minute = current_minute

            elif basis_minute_unit == 15:
                if self.current_minute is not None and self.current_minute != current_minute and current_minute in self.minute_15_range:
                    self.current_minute = current_minute
                    return True
                self.current_minute = current_minute

            elif basis_minute_unit == 30:
                if self.current_minute is not None and self.current_minute != current_minute and current_minute in self.minute_3_range:
                    self.current_minute = current_minute
                    return True
                self.current_minute = current_minute
            return False

        elif basis_minute_unit in self.target_hours:
            if basis_minute_unit == 60:
                if self.current_hour is not None and self.current_hour != current_hour and current_hour in self.hour_1_range:
                    self.current_hour = current_hour
                    return True
                self.current_hour = current_hour

            elif basis_minute_unit == 120:
                if self.current_hour is not None and self.current_hour != current_hour and current_hour in self.hour_2_range:
                    self.current_hour = current_hour
                    return True
                self.current_hour = current_hour

            elif basis_minute_unit == 180:
                if self.current_hour is not None and self.current_hour != current_hour and current_hour in self.hour_3_range:
                    self.current_hour = current_hour
                    return True
                self.current_hour = current_hour

            elif basis_minute_unit == 240:
                if self.current_hour is not None and self.current_hour != current_hour and current_hour in self.hour_4_range:
                    self.current_hour = current_hour
                    return True
                self.current_hour = current_hour

            elif basis_minute_unit == 360:
                if self.current_hour is not None and self.current_hour != current_hour and current_hour in self.hour_6_range:
                    self.current_hour = current_hour
                    return True
                self.current_hour = current_hour

            elif basis_minute_unit == 720:
                if self.current_hour is not None and self.current_hour != current_hour and current_hour in self.hour_12_range:
                    self.current_hour = current_hour
                    return True
                self.current_hour = current_hour

            return False

    def get_short_position_stop_loss(self, stop_loss_basis_candles):
        highest_price = stop_loss_basis_candles[0].high_price
        for stop_loss_basis_candle in stop_loss_basis_candles:
            if highest_price < stop_loss_basis_candle.high_price:
                highest_price = stop_loss_basis_candle.high_price
        return highest_price

    def get_long_position_stop_loss(self, stop_loss_basis_candles):
        lowest_price = stop_loss_basis_candles[0].low_price
        for stop_loss_basis_candle in stop_loss_basis_candles:
            if lowest_price > stop_loss_basis_candle.low_price:
                lowest_price = stop_loss_basis_candle.low_price
        return lowest_price

    def trade(self, code, quantity, candle, stop_loss_basis_candles):
        position = self.get_position(code)
        print('current_position:' + str(position))

        short_position_stop_loss_price = self.get_short_position_stop_loss(stop_loss_basis_candles)
        long_position_stop_loss_price = self.get_long_position_stop_loss(stop_loss_basis_candles)

        ma_diff = self.get_moving_average_diff()
        if ma_diff < 0 and abs(ma_diff) > self.basis_ma and (position == 0 or position == 2):
            if position == 0 and code not in self.stop_loss:
                self.set_current_entry_price(code, candle.close_price)
                self.set_position(code, 1)
                self.set_stop_loss(code, short_position_stop_loss_price)
                self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                self.get_order_type('신규매도'), code, quantity, '0', '', self.get_trade_type('시장가'),
                                '')
                message = f'숏 포지션 신규 진입, 진입가: {candle.close_price}, 손절가: {short_position_stop_loss_price}, 종목코드: {candle.name} ' \
                          f'진입한 시점의 틱 정보: 고가: {candle.high_price}, 저가: {candle.low_price}, 시가: {candle.open_price}, 종가: {candle.close_price}'
                TelegramBot.send_message(kei_id, message)

            elif position == 2 and code in self.stop_loss and self.switching_strategy == 1:
                self.set_current_entry_price(code, candle.close_price)
                self.set_position(code, 1)
                self.set_stop_loss(code, short_position_stop_loss_price)
                self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                self.get_order_type('신규매도'), code, quantity+quantity, '0', '', self.get_trade_type('시장가'),
                                '')
                message = f'롱 포지션 정리하고 숏 포지션으로 스위칭, 진입가: {candle.close_price}, 손절가: {short_position_stop_loss_price}, 종목코드: {candle.name} ' \
                          f'진입한 시점의 틱 정보: 고가: {candle.high_price}, 저가: {candle.low_price}, 시가: {candle.open_price}, 종가: {candle.close_price}'
                TelegramBot.send_message(kei_id, message)

        elif ma_diff > 0 and abs(ma_diff) > self.basis_ma and (position == 0 or position == 1):
            if position == 0 and code not in self.stop_loss:
                self.set_current_entry_price(code, candle.close_price)
                self.set_position(code, 2)
                self.set_stop_loss(code, long_position_stop_loss_price)
                self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                self.get_order_type('신규매수'), code, quantity, '0', '', self.get_trade_type('시장가'),
                                '')
                message = f'롱 포지션 신규 진입, 진입가: {candle.close_price}, 손절가: {long_position_stop_loss_price}, 종목코드: {candle.name} ' \
                          f'진입한 시점의 틱 정보: 고가: {candle.high_price}, 저가: {candle.low_price}, 시가: {candle.open_price}, 종가: {candle.close_price}'
                TelegramBot.send_message(kei_id, message)
                
            elif position == 1 and code in self.stop_loss and self.switching_strategy == 1:
                self.set_current_entry_price(code, candle.close_price)
                self.set_position(code, 2)
                self.set_stop_loss(code, long_position_stop_loss_price)
                self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                self.get_order_type('신규매수'), code, quantity+quantity, '0', '', self.get_trade_type('시장가'),
                                '')
                message = f'숏 포지션 정리하고 롱 포지션으로 스위칭, 진입가: {candle.close_price}, 손절가: {long_position_stop_loss_price}, 종목코드: {candle.name} ' \
                          f'진입한 시점의 틱 정보: 고가: {candle.high_price}, 저가: {candle.low_price}, 시가: {candle.open_price}, 종가: {candle.close_price}'

                TelegramBot.send_message(kei_id, message)

    def liquidate_position_if_have_position(self, code):
        if code in self.current_position:
            position = self.get_position(code)
            if position == 2:
                self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                self.get_order_type('신규매도'), code, self.quantity, '0', '',
                                self.get_trade_type('시장가'), '')
                message = f'프로그램 종료 전 롱 포지션 정리, 종목코드: {code}'
                TelegramBot.send_message(kei_id, message)
                self.init_position(code)
                del self.stop_loss[code]
                del self.current_entry_price[code]
            elif position == 1:
                self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                self.get_order_type('신규매수'), code, self.quantity, '0', '',
                                self.get_trade_type('시장가'), '')
                message = f'프로그램 종료 전 숏 포지션 정리, 종목코드 : {code}'
                TelegramBot.send_message(kei_id, message)
                self.init_position(code)
                del self.stop_loss[code]
                del self.current_entry_price[code]

    def check_is_starting_time(self, code, trade_time):
        current_hour = int(trade_time[:2])
        current_minute = int(trade_time[2:4])

        start_hour = self.start_time.split(':')[0]
        start_minute = self.start_time.split(':')[1]

        if current_hour == int(start_hour) and current_minute >= int(start_minute):
            self.is_starting_time = True
            message = f'프로그램 시작 시간에 도달했습니다. 자동매매 프로그램을 시작합니다.'
            TelegramBot.send_message(kei_id, message)
            return True
        else:
            return False

    def running_or_exit(self, code, trade_time):
        current_hour = int(trade_time[:2])
        current_minute = int(trade_time[2:4])

        exit_hour = self.exit_time.split(':')[0]
        exit_minute = self.exit_time.split(':')[1]

        if current_hour == int(exit_hour) and current_minute >= int(exit_minute):
            self.liquidate_position_if_have_position(code)
            message = f'프로그램이 종료됩니다.'
            TelegramBot.send_message(kei_id, message)
            sys.exit()

    def holding_or_liquid_position(self, code, current_price):
        if code in self.stop_loss:
            position = self.get_position(code)
            if position == 2: # 2: buy, 1: sell
                if self.stop_loss[code] > current_price:
                    self.init_position(code)
                    self.is_just_position_close = True
                    self.current_skip_candle = 0
                    del self.stop_loss[code]
                    del self.current_entry_price[code]
                    self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                   self.get_order_type('신규매도'), code, self.quantity, '0', '', self.get_trade_type('시장가'), '')

                    message = f'롱 포지션 손절, 종목코드: {code}, 손절가격: {current_price}'
                    TelegramBot.send_message(kei_id, message)
                    return
            elif position == 1:
                if self.stop_loss[code] < current_price:
                    self.init_position(code)
                    self.is_just_position_close = True
                    self.current_skip_candle = 0
                    del self.stop_loss[code]
                    del self.current_entry_price[code]
                    self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                    self.get_order_type('신규매수'), code, self.quantity, '0', '',
                                    self.get_trade_type('시장가'), '')
                    message = f'숏 포지션 손절, 종목코드: {code}, 손절가격: {current_price}'
                    TelegramBot.send_message(kei_id, message)
                    return

        if code in self.current_entry_price and self.profit_tick != 0 and self.loss_tick != 0:
            position = self.get_position(code)
            entry_price = self.get_current_entry_price(code)

            if position == 2: # Long Position
                profit_limit_price = entry_price + (self.profit_tick * float(self.tick_unit[code]))
                loss_limit_price = entry_price - (self.loss_tick * float(self.tick_unit[code]))
                if current_price >= profit_limit_price:
                    self.init_position(code)
                    self.is_just_position_close = True
                    self.current_skip_candle = 0
                    del self.stop_loss[code]
                    del self.current_entry_price[code]
                    self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                    self.get_order_type('신규매도'), code, self.quantity, '0', '',
                                    self.get_trade_type('시장가'), '')
                    message = f'롱 포지션 익절, 종목코드: {code}, 익절 가격: {current_price}'
                    TelegramBot.send_message(kei_id, message)
                elif current_price <= loss_limit_price:
                    self.init_position(code)
                    self.is_just_position_close = True
                    self.current_skip_candle = 0
                    del self.stop_loss[code]
                    del self.current_entry_price[code]
                    self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                    self.get_order_type('신규매도'), code, self.quantity, '0', '',
                                    self.get_trade_type('시장가'), '')
                    message = f'롱 포지션 손절, 종목코드: {code}, 손절 가격: {current_price}'
                    TelegramBot.send_message(kei_id, message)

            elif position == 1: # Short Position
                profit_limit_price = entry_price - ((self.profit_tick * float(self.tick_unit[code])))
                loss_limit_price = entry_price + (self.loss_tick * float(self.tick_unit[code]))

                if current_price <= profit_limit_price:
                    self.init_position(code)
                    self.is_just_position_close = True
                    self.current_skip_candle = 0
                    del self.stop_loss[code]
                    del self.current_entry_price[code]
                    self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                    self.get_order_type('신규매수'), code, self.quantity, '0', '',
                                    self.get_trade_type('시장가'), '')
                    message = f'숏 포지션 익절, 종목코드: {code}, 익절 가격: {current_price}'
                    TelegramBot.send_message(kei_id, message)

                elif current_price >= loss_limit_price:
                    self.init_position(code)
                    self.is_just_position_close = True
                    self.current_skip_candle = 0
                    del self.stop_loss[code]
                    del self.current_entry_price[code]
                    self.send_order("시장가주문", self.get_screen_number(), self.account_numbers[0],
                                    self.get_order_type('신규매수'), code, self.quantity, '0', '',
                                    self.get_trade_type('시장가'), '')

                    message = f'숏 포지션 손절, 종목코드: {code}, 손절 가격: {current_price}'
                    TelegramBot.send_message(kei_id, message)

    def get_moving_average_diff(self):
        if self.basis_tick_unit > 0:
            tick_candles = Tick.objects(tick_unit=self.basis_tick_unit).order_by('-time')[:600]
            close_list = [float(candle.close_price) for candle in tick_candles]
            close_list = np.asarray(close_list)
            close_list = close_list[::-1]

            close_df_with_ma = DataFrame.create_jisu_ma(close_list, 5)
            df_tails = close_df_with_ma.tail(5)
            print(df_tails)
            before_ma = round(df_tails['MA'].values[3], 3)
            current_ma = round(df_tails['MA'].values[4], 3)
            diff = current_ma - before_ma
            return diff
        elif self.basis_time_unit > 0: # basis_time_unit (분봉)인 경우
            minute_candles = Minute.objects(minute_unit=self.basis_time_unit).order_by('-time')[:600]
            close_list = [float(candle.close_price) for candle in minute_candles]
            close_list = np.asarray(close_list)
            close_list = close_list[::-1]

            close_df_with_ma = DataFrame.create_jisu_ma(close_list, 5)
            df_tails = close_df_with_ma.tail(5)
            print(df_tails)
            before_ma = round(df_tails['MA'].values[3], 3)
            current_ma = round(df_tails['MA'].values[4], 3)
            diff = current_ma - before_ma
            return diff

    def send_order(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, sPrice, sStop, sHogaGb, sOrgOrderNo):
        if not (isinstance(sRQName, str)
                and isinstance(sScreenNo, str)
                and isinstance(sAccNo, str)
                and isinstance(nOrderType, int)
                and isinstance(sCode, str)
                and isinstance(sPrice, str)
                and isinstance(sStop, str)
                and isinstance(sHogaGb, str)
                and isinstance(sOrgOrderNo, str)):
            print("Error : ParameterTypeError by SendOrder") # nQty type check는 제거함

        error_code = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, QString, QString, QString, QString)",
                         [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, sPrice, sStop, sHogaGb, sOrgOrderNo])
        print('error_code: ' + str(error_code))
        return error_code

    def send_oco_order(self, code, quantity, stop_loss_price, limit_price):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_numbers[0])
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", '0000')
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체", '00')
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", self.code_symbol)

        position = self.get_position(code)
        if position == 2:
            self.dynamicCall("SetInputValue(QString, QString)", "매도수구분", '1')
        elif position == 1:
            self.dynamicCall("SetInputValue(QString, QString)", "매도수구분", '2')

        self.dynamicCall("SetInputValue(QString, QString)", "해외주문유형", '5') # 5: oco
        self.dynamicCall("SetInputValue(QString, QString)", "주문수량", str(quantity))
        self.dynamicCall("SetInputValue(QString, QString)", "주문표시가격", '0')

        self.dynamicCall("SetInputValue(QString, QString)", "STOP구분", '1')
        self.dynamicCall("SetInputValue(QString, QString)", "STOP표시가격", str(stop_loss_price))

        self.dynamicCall("SetInputValue(QString, QString)", "LIMIT구분", '1')
        self.dynamicCall("SetInputValue(QString, QString)", "LIMIT표시가격", str(limit_price))

        self.dynamicCall("SetInputValue(QString, QString)", "해외주문조건구분", '0')
        self.dynamicCall("SetInputValue(QString, QString)", "주문조건종료일자", '0')

        self.dynamicCall("SetInputValue(QString, QString)", "통신주문구분", 'AP')
        self.dynamicCall("CommRqData(QString, QString, QString, QString)", "해외파생신규주문2", "opw10008", '', "2004")

    def get_order_type(self, order_type):
        if order_type == '신규매도':
            return 1
        elif order_type == '신규매수':
            return 2
        elif order_type == '매수취소':
            return 3
        elif order_type == '매도취소':
            return 4
        elif order_type == '매수정정':
            return 5
        elif order_type == '매도정정':
            return 6

    def get_trade_type(self, trade_type):
        if trade_type == '지정가':
            return '0'
        elif trade_type == '시장가':
            return '1'

    def get_screen_number(self):
        if self.screen_number > 9999:
            self.screen_number = 1000
        self.screen_number = self.screen_number + 1
        return str(self.screen_number)

    def on_receive_msg(self, screen_number, rq_name, tr_code, msg):
        pass
        #print('== receive msg ==')
        #print(screen_number)
        #print(rq_name)
        #print(tr_code)
        #print(msg)

    def on_receive_chejan_data(self, sGubun, nItemCnt, sFidList):
        if sGubun == '1': # 잔고
            profit_or_loss = self.get_chejan_data(50719)
            trade_price = self.get_chejan_data(910)
            buy_or_sell = self.get_chejan_data(907)
            code = self.get_chejan_data(9001)

            if self.basis_tick_unit > 0:
                if self.stop_loss_candle_count > 0:
                    stop_loss_candles = Tick.objects().order_by('-time')[:self.stop_loss_candle_count]
                elif self.stop_loss_candle_count == 0:  # default stop loss candle if stop_loss_canlde_count is zero
                    stop_loss_candles = Tick.objects().order_by('-time')[:1]
                else:
                    stop_loss_candles = None
            elif self.basis_time_unit > 0:
                if self.stop_loss_candle_count > 0:
                    stop_loss_candles = Minute.objects().order_by('-time')[:self.stop_loss_candle_count]
                elif self.stop_loss_candle_count == 0:
                    stop_loss_candles = Minute.objects().order_by('-time')[:1]
                else:
                    stop_loss_candles = None

            short_position_stop_loss_price = self.get_short_position_stop_loss(stop_loss_candles)
            long_position_stop_loss_price = self.get_long_position_stop_loss(stop_loss_candles)

            if not self.is_init_position(code):
                self.set_current_entry_price(code, int(float(trade_price)))

                if buy_or_sell == '1':
                    self.set_stop_loss(code, short_position_stop_loss_price)
                elif buy_or_sell == '2':
                    self.set_stop_loss(code, long_position_stop_loss_price)

                message = f"현재 실현 손익: {profit_or_loss}, 실제 체결 가격: {trade_price}, " \
                          f"매도, 매수 여부: {buy_or_sell}(1: 매도, 2: 매수), 종목코드: {code}," \
                          f"롱 포지션 일 경우 손절 가격: {long_position_stop_loss_price}, " \
                          f"숏 포지션 일 경우 손절 가격: {short_position_stop_loss_price}"
                TelegramBot.send_message(kei_id, message)
                self.current_profit_loss = int(float(profit_or_loss))

            if self.is_init_position(code):
                message = f"현재 실현 손익: {profit_or_loss}, 실제 체결 가격: {trade_price}, 종목코드: {code}"
                TelegramBot.send_message(kei_id, message)

    def get_chejan_data(self, nFid):
        if not (isinstance(nFid, int)):
            raise Exception('chejan error')
        return self.dynamicCall("GetChejanData(int)", nFid)

    def init_position(self, code):
        self.current_position[code] = 0

    def set_position(self, code, position):
        self.current_position[code] = position

    def is_init_position(self, code):
        if self.current_position[code] == 0:
            return True
        else:
            return False

    def set_current_entry_price(self, code, price):
        self.current_entry_price[code] = price

    def get_position(self, code):
        return self.current_position[code]

    def get_current_entry_price(self, code):
        return self.current_entry_price[code]

    def set_stop_loss(self, code, price):
        self.stop_loss[code] = price

    def set_basis_ma(self, basis_ma):
        self.basis_ma = basis_ma

    def get_basis_ma(self):
        return self.basis_ma

    def set_code_symbol(self, symbol):
        self.code_symbol = symbol

    def set_tick_unit(self, unit):
        self.basis_tick_unit = unit

    def set_time_unit(self, unit):
        self.basis_time_unit = unit

    def set_exit_time(self, exit_time):
        self.exit_time = exit_time

    def set_profit_tick(self, profit_tick):
        self.profit_tick = profit_tick

    def set_loss_tick(self, loss_tick):
        self.loss_tick = loss_tick

    def set_quantity(self, quantity):
        self.quantity = quantity

    def set_skip_candle(self, skip_candle):
        self.skip_candle = skip_candle

    def set_start_time(self, start_time):
        self.start_time = start_time

    def set_maximum_profit(self, maximum_profit):
        self.maximum_profit = maximum_profit

    def set_maximum_loss(self, maximum_loss):
        self.maximum_loss = maximum_loss

    def set_switching_strategy(self, switching_strategy):
        self.switching_strategy = switching_strategy

    def set_stop_loss_candle_count(self, stop_loss_candle_count):
        self.stop_loss_candle_count = stop_loss_candle_count


class TelegramBot(object):
    token = '985728867:AAE9kltQqpmIdwPi510h4fzfQas59besQzE'
    bot = telegram.Bot(token)

    @classmethod
    def send_message(cls, chat_id, message):
        try:
            cls.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            print('raise exception while sending telegram message')
            print(e)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        hts = GlobalKiwoom()
        window = Window(hts)#
        window.show()
        sys.exit( app.exec_() )
    except Exception as e:
        print(e)