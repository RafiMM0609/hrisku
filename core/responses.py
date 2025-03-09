from typing import Any, Optional, Union
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response

# class Ok:
#     def __init__(self, data: Optional[Any]) -> None:
#         if data != None:
#             self.data = data
#         else:
#             self.data = ""

#     def json(self):
#         """
#         parse class to JSONReponse
#         """
#         return JSONResponse(content=self.data, status_code=200)

class Ok:
    def __init__(
        self, 
        meta: Optional[Any] = None,
        data: Optional[Any] = None, 
        message: Optional[Any] = None,
    ) -> None:
        self.response_shape = {
            "meta": meta if meta is not None else "",
            "data": data if data is not None else "",
            "status": "success",
            "code": 200,
            "message": message if message is not None else ""
        }

    def json(self):
        """
        Parse class to JSONResponse
        """
        return JSONResponse(content=self.response_shape, status_code=200)


class Created:
    def __init__(self, data: Optional[Any]) -> None:
        if data != None:
            self.data = data
        else:
            self.data = ""

    def json(self):
        """
        parse class to JSONReponse
        """
        return JSONResponse(content=self.data, status_code=201)

class CudResponse:
    def __init__(
        self, 
        meta: Optional[Any] = None,
        data: Optional[Any] = None, 
        message: Optional[Any] = None,
    ) -> None:
        self.response_shape = {
            "meta": meta if meta is not None else "",
            "data": data if data is not None else "",
            "status": "success",
            "code": 201,
            "message": message if message is not None else ""
        }

    def json(self):
        """
        parse class to JSONReponse
        """
        return JSONResponse(content=self.response_shape, status_code=201)

class NoContent:
    def __init__(self) -> None:
        pass

    def json(self) -> Response:
        """
        parse class to Reponse
        """
        return Response(status_code=204)


class Unauthorized:
    def __init__(
        self, message: str = "Unauthorized", custom_response: str = None
    ) -> None:
        """
        custom_response: override default json response
        default json response:
        json:{
            'message': 'Unauthorized'
        }
        status_code: 401
        """
        self.message = message
        self.custom_response = custom_response

    def json(self) -> JSONResponse:
        if self.custom_response == None:
            return JSONResponse(content={"message": f"{self.message}"}, status_code=401)
        return JSONResponse(content=self.custom_response, status_code=401)


class BadRequest:
    def __init__(
        self, 
        meta: Optional[Any] = None,
        data: Optional[Any] = None, 
        message: Optional[Any] = None,
    ) -> None:
        self.response_shape = {
            "meta": meta if meta is not None else "",
            "data": data if data is not None else "",
            "status": "failed",
            "code": 400,
            "message": message if message is not None else ""
        }
    def json(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        return JSONResponse(content=self.response_shape, status_code=400)

class Forbidden:
    def __init__(self, custom_response: Optional[Any] = None) -> None:
        """
        custom_response: override default json response
        default json response:
        json:{
            'message': 'Anda tidak memiliki hak akses untuk melakukan aksi ini!'
        }
        status_code: 403

        example override default json:
        Forbidden(custom_response={"hello": "world"}).json() -> JSONResponse(content={"hello": "world"}, status_code=403)
        """
        self.custom_response = None
        if custom_response == None:
            self.message = "Anda tidak memiliki hak akses untuk melakukan aksi ini!"
        else:
            self.custom_response = custom_response

    def json(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response == None:
            return JSONResponse(content={"message": self.message}, status_code=403)
        else:
            return JSONResponse(content=self.custom_response, status_code=403)


class NotFound:
    def __init__(
        self, message: str = "Not Found", custom_response: Optional[Any] = None
    ) -> None:
        """
        custom_response: override default json response
        default json response:
        json:{
            'message': 'Not Found'
        }
        status_code: 404
        """
        self.custom_response = None
        if custom_response != None:
            self.custom_response = custom_response
        else:
            self.message = message

    def json(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response == None:
            return JSONResponse(content={"message": self.message}, status_code=404)
        else:
            return JSONResponse(content=self.custom_response, status_code=404)


class InternalServerError:
    def __init__(
        self, message: Optional[str] = "Internal Error", error: str = None, custom_response: Optional[Any] = None
    ) -> None:
        """
        error: error string for defaut json response
        custom_response: override default json response
        default json response:
        json:{
            'error': '{error}'
        }
        status_code: 500

        example override default json:
        Forbidden(custom_response={"hello": "world"}).json() -> JSONResponse(content={"hello": "world"}, status_code=500)
        """
        self.custom_response = None
        if custom_response != None:
            self.custom_response = custom_response
        else:
            self.error = error
            self.message = message

    def http_exception(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        # OLD VERSION
        # if self.custom_response == None:
        #     raise HTTPException(status_code=500, detail=self.error)
        # else:
        #     raise HTTPException(status_code=500, detail=self.custom_response)

        if self.custom_response == None:
            return JSONResponse(content={"message": self.message, "detail": self.error}, status_code=500)
        else:
            return JSONResponse(content={"message": self.message, "detail": self.custom_response}, status_code=500)
            # return JSONResponse(content=self.custom_response, status_code=500)


class NotImplemented:
    def __init__(self, custom_response: Optional[Any] = None) -> None:
        """
        message: error string for defaut json response
        custom_response: override default json response
        default json response:
        json:{
            'message': 'Not Implemented'
        }
        status_code: 500

        example override default json:
        Forbidden(custom_response={"hello": "world"}).json() -> JSONResponse(content={"hello": "world"}, status_code=501)
        """
        self.custom_response = None
        if custom_response != None:
            self.custom_response = custom_response
        else:
            self.message = "Not Implemented"

    def json(self) -> JSONResponse:
        """
        parse class to JSONReponse
        """
        if self.custom_response == None:
            return JSONResponse(content={"message": self.message}, status_code=501)
        else:
            return JSONResponse(content=self.custom_response, status_code=501)


def common_response(
    res: Union[
        Ok,
        Created,
        NoContent,
        BadRequest,
        Unauthorized,
        Forbidden,
        NotFound,
        InternalServerError,
        CudResponse,
    ]
) -> JSONResponse:
    """
    call json function
    """
    if type(res) in [
        Ok,
        Created,
        NoContent,
        Unauthorized,
        BadRequest,
        Forbidden,
        NotFound,
        CudResponse,
    ]:
        return res.json()
    elif type(res) in [InternalServerError]:
        return res.http_exception()
    else:
        raise HTTPException(status_code=500, detail="invalid res type")
