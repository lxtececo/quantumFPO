package com.quantumfpo.stocks.model;

import java.util.List;

public class OptimizeRequest {
    private List<String> stocks;
    private Double varPercent;  // Using wrapper class to allow null detection
    private Boolean qcSimulator;  // Using wrapper class for consistency

    public List<String> getStocks() { return stocks; }
    public void setStocks(List<String> stocks) { this.stocks = stocks; }
    
    // Return default value of 0.0 when varPercent is null
    public double getVarPercent() { 
        return varPercent != null ? varPercent : 0.0; 
    }
    
    public void setVarPercent(Double varPercent) { this.varPercent = varPercent; }
    
    // Return default value of true when qcSimulator is null
    public boolean isQcSimulator() { 
        return qcSimulator == null || qcSimulator; 
    }
    
    public void setQcSimulator(Boolean qcSimulator) { this.qcSimulator = qcSimulator; }
    
    // Helper method to get qcSimulator with default value (same as isQcSimulator now)
    public boolean getQcSimulatorValue() { 
        return isQcSimulator(); 
    }
    
    // Internal getter for null checking in validation
    public Double getVarPercentRaw() {
        return varPercent;
    }
    
    // Internal getter for null checking in validation
    public Boolean getQcSimulatorRaw() {
        return qcSimulator;
    }
}
