use bigdecimal::{BigDecimal, ToPrimitive, FromPrimitive};
use crate::models::*;

fn logsumexp(
    inp: &Vec<f64>
) -> f64 {
    let max = inp.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let sum = inp.iter().map(|&x| (x - max).exp()).sum::<f64>();
    max + sum.ln()
}

fn cost_function_algo(
    liquidity: f64,
    shares: &Vec<f64>
) -> f64 {
    let shares_scaled = shares.iter().map(|s| s / liquidity).collect::<Vec<f64>>();
    let lse = logsumexp(&shares_scaled);
    liquidity * lse
}

fn prob_algo(
    liquidity: f64,
    shares: &Vec<f64>,
) -> Vec<f64> {
    let shares_scaled = shares.iter().map(|s| s / liquidity).collect::<Vec<f64>>();
    let lse = logsumexp(&shares_scaled);
    shares_scaled.iter().map(|&s| (s - lse).exp()).collect::<Vec<f64>>()
}

fn schange_to_bchange_algo(
    liquidity: f64,
    shares: &Vec<f64>,
    share_change: f64,
    share_index: usize
) -> f64 {
    let curr_cost_func = cost_function_algo(liquidity, shares);
    let new_shares = shares.iter().enumerate()
        .map(|(i, &s)| if i == share_index { s + share_change } else { s })
        .collect::<Vec<f64>>();
    let new_cost_func = cost_function_algo(liquidity, &new_shares);
    curr_cost_func - new_cost_func
}


pub fn cost_function(
    market: &Market
) -> BigDecimal {
    let shares = market.bought_shares.iter()
        .map(|s| s.clone().map_or(
            0.0, 
            |v| v.to_f64().unwrap()
        ))
        .collect::<Vec<f64>>();
    let liquidity = market.liquidity.to_f64().unwrap();
    BigDecimal::from_f64(cost_function_algo(liquidity, &shares)).unwrap()
}

pub fn prob(
    market: &Market
) -> Vec<BigDecimal> {
    let shares = market.bought_shares.iter()
        .map(|s| s.clone().map_or(
            0.0, 
            |v| v.to_f64().unwrap()
        ))
        .collect::<Vec<f64>>();
    let liquidity = market.liquidity.to_f64().unwrap();
    prob_algo(liquidity, &shares)
        .into_iter()
        .map(|p| BigDecimal::from_f64(p).unwrap())
        .collect()
}

pub fn schange_to_bchange(
    market: &Market,
    share_change: BigDecimal,
    share_index: i32
) -> BigDecimal {
    let liquidity = market.liquidity.to_f64().unwrap();
    let shares = market.bought_shares.iter()
        .map(|s| s.clone().map_or(
            0.0, 
            |v| v.to_f64().unwrap()
        ))
        .collect::<Vec<f64>>();
    let share_change_f64 = share_change.to_f64().unwrap();
    BigDecimal::from_f64(schange_to_bchange_algo(liquidity, &shares, share_change_f64, share_index.try_into().unwrap())).unwrap()
}