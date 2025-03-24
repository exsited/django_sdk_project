import MySQLdb
from datetime import timedelta, datetime
import calendar

from exsited.exsited.order.dto.usage_dto import UsageCreateDTO, UsageDataDTO
from service.exsited_service import ExsitedService
from service.order_service import OrderService


def connect_to_db():
    return MySQLdb.connect(
        host="127.0.0.1",
        user="root",
        passwd="",
        db="call_service"
    )


def update_status_to_active(record_list, column_name, table_name):
    db = connect_to_db()
    cursor = db.cursor()
    try:
        record_list_str = ", ".join(["%s"] * len(record_list))
        query = f"""
            UPDATE {table_name}
            SET Status = 'ACTIVE'
            WHERE {column_name} IN ({record_list_str})
        """
        cursor.execute(query, tuple(record_list))
        db.commit()
    except Exception as e:
        print(f"Error updating status to active for {record_list}: {e}")
    finally:
        cursor.close()
        db.close()


def calculate_charging_period(start_date, end_date):
    charging_period = f"{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"

    return charging_period


def create_usage_dto(charge_item_uuid: str, quantity: str, start_time: str, end_time: str, charging_period: str, usageReference:str):
    usage_data = UsageDataDTO(chargeItemUuid=charge_item_uuid,
                              quantity=quantity,
                              startTime=start_time,
                              endTime=end_time,
                              type="INCREMENTAL",
                              chargingPeriod=charging_period,
                              usageReference=usageReference
                              )

    return usage_data


def fetch_call_usage():
    db = connect_to_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT ID, CallStart, CallDurationSec, CallDestination, CallType, ItemName, OrderID, 
                   ChargingPeriodStart, ChargingPeriodEnd, Status, ReferenceUUID 
            FROM CallUsage 
            WHERE  Status = 'INACTIVE'
            """
        )

        rows = cursor.fetchall()
        if not rows:
            return {"status": "success", "message": "No inactive message usage records found."}

        unique_orders = set()
        reference_uuid_map = {}

        exsited_service = ExsitedService()
        order_service = OrderService(exsited_service)

        for row in rows:
            (call_id, call_start, call_duration, call_destination, call_type, item_name, order_id,
             charging_period_start, charging_period_end, status, reference_uuid) = row
            unique_orders.add((order_id, item_name))
            reference_uuid_map[reference_uuid] = call_id

        charge_item_uuids = {}
        for order_id, item_name in unique_orders:
            charge_item_uuid = order_service.get_charge_item_uuid_by_order_id(order_id, item_name)
            charge_item_uuids[(order_id, item_name)] = charge_item_uuid

        call_usage_list = []
        for row in rows:
            (call_id, call_start, call_duration, call_destination, call_type, item_name, order_id,
             charging_period_start, charging_period_end, status, reference_uuid) = row
            call_end = call_start + timedelta(seconds=call_duration)
            charging_period = calculate_charging_period(charging_period_start, charging_period_end)

            call_usage_data = create_usage_dto(charge_item_uuid=charge_item_uuids[(order_id, item_name)], quantity="1",
                                               start_time=call_start.strftime('%Y-%m-%d %H:%M:%S'),
                                               end_time=call_end.strftime('%Y-%m-%d %H:%M:%S'),
                                               charging_period=charging_period,
                                               usageReference=reference_uuid)

            call_usage_list.append(call_usage_data)
        response = order_service.order_usages_add(call_usage_list)
        print(response)
        if response.get('status') == 'success' and 'data' in response:
            success_call_ids = []
            success_entries = response['data'].get('success', [])

            for usage in success_entries:
                usage_reference = usage.get('usageReference')
                if usage_reference and usage_reference in reference_uuid_map:
                    success_call_ids.append(reference_uuid_map[usage_reference])

            if success_call_ids:
                update_status_to_active(record_list=success_call_ids, column_name='ID', table_name='CallUsage')

        return response

    finally:
        cursor.close()
        db.close()


def fetch_message_usage():
    db = connect_to_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
             SELECT ID, BillingPeriod, MessagesSent, ChargingPeriodStart, ChargingPeriodEnd, 
                    IncludedMessages, BillableMessages, ItemName, OrderID, UsageCustomAttribute1, 
                    UsageCustomAttribute2, UsageCustomAttribute3, Status,ReferenceUUID  
                    FROM MessageUsage
                    WHERE Status = 'INACTIVE'
            """
        )
        rows = cursor.fetchall()
        if not rows:
            return {"status": "success", "message": "No inactive message usage records found."}

        unique_orders = set()
        exsited_service = ExsitedService()
        order_service = OrderService(exsited_service)
        reference_uuid_map = {}

        for row in rows:
            (message_id, sent_date, messages_sent, charging_period_start, charging_period_end, included_messages,
             billable_messages, item_name, order_id, usage_custom_attribute1, usage_custom_attribute2,
             usage_custom_attribute3, status, reference_uuid) = row
            unique_orders.add((order_id, item_name))
            reference_uuid_map[reference_uuid] = message_id

        charge_item_uuids = {}
        for order_id, item_name in unique_orders:
            charge_item_uuid = order_service.get_charge_item_uuid_by_order_id(order_id, item_name)
            charge_item_uuids[(order_id, item_name)] = charge_item_uuid

        message_usages_list = []
        for row in rows:
            (message_id, sent_date, messages_sent, charging_period_start, charging_period_end,
             included_messages, billable_messages, item_name, order_id, usage_custom_attribute1,
             usage_custom_attribute2, usage_custom_attribute3, status, reference_uuid) = row

            charging_period = calculate_charging_period(charging_period_start, charging_period_end)

            message_usage_data = create_usage_dto(charge_item_uuid=charge_item_uuids[(order_id, item_name)],
                                                  quantity=str(billable_messages),
                                                  start_time=sent_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                  end_time=datetime(
                                                      sent_date.year,
                                                      sent_date.month,
                                                      sent_date.day,
                                                      23, 59, 59
                                                  ).strftime('%Y-%m-%d %H:%M:%S'),
                                                  charging_period=charging_period,
                                                  usageReference=reference_uuid
                                                  )

            message_usages_list.append(message_usage_data)
        response = order_service.order_usages_add(message_usages_list)
        if response.get('status') == 'success' and 'data' in response:
            success_message_ids = []
            success_entries = response['data'].get('success', [])

            for usage in success_entries:
                usage_reference = usage.get('usageReference')
                if usage_reference and usage_reference in reference_uuid_map:
                    success_message_ids.append(reference_uuid_map[usage_reference])

            if success_message_ids:
                update_status_to_active(record_list=success_message_ids, column_name='ID', table_name='MessageUsage')

        return response

    finally:
        cursor.close()
        db.close()
