from app.services.pricing_policy import PricingPolicyService


def test_pricing_policy_returns_configured_values() -> None:
    policy = PricingPolicyService()
    assert policy.get_welcome_credits() > 0
    assert policy.get_job_price("transparent_bg") >= 1


def test_pricing_screen_contains_key_modes() -> None:
    policy = PricingPolicyService()
    text = policy.pricing_screen_text()
    assert "Удалить фон" in text
    assert "Кинопостер" in text
    assert "Stars" in text
