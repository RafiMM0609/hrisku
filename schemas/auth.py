from typing import List, Optional, TypedDict
from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    email: str
    name: str
    phone: str
    face_id: Optional[str]
    # password: Optional[str]
class MenuDict(TypedDict):
    id: int
    url: str
    menu_name: str
    icon: str
    is_has_child: bool
    is_active: bool
    order: int
    sub_menu: List[dict]  # MenuDict
class FirstLoginUserRequest(BaseModel):
    email: str
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    email: str
    password: str



class LoginSuccessResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    token: str

class Organization(BaseModel):
    id:int
    name:str
class RegisRequest(BaseModel):
    email: str
    name: str
    password: str
    photo_user: Optional[str]
    photo_face: str
    role_id: Optional[int]
class MeSuccessResponse(BaseModel):
    id: str
    email: str
    username: str
    name: str
    is_active: bool
    phone: str
    refreshed_token: str
    image: str
    role: Organization
    unit_kerja: List[Organization]
    cabang: List[Organization]
    wilayah: Optional[Organization]
    zona: Optional[Organization]
    jenis_kelamin: str
    code_user: str


class ChangeUserProfileRequest(BaseModel):
    username: str
    email: str
    NIK: Optional[str]
    signature_path: Optional[str]
    telegram: Optional[str]


class LogoutSuccessResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangePasswordSuccessResponse(BaseModel):
    message: str = "password berhasil diganti"


class ForgotPasswordSendEmailRequest(BaseModel):
    email: str


class ForgotPasswordSendEmailResponse(BaseModel):
    message: str = "success kirim email ganti password, silahkan cek email anda"


class ForgotPasswordChangePasswordRequest(BaseModel):
    token: str
    password: str
    
class UpdateProfileRequest(BaseModel):
    name: str
    email: str
    username: str
    photo_user: Optional[str]


class ForgotPasswordChangePasswordResponse(BaseModel):
    message: str = "success menganti password anda"


class PermissionsResponse(BaseModel):
    class DetailPermission(BaseModel):
        id: int
        permission: str

        class DetailModule(BaseModel):
            id: int
            nama: str

        module: DetailModule

    results: List[DetailPermission]


class MenuResponse(BaseModel):
    class MenuDetail(BaseModel):
        id: int
        url: str
        name: str
        icon: str
        order: int
        is_has_child: bool

        class SubMenuDetail(BaseModel):
            id: int
            url: str
            name: str
            icon: str
            is_has_child: bool
            order: int
            sub_menu: list

        sub_menu: List[SubMenuDetail]

    results: List[MenuDetail]
