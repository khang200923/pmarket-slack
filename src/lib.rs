mod pmarket;
mod python;
mod schema;
mod models;
mod db;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::exceptions::{PyException, PyValueError};
use bigdecimal::BigDecimal;
use serde_json::Value;
use std::collections::HashMap;
use std::str::FromStr;
use crate::python::classes::*;

fn bigdecimal_to_pydecimal<'py>(
    py: Python<'py>,
    value: &BigDecimal,
) -> PyResult<Bound<'py, PyAny>> {
    let s = value.to_string();

    let decimal = py.import("decimal")?;
    let decimal_cls = decimal.getattr("Decimal")?;

    let py_decimal = decimal_cls.call1((s,))?;

    Ok(py_decimal)
}

fn pydecimal_to_bigdecimal<'py>(
    _py: Python<'py>,
    value: Bound<'py, PyAny>
) -> PyResult<BigDecimal> {
    let decimal = value.str()?.extract::<String>()?;
    BigDecimal::from_str(&decimal)
        .map_err(|e| PyValueError::new_err(format!("Invalid BigDecimal: {}", e)))
}

#[pyfunction]
fn create_user(id: &str) -> PyResult<()> {
    let mut conn = db::establish_connection();
    pmarket::methods::create_user(id, &mut conn)
        .map_err(PyException::new_err)
}

#[pyfunction]
fn try_create_user(id: &str) -> PyResult<()> {
    let mut conn = db::establish_connection();
    pmarket::methods::try_create_user(id, &mut conn)
        .map_err(PyException::new_err)
}

#[pyfunction]
fn change_balance<'py>(
    py: Python<'py>,
    user_id: &str, 
    amount: Bound<'py, PyAny>
) -> PyResult<()> {
    let mut conn = db::establish_connection();
    let amount = pydecimal_to_bigdecimal(py, amount)
        .map_err(|e| PyValueError::new_err(format!("Invalid amount: {}", e)))?;
    pmarket::methods::change_balance(user_id, &amount, &mut conn)
        .map_err(PyException::new_err)
}

#[pyfunction]
fn create_market<'py>(
    py: Python<'py>,
    title: &str,
    description: &str,
    owner_id: &str,
    liquidity: Bound<'py, PyAny>
) -> PyResult<i32> {
    let mut conn = db::establish_connection();
    let liquidity = pydecimal_to_bigdecimal(py, liquidity)
        .map_err(|e| PyValueError::new_err(format!("Invalid liquidity: {}", e)))?;
    pmarket::methods::create_market(title, description, owner_id, &liquidity, &mut conn)
        .map_err(PyException::new_err)
}

#[pyfunction]
fn check_valid_trade<'py>(
    py: Python<'py>,
    market_id: i32,
    user_id: &str,
    shares_amount: Bound<'py, PyAny>,
    share_index: i32
) -> PyResult<(bool, Bound<'py, PyAny>)> {
    let mut conn = db::establish_connection();
    let shares_amount = pydecimal_to_bigdecimal(py, shares_amount)
        .map_err(|e| PyValueError::new_err(format!("Invalid shares_amount: {}", e)))?;
    let (valid, change) = pmarket::methods::check_valid_trade(market_id, user_id, &shares_amount, share_index, &mut conn)
        .map_err(PyException::new_err)?;
    let py_change = bigdecimal_to_pydecimal(py, &change)?;
    Ok((valid, py_change))
}

#[pyfunction]
fn create_trade<'py>(
    py: Python<'py>,
    market_id: i32,
    user_id: &str,
    shares_amount: Bound<'py, PyAny>,
    share_index: i32
) -> PyResult<()> {
    let mut conn = db::establish_connection();
    let shares_amount = pydecimal_to_bigdecimal(py, shares_amount)
        .map_err(|e| PyValueError::new_err(format!("Invalid shares_amount: {}", e)))?;
    pmarket::methods::create_trade(market_id, user_id, &shares_amount, share_index, &mut conn)
        .map_err(PyException::new_err)
}

#[pyfunction]
fn get_positions(market_id: i32) -> PyResult<HashMap<String, Vec<String>>> {
    let mut conn = db::establish_connection();
    let positions = pmarket::methods::get_positions(market_id, &mut conn)
        .map_err(PyException::new_err)?;
    Ok(positions.into_iter()
        .map(|(user, shares)| {
            (user, shares.into_iter().map(|s| s.to_string()).collect())
        })
        .collect())
}

#[pyfunction]
fn get_balance_changes_on_market(market_id: i32) -> PyResult<HashMap<String, String>> {
    let mut conn = db::establish_connection();
    let changes = pmarket::methods::get_balance_changes_on_market(market_id, &mut conn)
        .map_err(PyException::new_err)?;
    Ok(changes.into_iter()
        .map(|(user, change)| (user, change.to_string()))
        .collect())
}

#[pyfunction]
fn resolve_market(market_id: i32, resolution: Option<i32>) -> PyResult<()> {
    let mut conn = db::establish_connection();
    pmarket::methods::resolve_market(market_id, resolution, &mut conn)
        .map_err(PyException::new_err)
}

#[pyfunction]
fn get_user_data<'py>(py: Python<'py>, id: &str) -> PyResult<Bound<'py, PyAny>> {
    let mut conn = db::establish_connection();
    let user_data: Value = pmarket::utils::get_user_data(id, &mut conn)
        .map_err(PyException::new_err)?;
    let user_data: String = serde_json::to_string(&user_data)
        .map_err(|e| PyException::new_err(format!("Serialization error: {}", e)))?;

    let json = py.import("json")?;
    let json_cls = json.getattr("loads")?;
    let py_user = json_cls.call1((user_data,))?;
    Ok(py_user)
}

#[pyfunction]
fn get_market_data<'py>(py: Python<'py>, market_id: i32) -> PyResult<Bound<'py, PyAny>> {
    let mut conn = db::establish_connection();
    let market_data = pmarket::utils::get_market_data(market_id, &mut conn)
        .map_err(PyException::new_err)?;
    let market_data: String = serde_json::to_string(&market_data)
        .map_err(|e| PyException::new_err(format!("Serialization error: {}", e)))?;

    let json = py.import("json")?;
    let json_cls = json.getattr("loads")?;
    let py_market = json_cls.call1((market_data,))?;
    Ok(py_market)
}

#[pyfunction]
fn get_lmsr_info<'py>(
    py: Python<'py>,
    shares: Vec<Bound<'py, PyAny>>,
    liquidity: f64
) -> PyResult<Bound<'py, PyAny>> {
    let shares_f64: Vec<f64> = shares.iter()
        .map(|s| s.extract::<f64>().unwrap_or(0.0))
        .collect();
    
    let info = pmarket::utils::get_lmsr_info(&shares_f64, liquidity);
    let info_str = serde_json::to_string(&info)
        .map_err(|e| PyException::new_err(format!("Serialization error: {}", e)))?;

    let json = py.import("json")?;
    let json_cls = json.getattr("loads")?;
    let py_info = json_cls.call1((info_str,))?;
    Ok(py_info)
}

#[pymodule]
fn pmarket_slack(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_user, py)?)?;
    m.add_function(wrap_pyfunction!(try_create_user, py)?)?;
    m.add_function(wrap_pyfunction!(change_balance, py)?)?;
    m.add_function(wrap_pyfunction!(create_market, py)?)?;
    m.add_function(wrap_pyfunction!(check_valid_trade, py)?)?;
    m.add_function(wrap_pyfunction!(create_trade, py)?)?;
    m.add_function(wrap_pyfunction!(get_positions, py)?)?;
    m.add_function(wrap_pyfunction!(get_balance_changes_on_market, py)?)?;
    m.add_function(wrap_pyfunction!(resolve_market, py)?)?;
    m.add_function(wrap_pyfunction!(get_user_data, py)?)?;
    m.add_function(wrap_pyfunction!(get_market_data, py)?)?;
    m.add_function(wrap_pyfunction!(get_lmsr_info, py)?)?;
    Ok(())
}