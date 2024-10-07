from ab_py.common.ab_exception import ABException
from ab_py.exsited.exsited_sdk import ExsitedSDK
from service.exsited_service import ExsitedService
from tests.common.common_data import CommonData


class OrderService:
    def __init__(self, exsited_service: ExsitedService):

        self.exsited_service = exsited_service

    def get_charge_item_uuid_by_order_id(self, order_id, item_name):
        sdk = self.exsited_service.get_sdk()
        try:
            response = sdk.order.details(id=order_id)
            if response.order:
                for line in response.order.lines:
                    if line.itemName == item_name:
                        return line.chargeItemUuid
            return None
        except ABException as ab:
            error_code = None
            if ab.get_errors() and "errors" in ab.raw_response:
                error_code = ab.raw_response["errors"][0].get("code", None)

    def order_usage_add(self, request_data):
        sdk = self.exsited_service.get_sdk()

        try:
            response = sdk.order.add_usage(request_data=request_data)
            if response:
                return response
            else:
                return "error"
        except ABException as ab:
            error_code = None
            if ab.get_errors() and "errors" in ab.raw_response:
                error_code = ab.raw_response["errors"][0]
            return error_code
