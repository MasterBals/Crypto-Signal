"""Decision engine for combining signals into a single trade decision."""

from datetime import datetime, timezone

import structlog
from talib import abstract

from analyzers.utils import IndicatorUtils


class DecisionEngine:
    """Aggregates indicator signals into a single decision."""

    def __init__(self, exchange_interface):
        self.logger = structlog.get_logger()
        self.exchange_interface = exchange_interface
        self.utils = IndicatorUtils()
        self.weights = {
            'h4_trend': 3,
            'zone_proximity': 3,
            'ema_alignment': 2,
            'rsi': 2,
            'macd': 1
        }
        self.threshold = 7
        self.h1_timeframe = '1h'
        self.h4_timeframe = '4h'
        self.atr_period = 14
        self.zone_lookback = 50
        self.zone_buffer_atr = 0.5
        self.atr_high_multiplier = 1.2
        self.atr_low_multiplier = 0.8


    def evaluate(self, exchange, market_pair, indicator_results, informant_results):
        """Evaluate a market pair and return a decision payload."""

        h1_data = self._get_historical_data(market_pair, exchange, self.h1_timeframe)
        h4_data = self._get_historical_data(market_pair, exchange, self.h4_timeframe)

        if not h1_data or not h4_data:
            return self._neutral_decision('missing_historical_data')

        h1_df = self.utils.convert_to_dataframe(h1_data)
        h4_df = self.utils.convert_to_dataframe(h4_data)

        h4_trend = self._get_h4_trend_signal(h4_df)
        rsi_signal = self._get_indicator_signal(indicator_results, 'rsi')
        macd_signal = self._get_indicator_signal(indicator_results, 'macd')
        ema_alignment = self._get_ema_alignment(informant_results)
        zone_signal, zone_type = self._get_zone_signal(h1_df)

        if zone_signal == 0:
            return self._neutral_decision('no_zone')

        h1_bias = self._weighted_sum({
            'zone_proximity': zone_signal,
            'ema_alignment': ema_alignment,
            'rsi': rsi_signal,
            'macd': macd_signal
        })

        if h4_trend == 0 or (h1_bias > 0 and h4_trend < 0) or (h1_bias < 0 and h4_trend > 0):
            return self._neutral_decision('h4_not_confirmed')

        scenario = self._get_volatility_scenario(h1_df)
        if scenario is None:
            return self._neutral_decision('volatility_mismatch')

        if not self._session_allows_signal(h4_trend):
            return self._neutral_decision('session_filter')

        weighted_score = self._weighted_sum({
            'h4_trend': h4_trend,
            'zone_proximity': zone_signal,
            'ema_alignment': ema_alignment,
            'rsi': rsi_signal,
            'macd': macd_signal
        })

        if abs(weighted_score) < self.threshold:
            return self._neutral_decision('threshold_not_met')

        decision = 'buy' if weighted_score > 0 else 'sell'
        confidence = self._confidence_score(weighted_score)

        return {
            'signal': decision,
            'confidence': confidence,
            'timeframe': 'H1/H4',
            'scenario': scenario,
            'zone': zone_type,
            'score': weighted_score,
            'weights': self.weights,
            'inputs': {
                'h4_trend': h4_trend,
                'zone_proximity': zone_signal,
                'ema_alignment': ema_alignment,
                'rsi': rsi_signal,
                'macd': macd_signal
            },
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'alert_enabled': True,
            'alert_frequency': 'once'
        }


    def _get_historical_data(self, market_pair, exchange, candle_period):
        try:
            return self.exchange_interface.get_historical_data(
                market_pair,
                exchange,
                candle_period
            )
        except Exception:
            self.logger.exception(
                'Decision engine failed fetching data for %s %s %s',
                exchange,
                market_pair,
                candle_period
            )
            return list()


    def _get_indicator_signal(self, indicator_results, indicator_name):
        entries = indicator_results.get(indicator_name, [])
        if not entries:
            return 0

        result = entries[0]['result']
        if result.shape[0] == 0:
            return 0

        latest = result.iloc[-1]
        if latest.get('is_hot'):
            return 1
        if latest.get('is_cold'):
            return -1
        return 0


    def _get_ema_alignment(self, informant_results):
        ema_entries = informant_results.get('ema', [])
        if len(ema_entries) >= 2:
            fast = ema_entries[0]['result']
            slow = ema_entries[-1]['result']
            if fast.shape[0] == 0 or slow.shape[0] == 0:
                return 0
            fast_value = fast.iloc[-1]['ema']
            slow_value = slow.iloc[-1]['ema']
            if fast_value > slow_value:
                return 1
            if fast_value < slow_value:
                return -1
        return 0


    def _get_h4_trend_signal(self, dataframe):
        ema_fast = abstract.EMA(dataframe, timeperiod=50)
        ema_slow = abstract.EMA(dataframe, timeperiod=200)
        if ema_fast.shape[0] < 2 or ema_slow.shape[0] < 2:
            return 0
        fast_now = ema_fast.iloc[-1]
        slow_now = ema_slow.iloc[-1]
        fast_prev = ema_fast.iloc[-2]
        if fast_now > slow_now and fast_now > fast_prev:
            return 1
        if fast_now < slow_now and fast_now < fast_prev:
            return -1
        return 0


    def _get_zone_signal(self, dataframe):
        recent = dataframe.tail(self.zone_lookback)
        if recent.shape[0] < self.zone_lookback:
            return 0, None

        atr_series = abstract.ATR(recent, timeperiod=self.atr_period)
        if atr_series.shape[0] == 0:
            return 0, None
        atr_value = atr_series.iloc[-1]
        zone_buffer = atr_value * self.zone_buffer_atr

        support = recent['low'].min()
        resistance = recent['high'].max()
        close = recent['close'].iloc[-1]

        if close <= support + zone_buffer:
            return 1, 'support'
        if close >= resistance - zone_buffer:
            return -1, 'resistance'
        return 0, None


    def _get_volatility_scenario(self, dataframe):
        atr_series = abstract.ATR(dataframe, timeperiod=self.atr_period)
        if atr_series.shape[0] < self.zone_lookback:
            return None

        recent_atr = atr_series.tail(self.zone_lookback)
        median_atr = recent_atr.median()
        current_atr = recent_atr.iloc[-1]
        if current_atr >= median_atr * self.atr_high_multiplier:
            return 'breakout'
        if current_atr <= median_atr * self.atr_low_multiplier:
            return 'rejection'
        return None


    def _session_allows_signal(self, h4_trend):
        now = datetime.now(timezone.utc)
        hour = now.hour
        is_london = 7 <= hour < 16
        is_new_york = 12 <= hour < 21
        is_asia = hour >= 23 or hour < 7

        if is_london or is_new_york:
            return True
        if is_asia and abs(h4_trend) >= 1:
            return True
        return False


    def _weighted_sum(self, signals):
        score = 0
        for key, value in signals.items():
            weight = self.weights.get(key, 0)
            score += weight * value
        return score


    def _confidence_score(self, score):
        max_score = sum(self.weights.values())
        if max_score == 0:
            return 0
        return round(min(abs(score) / max_score, 1) * 100)


    def _neutral_decision(self, reason):
        return {
            'signal': None,
            'confidence': 0,
            'timeframe': 'H1/H4',
            'scenario': None,
            'zone': None,
            'score': 0,
            'weights': self.weights,
            'inputs': dict(),
            'reason': reason,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'alert_enabled': False,
            'alert_frequency': 'once'
        }
