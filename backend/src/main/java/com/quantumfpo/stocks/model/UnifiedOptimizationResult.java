package com.quantumfpo.stocks.model;

import java.util.Map;

public class UnifiedOptimizationResult {
    private String type;  // 'classical', 'hybrid', 'dynamic'
    private String status;  // 'success', 'error'
    private String error;
    
    // Core results
    private Double objectiveValue;
    private Map<String, Double> weights;  // Current/final period weights
    
    // Performance metrics
    private PerformanceMetrics performance;
    
    // Quantum-specific (hybrid/dynamic)
    private QuantumResult quantumResult;
    
    // Dynamic-specific
    private Map<String, Map<String, Double>> allocations;  // Multi-period allocations
    
    // Classical-specific (for hybrid compatibility)
    private Map<String, Double> classicalWeights;
    private Map<String, Double> classicalPerformance;
    
    // Constructors
    public UnifiedOptimizationResult() {}
    
    public UnifiedOptimizationResult(String type) {
        this.type = type;
        this.status = "success";
    }
    
    // Getters and Setters
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    
    public String getError() { return error; }
    public void setError(String error) { 
        this.error = error; 
        this.status = "error";
    }
    
    public Double getObjectiveValue() { return objectiveValue; }
    public void setObjectiveValue(Double objectiveValue) { this.objectiveValue = objectiveValue; }
    
    public Map<String, Double> getWeights() { return weights; }
    public void setWeights(Map<String, Double> weights) { this.weights = weights; }
    
    public PerformanceMetrics getPerformance() { return performance; }
    public void setPerformance(PerformanceMetrics performance) { this.performance = performance; }
    
    public QuantumResult getQuantumResult() { return quantumResult; }
    public void setQuantumResult(QuantumResult quantumResult) { this.quantumResult = quantumResult; }
    
    public Map<String, Map<String, Double>> getAllocations() { return allocations; }
    public void setAllocations(Map<String, Map<String, Double>> allocations) { this.allocations = allocations; }
    
    public Map<String, Double> getClassicalWeights() { return classicalWeights; }
    public void setClassicalWeights(Map<String, Double> classicalWeights) { this.classicalWeights = classicalWeights; }
    
    public Map<String, Double> getClassicalPerformance() { return classicalPerformance; }
    public void setClassicalPerformance(Map<String, Double> classicalPerformance) { this.classicalPerformance = classicalPerformance; }
    
    // Nested classes for structured data
    public static class PerformanceMetrics {
        private Double expectedAnnualReturn;
        private Double annualVolatility;
        private Double sharpeRatio;
        private Double valueAtRisk;
        
        public PerformanceMetrics() {}
        
        // Getters and setters
        public Double getExpectedAnnualReturn() { return expectedAnnualReturn; }
        public void setExpectedAnnualReturn(Double expectedAnnualReturn) { this.expectedAnnualReturn = expectedAnnualReturn; }
        
        public Double getAnnualVolatility() { return annualVolatility; }
        public void setAnnualVolatility(Double annualVolatility) { this.annualVolatility = annualVolatility; }
        
        public Double getSharpeRatio() { return sharpeRatio; }
        public void setSharpeRatio(Double sharpeRatio) { this.sharpeRatio = sharpeRatio; }
        
        public Double getValueAtRisk() { return valueAtRisk; }
        public void setValueAtRisk(Double valueAtRisk) { this.valueAtRisk = valueAtRisk; }
    }
    
    public static class QuantumResult {
        private int[] solution;
        private Double objectiveValue;
        private Integer jobsExecuted;
        private Boolean simulatorUsed;
        
        public QuantumResult() {}
        
        // Getters and setters
        public int[] getSolution() { return solution; }
        public void setSolution(int[] solution) { this.solution = solution; }
        
        public Double getObjectiveValue() { return objectiveValue; }
        public void setObjectiveValue(Double objectiveValue) { this.objectiveValue = objectiveValue; }
        
        public Integer getJobsExecuted() { return jobsExecuted; }
        public void setJobsExecuted(Integer jobsExecuted) { this.jobsExecuted = jobsExecuted; }
        
        public Boolean getSimulatorUsed() { return simulatorUsed; }
        public void setSimulatorUsed(Boolean simulatorUsed) { this.simulatorUsed = simulatorUsed; }
    }
}