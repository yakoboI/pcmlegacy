import time
import uuid
from typing import Any, Dict, Optional
from portalsdk import APIContext, APIMethodType, APIRequest
class MpesaConfigError(Exception):
    """Raised when required MPesa configuration is missing."""
class MpesaRequestError(Exception):
    """Raised when the MPesa API responds with an error."""
def normalize_msisdn(phone_number: str, default_country_code: str = "255") -> str:
    """
    Convert a phone number into the MSISDN format required by MPesa (no plus sign, country code prefixed).
    """
    if not phone_number:
        raise ValueError("Phone number is required.")
    cleaned = "".join(ch for ch in phone_number if ch.isdigit())
    if cleaned.startswith(default_country_code):
        msisdn = cleaned
    elif cleaned.startswith("0"):
        msisdn = f"{default_country_code}{cleaned[1:]}"
    else:
        msisdn = f"{default_country_code}{cleaned}"
    if len(msisdn) < 11 or len(msisdn) > 15:
        raise ValueError("Invalid phone number length for MPesa.")
    return msisdn
class MpesaClient:
    """
    Thin wrapper around the MPesa Portal SDK for click-to-pay flows.
    """
    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger
        required_keys = [
            "MPESA_API_KEY",
            "MPESA_PUBLIC_KEY",
            "MPESA_SERVICE_PROVIDER_CODE",
        ]
        missing = [key for key in required_keys if not config.get(key)]
        if missing:
            raise MpesaConfigError(f"Missing MPesa configuration: {', '.join(missing)}")
        self.address = config.get("MPESA_IPG_ADDRESS", "openapi.m-pesa.com")
        self.port = int(config.get("MPESA_IPG_PORT", 443))
        self.origin = config.get("MPESA_IPG_ORIGIN", "*")
        self.ssl = True
        default_env = config.get("MPESA_ENV", "sandbox").strip("/").lower()
        prefix = f"/{default_env}/ipg/v2/vodacomTZN"
        self.session_path = config.get(
            "MPESA_SESSION_PATH", f"{prefix}/getSession/"
        )
        self.c2b_path = config.get(
            "MPESA_C2B_SINGLE_STAGE_PATH", f"{prefix}/c2bPayment/singleStage/"
        )
        self.session_wait_seconds = int(
            config.get("MPESA_SESSION_READY_DELAY", 30)
        )
        self.country = config.get("MPESA_COUNTRY", "TZN")
        self.currency = config.get("MPESA_CURRENCY", "TZS")
        self.service_provider_code = config["MPESA_SERVICE_PROVIDER_CODE"]
    def _base_context(
        self,
        api_key: str,
        method_type: APIMethodType,
        path: str,
    ) -> APIContext:
        ctx = APIContext()
        ctx.api_key = api_key
        ctx.public_key = self.config.get("MPESA_PUBLIC_KEY")
        ctx.ssl = self.ssl
        ctx.method_type = method_type
        ctx.address = self.address
        ctx.port = self.port
        ctx.path = path
        ctx.add_header("Origin", self.origin)
        ctx.add_header("Content-Type", "application/json")
        return ctx
    def _execute(self, context: APIContext) -> Dict[str, Any]:
        api_request = APIRequest(context)
        try:
            response = api_request.execute()
        except Exception as exc:
            raise MpesaRequestError(str(exc)) from exc
        payload = {
            "status_code": response.status_code,
            "headers": dict(response.headers or {}),
            "body": response.body,
        }
        if response.status_code >= 400:
            raise MpesaRequestError(f"MPesa error: {payload}")
        return payload
    def get_session_id(self) -> str:
        context = self._base_context(
            api_key=self.config.get("MPESA_API_KEY"),
            method_type=APIMethodType.GET,
            path=self.session_path,
        )
        result = self._execute(context)
        body = result.get("body") or {}
        session_id = body.get("output_SessionID")
        if not session_id:
            raise MpesaRequestError("MPesa session response missing SessionID.")
        return session_id
    def pay_single_stage(
        self,
        *,
        amount: str,
        msisdn: str,
        conversation_id: str,
        transaction_reference: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session_id = self.get_session_id()
        time.sleep(max(1, self.session_wait_seconds))
        context = self._base_context(
            api_key=session_id,
            method_type=APIMethodType.POST,
            path=self.c2b_path,
        )
        context.add_parameter("input_Amount", str(amount))
        context.add_parameter("input_Country", self.country)
        context.add_parameter("input_Currency", self.currency)
        context.add_parameter("input_CustomerMSISDN", msisdn)
        context.add_parameter(
            "input_ServiceProviderCode", self.service_provider_code
        )
        context.add_parameter(
            "input_ThirdPartyConversationID", conversation_id
        )
        context.add_parameter(
            "input_TransactionReference", transaction_reference
        )
        context.add_parameter("input_PurchasedItemsDesc", description[:128])
        if metadata:
            for key, value in metadata.items():
                if value is not None:
                    context.add_parameter(str(key), str(value))
        return self._execute(context)
def generate_conversation_id() -> str:
    return uuid.uuid4().hex
def generate_transaction_reference(material_id: int) -> str:
    seed = uuid.uuid4().hex[:6].upper()
    return f"MAT{material_id}{seed}"
