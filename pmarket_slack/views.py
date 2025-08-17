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
    market = ps.get_market_data(market_id)

    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{market['title']}*"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "...",
                        "emoji": true
                    },
                    "value": "options",
                    "action_id": "action_options_pmarket"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{market['prob'][0]*100:.0f}%* chance"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*{market['liquidity']:.0f}* :dollar: liquidity"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{market['description'] if market['description'] else ' '}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":white_check_mark: Buy YES shares",
                            "emoji": true
                        },
                        "value": "yes",
                        "action_id": "action_bet_yes"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":x: Buy NO shares",
                            "emoji": true
                        },
                        "value": "no",
                        "action_id": "action_bet_no"
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
                    "type": "rich_text_input",
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

def bet_view(
    market_data,
    shares_amount: float,
    yes_or_no: bool,
    channel_id: str,
    ts: str
):
    yesno = "yes" if yes_or_no else "no"
    YESNO = "YES" if yes_or_no else "NO"
    yesnoem = ":white_check_mark:" if yes_or_no else ":x:"
    shares_bef = market_data["bought_shares"]
    lmsr_bef = ps.get_lmsr_info(deepcopy(shares_bef), market_data["liquidity"])
    print(lmsr_bef)
    shares_aft = deepcopy(shares_bef)
    if yes_or_no:
        shares_aft[0] += shares_amount
    else:
        shares_aft[1] += shares_amount
    lmsr_aft = ps.get_lmsr_info(deepcopy(shares_aft), market_data["liquidity"])
    print(lmsr_aft)
    return {
        "type": "modal",
        "callback_id": f"bet_view_{yesno}",
        "title": {
            "type": "plain_text",
            "text": f"Buy {YESNO} shares",
            "emoji": true
        },
        "submit": {
            "type": "plain_text",
            "text": "Bet",
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
                "block_id": f"block_shares_buy_{yesno}",
                "dispatch_action": true,
                "element": {
                    "type": "number_input",
                    "dispatch_action_config": {
                        "trigger_actions_on": ["on_enter_pressed", "on_character_entered"]
                    },
                    "is_decimal_allowed": false,
                    "action_id": f"action_shares_buy_{yesno}",
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
                    "text": f"Bet amount: *{lmsr_aft['cost_func'] - lmsr_bef['cost_func']:.0f}* :dollar:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Probability: *{lmsr_bef['probs'][0]*100:.0f}%* → *{lmsr_aft['probs'][0]*100:.0f}%*"
                }
            }
        ],
        "private_metadata": json.dumps({
            "market_data": market_data,
            "channel_id": channel_id,
            "ts": ts,
        })
    }