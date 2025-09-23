package com.quantumfpo.stocks.model;

import java.util.List;

public class StockRequest {
    private List<String> stocks;
    private int period;
    private int stockAmount; // number of stocks to load/simulate

    public List<String> getStocks() { return stocks; }
    public void setStocks(List<String> stocks) { this.stocks = stocks; }
    public int getPeriod() { return period; }
    public void setPeriod(int period) { this.period = period; }
    public int getStockAmount() { return stockAmount; }
    public void setStockAmount(int stockAmount) { this.stockAmount = stockAmount; }
}
