from copy import deepcopy
import json
import pmarket_slack.pmarket_slack as ps

true = True
false = False

def home_view(
    user_id: str
):
    user = ps.get_user_data(user_id)
    balance = user["balance"]
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Your account",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Balance*: {balance:.0f} :dollar:"
                }
            }
        ]
    }

def pmarket_view(
    market_id: int,
):
    print("hiii")
    market = ps.get_market_data(market_id)
    is_resolved = market['is_resolved']
    resolution = market['resolution']
    resolution_text = ":question: N/A"
    if resolution is not None:
        resolution_text = ":white_check_mark: YES" if resolution == 0 else ":x: NO"

    menu_options = [
        {
            "text": {
                "type": "plain_text",
                "text": "Resolve :white_check_mark: YES"
            },
            "value": "resolve_yes"
        },
        {
            "text": {
                "type": "plain_text",
                "text": "Resolve :x: NO"
            },
            "value": "resolve_no"
        },
        {
            "text": {
                "type": "plain_text",
                "text": "Resolve :question: N/A"
            },
            "value": "resolve_na"
        }
    ]
    context_elements = [
        {
            "type": "mrkdwn",
            "text": f"*{market['liquidity']:.0f}* :dollar: liquidity"
        }
    ]
    probability_section = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{market['prob'][0]*100:.0f}%* chance"
            },
        },
    ]
    if is_resolved:
        print("yessssss")
        menu_options = [
            {
                "text": {
                    "type": "plain_text",
                    "text": "Unresolve"
                },
                "value": "unresolve"
            },
        ]
        probability_section = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Resolved *{resolution_text}*"
                },
            },
        ]

    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{market['title']}*"
                },
                "accessory": {
                    "type": "overflow",
                    "options": menu_options,
                    "action_id": "options_menu"
                }
            },
            *probability_section,
            {
                "type": "context",
                "elements": context_elements
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{market['description']}"
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Buy :white_check_mark: YES shares",
                            "emoji": true
                        },
                        "value": "yes",
                        "action_id": "action_buy_yes"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Buy :x: NO shares",
                            "emoji": true
                        },
                        "value": "no",
                        "action_id": "action_buy_no"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Sell :white_check_mark: YES shares",
                            "emoji": true
                        },
                        "value": "yes",
                        "action_id": "action_sell_yes"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Sell :x: NO shares",
                            "emoji": true
                        },
                        "value": "no",
                        "action_id": "action_sell_no"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Created by <@{market['owner_id']}> using /pmarket_"
                    },
                ]
            },
        ]
    }

def pmarket_add_view(
    title: str,
    channel_id: str,
    thread_ts: str | None
):
    return {
        "type": "modal",
        "callback_id": "pmarket_add_view",
        "title": {
            "type": "plain_text",
            "text": "Add a prediction market",
            "emoji": true
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": true
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": true
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "block_title_pmarket_add",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "action_title_pmarket_add",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Will Hack Club HQ's balance exceed 6 million dollars by 2026?"
                    },
                    "initial_value": title
                },
                "label": {
                    "type": "plain_text",
                    "text": "Title",
                    "emoji": true
                }
            },
            {
                "type": "input",
                "block_id": "block_desc_pmarket_add",
                "element": {
                    "type": "plain_text_input",
                    "multiline": true,
                    "action_id": "action_desc_pmarket_add",
                    "placeholder": {
                        "type": "plain_text",
                        "text": " "
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Description",
                    "emoji": true
                },
                "optional": true
            },
            {
                "type": "input",
                "block_id": "block_liquidity_pmarket_add",
                "element": {
                    "type": "number_input",
                    "is_decimal_allowed": false,
                    "action_id": "action_liquidity_pmarket_add",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "100"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Liquidity :dollar:",
                    "emoji": true
                }
            }
        ],
        "private_metadata": json.dumps({
            "channel_id": channel_id,
            "thread_ts": thread_ts
        })
    }

def trade_view(
    market_data,
    balance: float,
    user_positions: list[float],
    shares_amount: float,
    buy_or_sell: bool,
    yes_or_no: bool,
    channel_id: str,
    ts: str
):
    yesno = "yes" if yes_or_no else "no"
    YESNO = "YES" if yes_or_no else "NO"
    buysell = "buy" if buy_or_sell else "sell"
    BuySell = "Buy" if buy_or_sell else "Sell"
    yesnoem = ":white_check_mark:" if yes_or_no else ":x:"
    position = user_positions[0] if yes_or_no else user_positions[1]
    bet_amount_or_payoff_display = "Bet amount" if buy_or_sell else "Payoff"
    shares_bef = market_data["bought_shares"]
    lmsr_bef = ps.get_lmsr_info(deepcopy(shares_bef), market_data["liquidity"])
    shares_aft = deepcopy(shares_bef)
    shares_change = shares_amount if buy_or_sell else -shares_amount
    if yes_or_no:
        shares_aft[0] += shares_change
    else:
        shares_aft[1] += shares_change
    lmsr_aft = ps.get_lmsr_info(deepcopy(shares_aft), market_data["liquidity"])
    balance_or_position_display = f"Position: *{position:.0f}* {yesnoem} {YESNO} shares"
    if buy_or_sell:
        balance_or_position_display = f"Balance: *{balance:.0f}* :dollar:"
    bet_amount_or_payoff = lmsr_aft['cost_func'] - lmsr_bef['cost_func'] if buy_or_sell else lmsr_bef['cost_func'] - lmsr_aft['cost_func']
    return {
        "type": "modal",
        "callback_id": f"{buysell}_view_{yesno}",
        "title": {
            "type": "plain_text",
            "text": f"{BuySell} {YESNO} shares",
            "emoji": true
        },
        "submit": {
            "type": "plain_text",
            "text": f"{BuySell}",
            "emoji": true
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": true
        },
        "blocks": [
            {
                "type": "input",
                "block_id": f"block_shares_{buysell}_{yesno}",
                "dispatch_action": true,
                "element": {
                    "type": "number_input",
                    "dispatch_action_config": {
                        "trigger_actions_on": ["on_enter_pressed", "on_character_entered"]
                    },
                    "is_decimal_allowed": false,
                    "action_id": f"action_shares_{buysell}_{yesno}",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "0"
                    },
                    "initial_value": f"{shares_amount:.0f}"
                },
                "label": {
                    "type": "plain_text",
                    "text": f"Amount of {yesnoem} {YESNO} shares",
                    "emoji": true
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"""\
{balance_or_position_display}
{bet_amount_or_payoff_display}: *{bet_amount_or_payoff:.0f}* :dollar:
Probability: *{lmsr_bef['probs'][0]*100:.0f}%* → *{lmsr_aft['probs'][0]*100:.0f}%*"""
                }
            },
        ],
        "private_metadata": json.dumps({
            "balance": balance,
            "user_positions": user_positions,
            "market_data": market_data,
            "channel_id": channel_id,
            "ts": ts,
        })
    }