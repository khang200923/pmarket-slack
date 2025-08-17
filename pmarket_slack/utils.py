import pmarket_slack.pmarket_slack as ps
from copy import deepcopy

def bet_amount(
    market_data,
    shares_amount: float,
    yes_or_no: bool
):
    shares_bef = market_data["bought_shares"]
    lmsr_bef = ps.get_lmsr_info(deepcopy(shares_bef), market_data["liquidity"])
    shares_aft = deepcopy(shares_bef)
    if yes_or_no:
        shares_aft[0] += shares_amount
    else:
        shares_aft[1] += shares_amount
    lmsr_aft = ps.get_lmsr_info(deepcopy(shares_aft), market_data["liquidity"])
    return lmsr_aft["cost_func"] - lmsr_bef["cost_func"]