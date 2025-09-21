package com.quantumfpo.stocks.model;

import java.util.List;

public class StockRequest {
    private List<String> stocks;
    private int period;

    public List<String> getStocks() { return stocks; }
    public void setStocks(List<String> stocks) { this.stocks = stocks; }
    public int getPeriod() { return period; }
    public void setPeriod(int period) { this.period = period; }
}
