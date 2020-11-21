import numpy as np
import pandas as pd


class DataFrame:
    @classmethod
    def create(cls, close_list):
        df = pd.DataFrame(close_list, columns=['close'])
        return df

    @classmethod
    def create_ma(cls, close_list, period):
        df = pd.DataFrame(close_list, columns=['close'])
        df['MA'] = df.rolling(window=period).mean()
        return df

    @classmethod
    def create_jisu_ma(cls, close_list, period):
        df = pd.DataFrame(close_list, columns=['close'])
        df['MA'] = df.ewm(span=period).mean()
        return df
