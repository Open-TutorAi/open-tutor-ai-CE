import os
import builtins
from pathlib import Path

from fastapi import Depends

# Set DATA_DIR to backend/data by default
backend_dir = Path(__file__).parent.parent
data_dir = backend_dir / "data"
data_dir.mkdir(exist_ok=True)

if "DATA_DIR" not in os.environ:
    os.environ["DATA_DIR"] = str(data_dir.absolute())
    print(f"Setting default DATA_DIR to: {os.environ['DATA_DIR']}")

original_print = builtins.print

# Signature line to detect the WebUI banner (use a unique line from that banner)
WEBUI_SIGNATURE_LINE = """
 ██████╗ ██████╗ ███████╗███╗   ██╗    ██╗    ██╗███████╗██████╗ ██╗   ██╗██╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║    ██║    ██║██╔════╝██╔══██╗██║   ██║██║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║    ██║ █╗ ██║█████╗  ██████╔╝██║   ██║██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║    ██║███╗██║██╔══╝  ██╔══██╗██║   ██║██║
╚██████╔╝██║     ███████╗██║ ╚████║    ╚███╔███╔╝███████╗██████╔╝╚██████╔╝██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝     ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝
"""


def custom_print(*args, **kwargs):
    output = " ".join(str(arg) for arg in args)

    # Detect the WebUI banner using a unique line
    if WEBUI_SIGNATURE_LINE in output:
        if os.environ.get("SUPPRESS_WEBUI_BANNER") == "true":
            return  # Suppress the banner
    return original_print(*args, **kwargs)


builtins.print = custom_print


def patch_teacher_model_access():
    try:
        from open_webui.models.users import Users
        from open_webui.utils import access_control as access_control_module
        from open_webui.utils import auth as auth_module

        original_get_permissions = access_control_module.get_permissions
        original_get_verified_user = auth_module.get_verified_user

        def patched_get_permissions(user_id, default_permissions=None):
            permissions = original_get_permissions(user_id, default_permissions)
            if not isinstance(permissions, dict):
                permissions = {}

            user = Users.get_user_by_id(user_id)
            if not user or user.role != "teacher":
                return permissions

            workspace_permissions = permissions.setdefault("workspace", {})
            workspace_permissions["models"] = True
            permissions.setdefault("model", {})["enabled"] = True
            return permissions

        def patched_get_verified_user(user=Depends(auth_module.get_current_user)):
            if user.role in {"user", "admin", "teacher"}:
                return user

            return original_get_verified_user(user=user)

        access_control_module.get_permissions = patched_get_permissions
        auth_module.get_verified_user = patched_get_verified_user

        print("Applied teacher model access patch")
    except Exception as exc:
        print(f"Failed to apply teacher model access patch: {exc}")


patch_teacher_model_access()
