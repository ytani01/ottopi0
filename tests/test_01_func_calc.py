#
# (c) 2025 Yoichi Tanibayashi
#
import pytest

from ottopi0.svr.func_calc import Calc


@pytest.fixture
def calc_instance():
    """Calcクラスのインスタンスを提供するフィクスチャ。"""
    return Calc()


class TestCalc:
    """func_calc.py内のCalcクラスのテストクラス。"""

    def test_init(self, calc_instance):
        """Calcクラスの__init__メソッドをテスト。
        'foo'属性が正しく初期化されていることを確認する。
        """
        assert calc_instance.foo == "abc"

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (1, 2, 3),  # 正の整数
            (-1, -2, -3),  # 負の整数
            (1.5, 2.5, 4.0),  # 正の浮動小数点数
            (-1.5, -2.5, -4.0),  # 負の浮動小数点数
            (0, 0, 0),  # ゼロ
            (100, -50, 50),  # 混合符号
            (1e9, 2e9, 3e9),  # 大きい数値
        ],
    )
    def test_add(self, calc_instance, a, b, expected):
        """さまざまな入力でaddメソッドをテスト。"""
        assert calc_instance.add(a, b) == expected

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (3, 2, 1),  # 正の整数
            (-1, -2, 1),  # 負の整数
            (4.5, 2.5, 2.0),  # 正の浮動小数点数
            (-1.5, -2.5, 1.0),  # 負の浮動小数点数
            (0, 0, 0),  # ゼロ
            (50, -50, 100),  # 混合符号
            (3e9, 1e9, 2e9),  # 大きい数値
        ],
    )
    def test_sub(self, calc_instance, a, b, expected):
        """さまざまな入力でsubメソッドをテスト。"""
        assert calc_instance.sub(a, b) == expected

    @pytest.mark.parametrize(
        "func, a, b, expected",
        [
            ("add", 1, 2, 3),
            ("sub", 3, 1, 2),
            ("add", -1, 1, 0),
            ("sub", -5, -2, -3),
            ("add", 1.5, 2.5, 4.0),
            ("sub", 4.5, 2.5, 2.0),
        ],
    )
    def test_calc_valid_func(self, calc_instance, func, a, b, expected):
        """有効な関数文字列 ('add', 'sub') でcalcメソッドをテスト。"""
        assert calc_instance.calc(func, a, b) == expected

    @pytest.mark.parametrize(
        "func, a, b",
        [
            ("multiply", 1, 2),  # 無効な関数文字列
            ("divide", 10, 2),  # 無効な関数文字列
            ("", 5, 3),  # 空の関数文字列
            (None, 1, 1),  # 関数文字列としてのNone
        ],
    )
    def test_calc_invalid_func(self, calc_instance, func, a, b):
        """無効な関数文字列でcalcメソッドをテスト。
        未知の関数に対しては0.0を返すはず。
        """
        assert calc_instance.calc(func, a, b) == 0.0
