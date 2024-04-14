"""User domain service impl"""

import http
import io
from datetime import timedelta
from typing import Optional, List, Any

import pandas as pd
from fastapi import UploadFile
from fastapi_pagination import Params
from starlette.responses import StreamingResponse

from fss.common.cache.cache import get_cache_client, Cache
from fss.common.config import configs
from fss.common.enum.enum import TokenTypeEnum
from fss.common.exception.exception import ServiceException
from fss.common.schema.schema import Token
from fss.common.service.impl.service_impl import ServiceImpl
from fss.common.util import security
from fss.common.util.excel import export_template
from fss.common.util.security import verify_password, get_password_hash
from fss.starter.system.enum.system import SystemResponseCode, SystemConstantCode
from fss.starter.system.exception.system import SystemException
from fss.starter.system.mapper.user_mapper import UserMapper, userMapper
from fss.starter.system.model.user_do import UserDO
from fss.starter.system.schema.user_schema import (
    UserQuery,
    LoginCmd,
    UserExport,
    UserCreateCmd,
)
from fss.starter.system.service.user_service import UserService


class UserServiceImpl(ServiceImpl[UserMapper, UserDO], UserService):
    def __init__(self, mapper: UserMapper):
        super(UserServiceImpl, self).__init__(mapper=mapper)
        self.mapper = mapper

    async def find_by_id(self, id: int) -> Optional[UserQuery]:
        """
        Retrieval user through user id
        :param id: user id
        :return: user or none
        """
        user_do = await self.mapper.select_by_id(id=id)
        if user_do:
            return UserQuery(**user_do.model_dump())
        else:
            return None

    async def login(self, loginCmd: LoginCmd) -> Token:
        """
        Do log in
        :param loginCmd: loginCmd
        :return: access token and refresh token
        """
        username: str = loginCmd.username
        userDO: UserDO = await self.mapper.get_user_by_username(username=username)
        if userDO is None or not await verify_password(
            loginCmd.password, userDO.password
        ):
            raise SystemException(
                SystemResponseCode.AUTH_FAILED.code,
                SystemResponseCode.AUTH_FAILED.msg,
                status_code=http.HTTPStatus.BAD_REQUEST,
            )
        access_token_expires = timedelta(minutes=configs.access_token_expire_minutes)
        refresh_token_expires = timedelta(minutes=configs.refresh_token_expire_minutes)
        access_token = await security.create_token(
            subject=userDO.id,
            expires_delta=access_token_expires,
            token_type=TokenTypeEnum.access,
        )
        refresh_token = await security.create_token(
            subject=userDO.id,
            expires_delta=refresh_token_expires,
            token_type=TokenTypeEnum.refresh,
        )
        token = Token(
            access_token=access_token,
            expired_at=int(access_token_expires.total_seconds()),
            token_type="bearer",
            refresh_token=refresh_token,
            re_expired_at=int(refresh_token_expires.total_seconds()),
        )
        cache_client: Cache = await get_cache_client()
        await cache_client.set(
            f"{SystemConstantCode.USER_KEY.msg}{userDO.id}",
            access_token,
            access_token_expires,
        )
        return token

    async def export_user_template(
        self,
    ) -> StreamingResponse:
        """
        Export empty user import template
        """
        return await export_template(schema=UserExport, file_name="user_template")

    async def import_user(self, file: UploadFile):
        """
        Import user data
        """
        contents = await file.read()
        import_df = pd.read_excel(io.BytesIO(contents))
        user_datas: UserQuery = [
            user_data for user_data in import_df.to_dict(orient="records")
        ]
        user_import_list = []
        user_name_list = []
        for user_data in user_datas:
            user_import = UserDO(**user_data)
            user_import.password = await get_password_hash(user_import.password)
            user_import_list.append(user_import)
            user_name_list.append(user_import.username)
        await file.close()
        user_list: List[UserDO] = await self.mapper.get_user_by_usernames(
            usernames=user_name_list
        )

        if user_list is not None and len(user_list) > 0:
            err_msg = ""
            for user in user_list:
                err_msg += "," + str(user.username)
            raise SystemException(
                SystemResponseCode.USER_NAME_EXISTS.code,
                SystemResponseCode.USER_NAME_EXISTS.msg + err_msg,
            )
        await self.mapper.insert_batch(data_list=user_import_list)

    async def export_user(self, params: Params) -> StreamingResponse:
        user_pages = await self.mapper.select_list_page(params=params)
        user_items = user_pages.__dict__["items"]
        user_data = []
        for user in user_items:
            user_data.append(UserQuery(**user.model_dump()))
        return await export_template(
            schema=UserQuery, file_name="user", data_list=user_data
        )

    async def register(self, data: UserCreateCmd) -> UserDO:
        """
        User register
        """
        user: UserDO = await self.mapper.get_user_by_username(username=data.username)
        if user is not None:
            raise ServiceException(
                SystemResponseCode.USER_NAME_EXISTS.code,
                SystemResponseCode.USER_NAME_EXISTS.msg,
            )
        return await self.mapper.insert(data=data)

    async def list_user(
        self, page: int, size: int, query: Any
    ) -> Optional[List[UserQuery]]:
        results: List[UserDO] = await self.mapper.select_list(
            page=page, size=size, query=query
        )
        if results is None or len(results) == 0:
            return
        return [UserQuery(**user.model_dump()) for user in results]


def get_user_service() -> UserService:
    return UserServiceImpl(mapper=userMapper)