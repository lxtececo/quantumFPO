package com.quantumfpo.stocks.model;

import java.util.List;

public class OptimizeRequest {
    private List<String> stocks;
    private double varPercent;
    private boolean qcSimulator = true;

    public List<String> getStocks() { return stocks; }
    public void setStocks(List<String> stocks) { this.stocks = stocks; }
    public double getVarPercent() { return varPercent; }
    public void setVarPercent(double varPercent) { this.varPercent = varPercent; }
    public boolean isQcSimulator() { return qcSimulator; }
    public void setQcSimulator(boolean qcSimulator) { this.qcSimulator = qcSimulator; }
}
