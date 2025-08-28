use diesel::prelude::*;
use diesel::result::Error as DieselError;
use bigdecimal::{BigDecimal, ToPrimitive};
use serde_json::{Value, json};
use crate::{pmarket::lmsr::{cost_function_algo, prob, prob_algo}, python::classes::*};

pub fn get_user_data(
    id: &str, 
    conn: &mut PgConnection
) -> Result<Value, String> {
    use crate::schema::users::dsl::*;

    match users
        .find(id)
        .first::<crate::models::User>(conn) 
    {
        Ok(user) => {
            let user_data = json!({
                "id": user.id,
                "balance": user.balance.to_f64().unwrap(),
            });
            Ok(user_data)
        },
        Err(DieselError::NotFound) => Err("User not found".to_string()),
        Err(e) => Err(format!("Database error: {}", e)),
    }
}

pub fn get_market_data(
    market_id: i32, 
    conn: &mut PgConnection
) -> Result<Value, String> {
    use crate::schema::markets::dsl as markets_dsl;
    use crate::schema::market_slack_msg::dsl as msm_dsl;
    let main_slack_msg = msm_dsl::market_slack_msg
        .filter(msm_dsl::market_id.eq(market_id))
        .filter(msm_dsl::main.eq(true))
        .first::<crate::models::MarketSlackMsg>(conn)
        .optional()
        .map_err(|e| format!("Database error: {}", e))?;

    match markets_dsl::markets
        .find(market_id)
        .first::<crate::models::Market>(conn) 
    {
        Ok(market) => {
            let market_data = json!({
                "id": market.id,
                "title": market.title,
                "description": market.description,
                "owner_id": market.owner_id,
                "liquidity": market.liquidity.to_f64().unwrap(),
                "bought_shares": market.bought_shares.iter()
                    .map(|s| s.clone().unwrap().to_f64().unwrap())
                    .collect::<Vec<f64>>(),
                "remind_at": market.remind_at.and_utc().timestamp(),
                "is_resolved": market.is_resolved,
                "resolution": market.resolution,
                "created_at": market.created_at.and_utc().timestamp(),

                "prob": prob(&market).iter()
                    .map(|p| p.to_f64().unwrap())
                    .collect::<Vec<f64>>(),
                "main_slack_msg": json!({
                    "exists": main_slack_msg.is_some(),
                    "channel_id": main_slack_msg.as_ref().map(|msg| msg.channel_id.clone()),
                    "ts": main_slack_msg.as_ref().map(|msg| msg.ts.clone()),
                }),
            });
            Ok(market_data)
        },
        Err(DieselError::NotFound) => Err("Market not found".to_string()),
        Err(e) => Err(format!("Database error: {}", e)),
    }
}

pub fn get_lmsr_info(
    shares: &Vec<f64>,
    liquidity: f64,
) -> Value {
    json!({
        "probs": prob_algo(liquidity, &shares),
        "cost_func": cost_function_algo(liquidity, &shares),
    })
}