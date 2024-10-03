import MySQLdb
from datetime import timedelta, datetime
import calendar

from ab_py.common.ab_exception import ABException
from ab_py.exsited.exsited_sdk import ExsitedSDK
from service.exsited_service import ExsitedService
from service.order_service import OrderService
from tests.common.common_data import CommonData


def connect_to_db():
    return MySQLdb.connect(
        host="",
        user="",
        passwd="",
        db=""
    )


def calculate_charging_period(start_date):
    last_day_of_month = calendar.monthrange(start_date.year, start_date.month)[1]
    start_of_month = datetime(start_date.year, start_date.month, 1)
    end_of_month = datetime(start_date.year, start_date.month, last_day_of_month)

    charging_period = f"{start_of_month.strftime('%Y-%m-%d')}-{end_of_month.strftime('%Y-%m-%d')}"
    return charging_period, start_of_month, end_of_month


def fetch_call_usage():
    db = connect_to_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT CallID, CallStart, CallDurationSec, CallDestination, CallType, ItemName, OrderID FROM CallUsage")
        rows = cursor.fetchall()

        exsited_service = ExsitedService()
        order_service = OrderService(exsited_service)

        call_usage_list = []
        for row in rows:
            call_id, call_start, call_duration, call_destination, call_type, item_name, order_id = row
            call_end = call_start + timedelta(seconds=call_duration)
            charge_item_uuid = order_service.get_charge_item_uuid_by_order_id(order_id, item_name)
            charging_period, start_of_month, end_of_month = calculate_charging_period(call_start)

            call_usage_entry = {
                "charge_item_uuid": charge_item_uuid,
                "quantity": 1,
                "start_time": call_start.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": call_end.strftime('%Y-%m-%d %H:%M:%S'),
                "type": "INCREMENTAL",
                "charging_period": charging_period
            }

            call_usage_list.append(call_usage_entry)

        return call_usage_list

    finally:
        cursor.close()
        db.close()


def fetch_message_usage():
    db = connect_to_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT ID, BillingPeriod, BillableMessages, ItemName, OrderID FROM MessageUsage")
        rows = cursor.fetchall()

        exsited_service = ExsitedService()
        order_service = OrderService(exsited_service)

        message_usage_list = []
        for row in rows:
            message_id, billing_period, billable_messages, item_name, order_id = row

            charge_item_uuid = order_service.get_charge_item_uuid_by_order_id(order_id, item_name)
            charging_period, start_of_month, end_of_month = calculate_charging_period(billing_period)

            message_usage_entry = {
                "charge_item_uuid": charge_item_uuid,
                "quantity": billable_messages,
                "start_time": start_of_month.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": end_of_month.strftime('%Y-%m-%d %H:%M:%S'),
                "type": "INCREMENTAL",
                "charging_period": charging_period
            }

            message_usage_list.append(message_usage_entry)

        return message_usage_list

    finally:
        cursor.close()
        db.close()
