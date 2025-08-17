use pyo3::prelude::*;
use pyo3::types::*;

// #[pyclass]
// pub struct User {
//     pub id: PyString,
//     pub balance: PyFloat,
// }

// #[pyclass]
// pub struct Market {
//     pub id: i32,
//     pub title: String,
//     pub description: String,
//     pub owner_id: String,
//     pub liquidity: f64,
//     pub bought_shares: Vec<Option<f64>>,
//     pub is_resolved: bool,
//     pub resolution: Option<i32>,

//     pub prob: Vec<f64>,
// }

// #[pyclass]
// pub struct Trade {
//     pub id: i32,
//     pub market_id: i32,
//     pub user_id: String,
//     pub shares_amount: f64,
//     pub share_index: i32,
//     pub balance_change: f64,
// }