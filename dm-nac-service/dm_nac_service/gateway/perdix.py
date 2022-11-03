import os
import shutil

import requests
import json
from fastapi.encoders import jsonable_encoder

from datetime import datetime
from dm_nac_service.resource.log_config import logger
from dm_nac_service.resource.generics import response_to_dict, hanlde_response_body, hanlde_response_status
from dm_nac_service.resource.generics import response_to_dict
from fastapi.responses import JSONResponse
from dm_nac_service.schemas.logs import LogBase
import dm_nac_service.repository.logs as api_logs
# from dm_nac_service.data.database import insert_logs, insert_logs_all
from dm_nac_service.commons import get_env_or_fail


PERDIX_SERVER = 'perdix-server'


async def perdix_post_login():
    """ Generic Post Method for perdix login """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        username = get_env_or_fail(PERDIX_SERVER, 'username', PERDIX_SERVER + ' username not configured')
        password = get_env_or_fail(PERDIX_SERVER, 'password', PERDIX_SERVER + ' password not configured')
        url = validate_url + f'/oauth/token?client_id=application&client_secret=mySecretOAuthSecret&grant_type=password&password={password}&scope=read+write&skip_relogin=yes&username={username}'
        str_url = str(url)

        login_context_response = requests.post(url)
        login_context_dict = response_to_dict(login_context_response)
        api_call_duration = str(login_context_response.elapsed.total_seconds()) + ' sec'
        str_data = str(login_context_dict)
        info = (str_data[:4950] + '..') if len(str_data) > 4950 else str_data
        log_info = LogBase(
            channel='northernarc',
            request_url=url,
            request_method='POST',
            params=f"",
            request_body="",
            response_body=str(info),
            status_code=str(login_context_response.status_code),
            api_call_duration=api_call_duration,
            request_time=str(datetime.now())
        )
        await api_logs.insert(log_info)
        # Checking for successful login
        if(login_context_response.status_code == 200):
            access_token = login_context_dict.get('access_token')

           
           
            result = JSONResponse(status_code=200, content={"access_token": access_token})
           
        else:
            
            

            result = JSONResponse(status_code=500, content=login_context_dict)
           


    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with perdix_post_login function, {e.args[0]}")
        
        
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Perdix Login - {e.args[0]}"})

    return result


async def perdix_fetch_loan(loan_id):
    """ Generic Post Method for perdix fetch customer """
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        url = validate_url + f'/api/individualLoan/{loan_id}'
        str_url = str(url)


        login_token = await perdix_post_login()

        fetch_loan_response_status = hanlde_response_status(login_token)
        fetch_loan_response_body = hanlde_response_body(login_token)

        # If Login is success
        if(fetch_loan_response_status == 200):
            login_token = fetch_loan_response_body.get('access_token')
            headers = {
                "Content-Type": "application/json",
                "Content-Length": "0",
                "User-Agent": 'My User Agent 1.0',
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Authorization": f"bearer {login_token}"
            }

            loan_context_response = requests.get(url, headers=headers)
            loan_context_response_dict = response_to_dict(loan_context_response)
            
            api_call_duration = str(loan_context_response.elapsed.total_seconds()) + ' sec'
            str_data = str(loan_context_response_dict)
            info = (str_data[:4950] + '..') if len(str_data) > 4950 else str_data
            log_info = LogBase(
                channel='northernarc',
                request_url=url,
                request_method='POST',
                params=f"{loan_id}",
                request_body="",
                response_body=str(info),
                status_code=str(loan_context_response.status_code),
                api_call_duration=api_call_duration,
                request_time=str(datetime.now())
            )
            await api_logs.insert(log_info)
            # If Loan ID is present
            if(loan_context_response.status_code == 200):
                
                loan_context_response_content = loan_context_response.content
                loan_context_dict = json.loads(loan_context_response_content.decode('utf-8'))
                
               

                
               
                result = JSONResponse(status_code=200, content=loan_context_dict)
            else:
                response = loan_context_response.content.decode('utf-8')
               
                not_found_response = {"message": "Loan Not found in Perdix"}
                result = JSONResponse(status_code=404, content=not_found_response)
        
        else:
            fetch_loan_error = fetch_loan_response_body
           

            result = JSONResponse(status_code=500, content=fetch_loan_error)

    except Exception as e:
        logger.exception(f"{datetime.now()} - Issue with perdix_fetch_loan function, {e.args[0]}")
        
        result = JSONResponse(status_code=500,
                              content={"message": f"Error Occurred at Perdix - Fetch Loan - {e.args[0]}"})
    return result


async def perdix_update_loan(loan_data):
    """ Generic put Method to update perdix customer """
    try:
        print(loan_data)
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url', PERDIX_SERVER + ' base-url not configured')
        url = validate_url + f'/api/individualLoan'
        str_url = str(url)
        login_token = await perdix_post_login()
        login_token_decode = jsonable_encoder(login_token)
        print("STATUS",login_token.status_code)
       
        response_body = login_token_decode.get('body')
        response_body_json = json.loads(response_body)
        print(response_body_json)

        fetch_loan_response_decode_status = login_token_decode.get('status_code')
        print(fetch_loan_response_decode_status)

        # If login is success
        if (fetch_loan_response_decode_status == 200):
            login_token = response_body_json.get('access_token')
            headers = {
                "Content-Type": "application/json",
                "Content-Length": "0",
                "User-Agent": 'My User Agent 1.0',
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Authorization": f"bearer {login_token}"
            }
            str_url = str(url)
            loan_update_response = requests.put(url, json=loan_data, headers=headers)
            loan_update_response_dict = response_to_dict(loan_update_response)
            api_call_duration = str(loan_update_response.elapsed.total_seconds()) + ' sec'
            str_data = str(loan_update_response_dict)
            info = (str_data[:4950] + '..') if len(str_data) > 4950 else str_data
            log_info = LogBase(
                channel='northernarc',
                request_url=url,
                request_method='PUT',
                params=f"",
                request_body=str(loan_data),
                response_body=str(info),
                status_code=str(loan_update_response.status_code),
                api_call_duration=api_call_duration,
                request_time=str(datetime.now())
            )
            await api_logs.insert(log_info)
            
            # If loan update success
            if(loan_update_response.status_code == 200):
                
               

                result = JSONResponse(status_code=200, content=loan_update_response_dict)
            else:
                logger.error(f"unable to update perdix loan ,{loan_update_response_dict}")
               
                loan_update_unsuccess = {"error": 'Error from Perdix', "error_description": loan_update_response_dict}
                result = JSONResponse(status_code=500, content=loan_update_unsuccess)
        else:
            response_body = login_token_decode.get('body')
            response_body_json = json.loads(response_body)
            response_body_error = response_body_json.get('error')
            response_body_description = response_body_json.get('error_description')
           
            login_unsuccess = {"error": response_body_error, "error_description": response_body_description}
            result = JSONResponse(status_code=500, content=login_unsuccess)
           

    except Exception as e:
        logger.exception(f"Issue with perdix_update_loan function, {e.args[0]}")
        
        result = JSONResponse(status_code=500, content={"message": f"Error Occurred at Perdix - Update Loan - {e.args[0]}"})
    return result


# async def download_file_from_stream(
#     doc_id: str
# ):
#     """genric method for download file from stream url"""
#     try:
#         validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url',
#                                        PERDIX_SERVER + ' perdix-base-url not configured')
#         url = validate_url + f'/api/stream/{doc_id}'
      

#         download_file_response = requests.get(url)
       
#         if(download_file_response.status_code == 200):
#             download_file_response_headers = download_file_response.headers
#             download_file_response_headers_content = download_file_response_headers.get('Content-Disposition')
#             find_filename = download_file_response_headers_content.split('filename=', 1)
#             found_filename = find_filename[1]
#             found_file_ext = found_filename.split('.')
#             new_file_name = doc_id + '.' + found_file_ext[1]
            

#             file_path = os.path.abspath(('./static/'))

#             with open(new_file_name, 'wb') as f:
#                 f.write(download_file_response.content)
#                 basename = f.name
                
#                 move_item = shutil.copy(basename, file_path)
                
#                 if os.path.exists(move_item):
#                     remove = os.remove(basename)
#                 else:
                    
                    
#                     move_item = shutil.move(basename, file_path)
            
#             result = JSONResponse(status_code=200,content={"filename": new_file_name})
           
#         else:
#             download_file_response_json = json.loads(download_file_response.content.decode('utf-8'))
#             app_log_error = {"error": 'NAC', "error_description": download_file_response_json}
            
#             result = JSONResponse(status_code=404, content=app_log_error)
#     except Exception as e:
#         logger.exception(f"Issue with perdix_update_loan function, {e.args[0]}")
        
#         result = JSONResponse(status_code=500,content={"message": f"Error Occurred at Perdix - Update Loan - {e.args[0]}"})
#     return result



async def download_file_from_stream(
    doc_id: str
):
    """genric method for download file from stream url"""
    try:
        validate_url = get_env_or_fail(PERDIX_SERVER, 'perdix-base-url',
                                       PERDIX_SERVER + ' perdix-base-url not configured')
        url = validate_url + f'/api/stream/{doc_id}'
      

        download_file_response = requests.get(url)
       
        
        download_file_response_headers = download_file_response.headers
        download_file_response_headers_content = download_file_response_headers.get('Content-Disposition')
        find_filename = download_file_response_headers_content.split('filename=', 1)
        found_filename = find_filename[1]
        found_file_ext = found_filename.split('.')
        new_file_name = doc_id + '.' + found_file_ext[1]
            

        file_path = os.path.abspath(('./static/'))

        with open(new_file_name, 'wb') as f:
            f.write(download_file_response.content)
            basename = f.name
            
            move_item = shutil.copy(basename, file_path)
            
            if os.path.exists(move_item):
                remove = os.remove(basename)
            else:
                
                
                move_item = shutil.move(basename, file_path)
        api_call_duration = str(download_file_response.elapsed.total_seconds()) + ' sec'
        # info = (str_data[:4950] + '..') if len(str_data) > 4950 else str_data
        log_info = LogBase(
                channel='northernarc',
                request_url=url,
                request_method='GET',
                params=f"{doc_id}",
                request_body="",
                response_body="",
                status_code=download_file_response.status_code,
                api_call_duration=api_call_duration,
                request_time=str(datetime.now()))
        await api_logs.insert(log_info)
        return new_file_name
           
       
            
       
    except Exception as e:
        logger.exception(f"GATEWAY - DOWNLOAD_FILE, {e.args[0]}")
        
        return JSONResponse(status_code=500,content={"message": f" {e.args[0]}"})