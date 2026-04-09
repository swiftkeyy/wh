class CreditPolicyService:
    def estimate_job_cost(self, mode: str, num_outputs: int, premium: bool) -> int:
        base_costs = {
            "photo_enhance": 1,
            "background_replace": 2,
            "outfit_swap": 3,
            "transparent_bg": 2,
            "movie_poster": 4,
            "action_figure": 4,
            "manga_style": 3,
            "product_photo": 3,
        }
        cost = base_costs.get(mode, 3) * max(1, num_outputs)
        if premium:
            cost += 2
        return cost
