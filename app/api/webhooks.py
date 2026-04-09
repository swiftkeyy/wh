from fastapi import APIRouter, Header, HTTPException, Request, status

from app.bot.runtime import handle_update
from app.core.config import settings
from app.services.billing import BillingService

router = APIRouter()
billing_service = BillingService()


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")
    payload = await request.json()
    await handle_update(payload)
    return {"accepted": True}


@router.post("/payments/provider")
async def payment_webhook(request: Request) -> dict[str, bool | str]:
    payload = await request.json()
    if payload.get("event") == "payment.succeeded":
        result_text = await billing_service.confirm_successful_payment(
            telegram_user_id=int(payload["telegram_user_id"]),
            payload=payload["invoice_payload"],
            telegram_payment_charge_id=payload["payment_charge_id"],
            provider_payment_charge_id=payload.get("provider_payment_charge_id", payload["payment_charge_id"]),
            total_amount=int(payload["total_amount"]),
        )
        return {"accepted": True, "result": result_text}
    return {"accepted": True, "result": "ignored"}
