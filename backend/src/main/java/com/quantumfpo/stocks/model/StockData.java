package com.quantumfpo.stocks.model;

import java.time.LocalDate;

public class StockData {
    private String symbol;
    private LocalDate date;
    private double open;
    private double high;
    private double low;
    private double close;

    public StockData(String symbol, LocalDate date, double open, double high, double low, double close) {
        this.symbol = symbol;
        this.date = date;
        this.open = open;
        this.high = high;
        this.low = low;
        this.close = close;
    }

    public String getSymbol() { return symbol; }
    public LocalDate getDate() { return date; }
    public double getOpen() { return open; }
    public double getHigh() { return high; }
    public double getLow() { return low; }
    public double getClose() { return close; }
}
