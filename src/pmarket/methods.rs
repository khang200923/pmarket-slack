use std::collections::HashMap;
use bigdecimal::Zero;
use diesel::prelude::*;
use diesel::result::Error as DieselError;
use bigdecimal::BigDecimal;
use crate::models::*;
use crate::schema::*;
use crate::pmarket::lmsr::schange_to_bchange;

pub fn create_user(
    id: &str, 
    conn: &mut PgConnection
) -> Result<(), String> {
    let new_user = NewUser {
        id: id.to_string(),
        balance: BigDecimal::zero(),
    };

    diesel::insert_into(users::table)
        .values(new_user)
        .execute(conn)
        .map(|_| ())
        .map_err(|e| format!("Error creating new user: {}", e))
}

pub fn change_balance(
    user_id: &str,
    amount: &BigDecimal,
    conn: &mut PgConnection,
) -> Result<(), String> {
    use crate::schema::users::dsl::*;

    diesel::update(users.filter(id.eq(user_id)))
        .set(balance.eq(balance + amount))
        .execute(conn)
        .map(|_| ())
        .map_err(|e| format!("Error updating user balance: {}", e))
}

pub fn create_market(
    title: &str,
    description: &str,
    owner_id: &str,
    liquidity: &BigDecimal,
    conn: &mut PgConnection,
) -> Result<(), String> {
    
    let new_market = NewMarket {
        title: title.to_string(),
        description: description.to_string(),
        owner_id: owner_id.to_string(),
        liquidity: liquidity.clone(),
    };
    
    let mut err = None;
    let transaction = conn.transaction::<(), DieselError, _>(|conn| {
        change_balance(owner_id, &-liquidity, conn)
            .map_err(|e| {
                err = Some(format!("Error deducting owner's balance for new market: {}", e));
                DieselError::RollbackTransaction
            })?;
        diesel::insert_into(markets::table)
            .values(&new_market)
            .execute(conn)
            .map(|_| ())
            .map_err(|e| {
                err = Some(format!("Error creating new market: {}", e));
                DieselError::RollbackTransaction
            })
    });
    if let Err(e) = transaction {
        return Err(err.unwrap_or_else(|| format!("Transaction failed: {}", e)));
    }
    Ok(())
}

pub fn check_valid_trade(
    market_id: i32,
    user_id: &str,
    shares_amount: &BigDecimal,
    share_index: i32,
    conn: &mut PgConnection,
) -> Result<(bool, BigDecimal), String> {
    let balance = users::table
        .filter(users::id.eq(user_id))
        .select(users::balance)
        .first::<BigDecimal>(conn)
        .map_err(|e| format!("Error fetching user balance: {}", e))?;
    let market = markets::table
        .filter(markets::id.eq(market_id))
        .first::<Market>(conn)
        .map_err(|e| format!("Error fetching market: {}", e))?;
    let balance_change = schange_to_bchange(&market, shares_amount.clone(), share_index);
    let new_balance = balance + balance_change;
    let is_resolved = market.is_resolved;
    if is_resolved {
        return Ok((false, BigDecimal::zero()));
    }
    Ok((new_balance >= BigDecimal::zero(), new_balance))
}

pub fn create_trade(
    market_id: i32,
    user_id: &str,
    shares_amount: &BigDecimal,
    share_index: i32,
    conn: &mut PgConnection,
) -> Result<(), String> {
    let (is_valid, balance_change) = check_valid_trade(market_id, user_id, shares_amount, share_index, conn)?;
    if !is_valid {
        return Err("Invalid trade".to_string());
    }

    let new_trade = NewTrade {
        market_id,
        user_id: user_id.to_string(),
        shares_amount: shares_amount.clone(),
        share_index,
        balance_change: balance_change.clone(),
    };

    let mut err = None;
    let transaction = conn.transaction::<(), DieselError, _>(|conn| {
        change_balance(user_id, &balance_change, conn)
            .map_err(|e| {
                err = Some(format!("Error updating user balance for trade: {}", e));
                DieselError::RollbackTransaction
            })?;
        diesel::insert_into(trades::table)
            .values(&new_trade)
            .execute(conn)
            .map(|_| ())
            .map_err(|e| {
                err = Some(format!("Error creating new trade: {}", e));
                DieselError::RollbackTransaction
            })
    });
    if let Err(e) = transaction {
        return Err(err.unwrap_or_else(|| format!("Transaction failed: {}", e)));
    }
    Ok(())
}

pub fn get_positions(
    market_id: i32,
    conn: &mut PgConnection,
) -> Result<HashMap<String, Vec<BigDecimal>>, String> {
    use crate::schema::trades::dsl as trades_dsl;
    use crate::schema::users::dsl as users_dsl;

    let trades_simple = trades_dsl::trades
        .inner_join(users_dsl::users.on(trades_dsl::user_id.eq(users_dsl::id)))
        .filter(trades_dsl::market_id.eq(market_id))
        .select((
            users_dsl::id, 
            trades_dsl::shares_amount, 
            trades_dsl::share_index
        ))
        .load::<(String, BigDecimal, i32)>(conn)
        .map_err(|e| format!("Error fetching trades: {}", e))?;

    let positions = trades_simple.into_iter()
        .fold(
            HashMap::new(), 
            |mut acc, (user_id, shares_amount, share_index)| {
                let idx: usize = share_index.try_into().unwrap();
                acc.entry(user_id)
                    .or_insert(
                        vec![BigDecimal::zero(), BigDecimal::zero()]
                    )[idx] += shares_amount;
                acc
            }
        );

    Ok(positions)
}

pub fn get_balance_changes_on_market(
    market_id: i32,
    conn: &mut PgConnection,
) -> Result<HashMap<String, BigDecimal>, String> {
    use crate::schema::trades::dsl as trades_dsl;

    let trades_simple = trades_dsl::trades
        .filter(trades_dsl::market_id.eq(market_id))
        .select((trades_dsl::user_id, trades_dsl::balance_change))
        .load::<(String, BigDecimal)>(conn)
        .map_err(|e| format!("Error fetching trades: {}", e))?;

    Ok(
        trades_simple.into_iter()
        .fold(HashMap::new(), |mut acc, (user_id, balance_change)| {
            *acc.entry(user_id).or_insert(BigDecimal::zero()) += balance_change;
            acc
        })
    )
}

pub fn resolve_market(
    market_id: i32,
    resolution: Option<i32>,
    conn: &mut PgConnection
) -> Result<(), String> {
    use crate::schema::markets::dsl as markets_dsl;

    if resolution.is_none() {
        let bchanges = get_balance_changes_on_market(market_id, conn)
            .map_err(|e| format!("Error fetching balance changes: {}", e))?;

        // undo all balance changes
        let mut err = None;
        let transaction = conn.transaction::<(), DieselError, _>(|conn| {
            for (user_id, balance_change) in bchanges {
                change_balance(&user_id, &-balance_change, conn)
                    .map_err(|e| {
                        err = Some(format!("Error updating user balance for resolution: {}", e));
                        DieselError::RollbackTransaction
                    })?;
            }

            diesel::update(markets_dsl::markets.filter(markets_dsl::id.eq(market_id)))
                .set((
                    markets_dsl::is_resolved.eq(true),
                    markets_dsl::resolution.eq(resolution),
                ))
                .execute(conn)
                .map(|_| ())
                .map_err(|e| {
                    err = Some(format!("Error resolving market: {}", e));
                    DieselError::RollbackTransaction
                })
        });
        if let Err(e) = transaction {
            return Err(err.unwrap_or_else(|| format!("Transaction failed: {}", e)));
        }
        return Ok(());
    }

    let share_index = resolution.unwrap();
    let share_index: usize = share_index.try_into().unwrap();
    let positions = get_positions(market_id, conn)
        .map_err(|e| format!("Error fetching positions: {}", e))?;

    // reward traders by how many correct shares they bought
    let mut err = None;
    let transaction = conn.transaction::<(), DieselError, _>(|conn| {
        for (users_id, shares) in positions {
            let reward = shares[share_index].clone();
            change_balance(&users_id, &reward, conn)
                .map_err(|e| {
                    err = Some(format!("Error updating user balance for resolution: {}", e));
                    DieselError::RollbackTransaction
                })?;
        }

        diesel::update(markets_dsl::markets.filter(markets_dsl::id.eq(market_id)))
            .set((
                markets_dsl::is_resolved.eq(true),
                markets_dsl::resolution.eq(resolution),
            ))
            .execute(conn)
            .map(|_| ())
            .map_err(|e| {
                err = Some(format!("Error resolving market: {}", e));
                DieselError::RollbackTransaction
            })
    });
    if let Err(e) = transaction {
        return Err(err.unwrap_or_else(|| format!("Transaction failed: {}", e)));
    }
    Ok(())
}