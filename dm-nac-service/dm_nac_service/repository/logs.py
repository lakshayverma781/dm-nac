from fastapi.responses import JSONResponse
# data
from dm_nac_service.config.database import get_database
from dm_nac_service.models.logs import api_logs
# resource
from dm_nac_service.resource.log_config import logger
# config
# from lotuspay_nach_service.utils import _raise


async def insert(log_object):
    try:

        log_object = log_object.dict()
        Database = get_database()

        channel = log_object.get("channel")
        request_url = log_object.get("request_url")
        request_method = log_object.get("request_method")
        params = log_object.get("params")
        request_body = log_object.get("request_body")
        response_body = log_object.get("response_body")
        status_code = log_object.get("status_code")
        api_call_duration = log_object.get("api_call_duration")
        request_time = log_object.get("request_time")
        log_info = {'channel': channel,
                    'request_url': request_url,
                    'request_method': request_method,
                    'params': params,
                    'request_body': request_body,
                    'response_body': response_body,
                    'status_code': status_code,
                    'api_call_duration': api_call_duration,
                    'request_time': request_time}
        insert_query = api_logs.insert().values(log_info)
        await Database.execute(insert_query)
        logger.info(f"{channel} LOGS SUCCESSFULLY INSERTED INTO LOGS TABLE")
    except Exception as e:
        logger.exception(f"REPOSITORY - LOGS - INSERT - {e.args[0]}")
        return JSONResponse(status_code=500, content={"message": f"{e.args[0]}"})
