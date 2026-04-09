from app.core.config import settings


class PricingPolicyService:
    def get_welcome_credits(self) -> int:
        return settings.default_free_credits

    def get_job_price(self, mode: str) -> int:
        return settings.job_pricing.get(mode, 3)

    def pricing_screen_text(self) -> str:
        transparent_price = self.get_job_price("transparent_bg")
        poster_price = self.get_job_price("movie_poster")
        figure_price = self.get_job_price("action_figure")
        packs_text = "\n".join(
            [
                f"- {pack['title']}: {pack['price_stars']} Stars, {pack['credits']} кредитов"
                for pack in settings.purchase_packs
            ]
        )
        plans_text = "\n".join(
            [
                f"- {plan['title']}: {plan['price_stars']} Stars/мес, {plan['credits_monthly']} кредитов в месяц"
                for plan in settings.subscription_plans
            ]
        )
        return (
            "Тарифы WHYNOT Photoshop\n\n"
            "Кредиты расходуются по режимам:\n"
            f"- Удалить фон: {transparent_price} кредита\n"
            f"- Кинопостер: {poster_price} кредита\n"
            f"- Экшн-фигурка: {figure_price} кредита\n\n"
            "Пакеты кредитов:\n"
            f"{packs_text}\n\n"
            "Подписки:\n"
            f"{plans_text}"
        )

    def get_purchase_pack(self, sku: str) -> dict | None:
        return next((pack for pack in settings.purchase_packs if pack["sku"] == sku), None)

    def get_subscription_plan(self, code: str) -> dict | None:
        return next((plan for plan in settings.subscription_plans if plan["code"] == code), None)
