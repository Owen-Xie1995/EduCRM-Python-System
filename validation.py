"""輸入格式與業務規則，不依賴桌面介面。"""
import re


def validate_payment_amount(value):
    text = str(value).strip()
    if not re.fullmatch(r'[0-9]+', text):
        raise ValueError('繳費金額請輸入正整數（元）')
    amount = int(text)
    if not 1 <= amount <= 2_147_483_647:
        raise ValueError('繳費金額必須大於 0，且不可超過資料庫整數上限')
    return amount


def validate_billing_period(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-(0[1-9]|1[0-2])', value):
        raise ValueError('帳期格式請使用 YYYY-MM，例如 2026-10')
    if value.startswith('0000'):
        raise ValueError('帳期年份必須大於 0')
    return value
