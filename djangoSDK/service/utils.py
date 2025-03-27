from contextlib import closing
import logging
import MySQLdb
from datetime import timedelta, datetime
from exsited.exsited.order.dto.usage_dto import UsageDataDTO
from service.exsited_service import ExsitedService
from service.order_service import OrderService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 200
ALLOWED_TABLES = {"CallUsage", "MessageUsage"}
ALLOWED_COLUMNS = {"ID"}


def connect_to_db():
    return MySQLdb.connect(
        host="",
        user="",
        passwd="",
        db=""
    )


def process_usages_in_chunks(order_service, usage_list, reference_uuid_map, table_name):
    success_data = []
    failed_data = []

    for i in range(0, len(usage_list), CHUNK_SIZE):
        success_ids = []
        chunk = usage_list[i:i + CHUNK_SIZE]
        response = order_service.order_usages_add(chunk)
        logger.info(f"Chunk {i // CHUNK_SIZE + 1}")

        if response.get("status") == "success" and "data" in response:
            success_ids.extend(
                reference_uuid_map[usage.get("usageReference")]
                for usage in response["data"].get("success", [])
                if usage.get("usageReference") in reference_uuid_map
            )
            if success_ids:
                update_status_to_active(success_ids, "ID", table_name)
            success_data.extend({
                                    "charge_item_uuid": usage.get("chargeItemUuid"),
                                    "charging_period": usage.get("chargingPeriod"),
                                    "quantity": usage.get("quantity"),
                                    "start_time": usage.get("startTime"),
                                    "end_time": usage.get("endTime"),
                                    "type": usage.get("type"),
                                    "usage_reference": usage.get("usageReference")
                                }
                                for usage in response.get("data", {}).get("success", [])
                                )
            failed_data.extend({
                                   "charge_item_uuid": usage.get("chargeItemUuid"),
                                   "charging_period": usage.get("chargingPeriod"),
                                   "quantity": usage.get("quantity"),
                                   "start_time": usage.get("startTime"),
                                   "end_time": usage.get("endTime"),
                                   "type": usage.get("type"),
                                   "usage_reference": usage.get("usageReference")
                               }
                               for usage in response.get("data", {}).get("failed", []))
        print(f"successful items: {len(response.get("data", {}).get("success", []))}")
        print(f"failed items: {len(response.get("data", {}).get("failed", []))}")
    return {
        "data": {
            "success": success_data,
            "failed": failed_data
        }
    }


def calculate_charging_period(start_date, end_date):
    if not start_date or not end_date:
        logger.warning("Charging period start or end date is None.")
        return None

    return f"{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"


def create_usage_dto(charge_item_uuid, quantity, start_time, end_time, charging_period, usage_reference):
    if not charge_item_uuid:
        logger.error(f"Charge item UUID is missing for reference: {usage_reference}")
        return None

    return UsageDataDTO(
        chargeItemUuid=charge_item_uuid,
        quantity=quantity,
        startTime=start_time,
        endTime=end_time,
        type="INCREMENTAL",
        chargingPeriod=charging_period,
        usageReference=usage_reference
    )


def update_status_to_active(record_list, column_name, table_name):
    try:
        if table_name not in ALLOWED_TABLES:
            logger.error(f"Invalid table name: {table_name}")
            return
        if column_name not in ALLOWED_COLUMNS:
            logger.error(f"Invalid column name: {column_name}")
            return
        if not record_list:
            logger.info("No records to update.")
            return

        record_list_str = ", ".join(["%s"] * len(record_list))
        query = f"UPDATE {table_name} SET Status = 'ACTIVE' WHERE {column_name} IN ({record_list_str})"
        with closing(connect_to_db()) as db, closing(db.cursor()) as cursor:
            cursor.execute(query, tuple(record_list))
            db.commit()
            logger.info(f"Updated {len(record_list)} records to ACTIVE in {table_name}.")
    except MySQLdb.Error as e:
        logger.error(f"Database error while updating records: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error while updating records: {e}")


def fetch_call_usage():
    try:
        with closing(connect_to_db()) as db, closing(db.cursor()) as cursor:
            cursor.execute("""
                SELECT ID, CallStart, CallDurationSec, CallDestination, CallType, ItemName, OrderID, 
                       ChargingPeriodStart, ChargingPeriodEnd, Status, ReferenceUUID 
                FROM CallUsage 
                WHERE Status = 'INACTIVE'
            """)
            rows = cursor.fetchall()

        if not rows:
            logger.info("No inactive call usage records found.")
            return {"status": "success", "message": "No inactive call usage records found."}

        unique_orders = set()
        reference_uuid_map = {}

        exsited_service = ExsitedService()
        order_service = OrderService(exsited_service)

        for row in rows:
            (call_id, call_start, call_duration, call_destination, call_type, item_name, order_id,
             charging_period_start, charging_period_end, status, reference_uuid) = row

            if not call_start or not charging_period_start or not charging_period_end or not item_name or not order_id:
                logger.warning(f"Skipping record {call_id} due to missing date values.")
                continue

            unique_orders.add((order_id, item_name))
            reference_uuid_map[reference_uuid] = call_id

        charge_item_uuids = {
            (order_id, item_name): order_service.get_charge_item_uuid_by_order_id(order_id, item_name)
            for order_id, item_name in unique_orders
        }

        call_usage_list = []
        for row in rows:
            (call_id, call_start, call_duration, call_destination, call_type, item_name, order_id,
             charging_period_start, charging_period_end, status, reference_uuid) = row

            if not all([call_start, call_duration, charging_period_start, charging_period_end, reference_uuid]):
                logger.warning(f"Skipping record {call_id} due to missing required values.")
                continue

            call_end = call_start + timedelta(seconds=call_duration)
            charging_period = calculate_charging_period(charging_period_start, charging_period_end)

            usage_data = create_usage_dto(
                charge_item_uuid=charge_item_uuids.get((order_id, item_name)),
                quantity="1",
                start_time=call_start.strftime('%Y-%m-%d %H:%M:%S'),
                end_time=call_end.strftime('%Y-%m-%d %H:%M:%S'),
                charging_period=charging_period,
                usage_reference=reference_uuid
            )

            if usage_data:
                call_usage_list.append(usage_data)
        print(f"total usage data: {len(call_usage_list)}")
        return process_usages_in_chunks(order_service, call_usage_list, reference_uuid_map, "CallUsage")

    except MySQLdb.Error as e:
        logger.error(f"Database error in fetch_call_usage: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in fetch_call_usage: {e}")

    return {"status": "error", "message": "An error occurred while fetching call usage."}


def fetch_message_usage():
    try:
        with closing(connect_to_db()) as db, closing(db.cursor()) as cursor:
            cursor.execute("""
                SELECT ID, BillingPeriod, MessagesSent, ChargingPeriodStart, ChargingPeriodEnd, 
                       IncludedMessages, BillableMessages, ItemName, OrderID, UsageCustomAttribute1, 
                       UsageCustomAttribute2, UsageCustomAttribute3, Status, ReferenceUUID  
                FROM MessageUsage
                WHERE Status = 'INACTIVE'
            """)
            rows = cursor.fetchall()

        if not rows:
            logger.info("No inactive message usage records found.")
            return {"status": "success", "message": "No inactive message usage records found."}

        unique_orders = set()
        reference_uuid_map = {}

        exsited_service = ExsitedService()
        order_service = OrderService(exsited_service)

        for row in rows:
            (message_id, sent_date, messages_sent, charging_period_start, charging_period_end, included_messages,
             billable_messages, item_name, order_id, usage_custom_attribute1, usage_custom_attribute2,
             usage_custom_attribute3, status, reference_uuid) = row

            if not sent_date or not charging_period_start or not charging_period_end or not item_name or not order_id:
                logger.warning(f"Skipping record {message_id} due to missing date values.")
                continue

            unique_orders.add((order_id, item_name))
            reference_uuid_map[reference_uuid] = message_id

        charge_item_uuids = {
            (order_id, item_name): order_service.get_charge_item_uuid_by_order_id(order_id, item_name)
            for order_id, item_name in unique_orders
        }

        message_usages_list = []
        for row in rows:
            (message_id, sent_date, messages_sent, charging_period_start, charging_period_end, included_messages,
             billable_messages, item_name, order_id, usage_custom_attribute1, usage_custom_attribute2,
             usage_custom_attribute3, status, reference_uuid) = row

            charging_period = calculate_charging_period(charging_period_start, charging_period_end)

            message_usage_data = create_usage_dto(
                charge_item_uuid=charge_item_uuids.get((order_id, item_name)),
                quantity=str(billable_messages),
                start_time=sent_date.strftime('%Y-%m-%d %H:%M:%S'),
                end_time=datetime(
                    sent_date.year if sent_date else 1970,
                    sent_date.month if sent_date else 1,
                    sent_date.day if sent_date else 1,
                    23, 59, 59
                ).strftime('%Y-%m-%d %H:%M:%S'),
                charging_period=charging_period,
                usage_reference=reference_uuid
            )

            if message_usage_data:
                message_usages_list.append(message_usage_data)

        return process_usages_in_chunks(order_service, message_usages_list, reference_uuid_map, "MessageUsage")

    except MySQLdb.Error as e:
        logger.error(f"Database error in fetch_message_usage: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in fetch_message_usage: {e}")

    return {"status": "error", "message": "An error occurred while fetching message usage."}
