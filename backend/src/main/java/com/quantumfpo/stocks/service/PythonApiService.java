package com.quantumfpo.stocks.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;

@Service
public class PythonApiService {
    private static final Logger logger = LoggerFactory.getLogger(PythonApiService.class);
    
    @Value("${PYTHON_API_BASE_URL:http://localhost:8002}")
    private String pythonApiBaseUrl;
    
    private final RestTemplate restTemplate;
    
    public PythonApiService() {
        this.restTemplate = new RestTemplate();
    }
    
    @SuppressWarnings("unchecked")
    public Map<String, Object> optimizeClassical(List<Map<String, Object>> stockData, double varPercent) {
        try {
            logger.info("[PythonAPI] Starting classical optimization");
            
            // Convert percentage to decimal (e.g., 5.0% -> 0.05)
            double varPercentDecimal = varPercent / 100.0;
            logger.info("[PythonAPI] Converting VaR from {}% to decimal: {}", varPercent, varPercentDecimal);
            
            Map<String, Object> request = new HashMap<>();
            request.put("stock_data", stockData);
            request.put("var_percent", varPercentDecimal);
            
            String endpoint = pythonApiBaseUrl + "/api/optimize/classical";
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> httpEntity = new HttpEntity<>(request, headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(
                endpoint, HttpMethod.POST, httpEntity, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                logger.info("[PythonAPI] Classical optimization completed successfully");
                return (Map<String, Object>) response.getBody();
            } else {
                throw new RuntimeException("Python API returned unexpected response");
            }
            
        } catch (RestClientException e) {
            logger.error("[PythonAPI] Connection error: {}", e.getMessage());
            throw new RuntimeException("Could not connect to Python API service: " + e.getMessage());
        } catch (Exception e) {
            logger.error("[PythonAPI] Classical optimization failed", e);
            throw new RuntimeException("Classical optimization failed: " + e.getMessage());
        }
    }
    
    @SuppressWarnings("unchecked")
    public Map<String, Object> optimizeHybrid(List<Map<String, Object>> stockData, double varPercent, boolean qcSimulator) {
        try {
            logger.info("[PythonAPI] Starting hybrid optimization (simulator: {})", qcSimulator);
            
            // Convert percentage to decimal (e.g., 5.0% -> 0.05)
            double varPercentDecimal = varPercent / 100.0;
            logger.info("[PythonAPI] Converting VaR from {}% to decimal: {}", varPercent, varPercentDecimal);
            
            Map<String, Object> request = new HashMap<>();
            request.put("stock_data", stockData);
            request.put("var_percent", varPercentDecimal);
            request.put("qc_simulator", qcSimulator);
            
            String endpoint = pythonApiBaseUrl + "/api/optimize/hybrid";
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> httpEntity = new HttpEntity<>(request, headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(
                endpoint, HttpMethod.POST, httpEntity, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                logger.info("[PythonAPI] Hybrid optimization completed successfully");
                return (Map<String, Object>) response.getBody();
            } else {
                throw new RuntimeException("Python API returned unexpected response");
            }
            
        } catch (RestClientException e) {
            logger.error("[PythonAPI] Connection error: {}", e.getMessage());
            throw new RuntimeException("Could not connect to Python API service: " + e.getMessage());
        } catch (Exception e) {
            logger.error("[PythonAPI] Hybrid optimization failed", e);
            throw new RuntimeException("Hybrid optimization failed: " + e.getMessage());
        }
    }
    
    @SuppressWarnings("unchecked")
    public Map<String, Object> optimizeDynamic(List<Map<String, Object>> stockData, double varPercent) {
        try {
            logger.info("[PythonAPI] Starting enhanced dynamic optimization");
            
            // Convert percentage to decimal (e.g., 5.0% -> 0.05)
            double varPercentDecimal = varPercent / 100.0;
            logger.info("[PythonAPI] Converting VaR from {}% to decimal: {}", varPercent, varPercentDecimal);
            
            // Convert stock data to assets format for dynamic optimization
            List<Map<String, Object>> assets = convertStockDataToAssets(stockData);
            
            Map<String, Object> request = new HashMap<>();
            request.put("assets", assets);
            request.put("async_execution", true); // Run asynchronously for complex scenarios
            request.put("config", Map.of(
                "risk_aversion", 1000.0,
                "transaction_fee", 0.01,
                "num_time_steps", 4,
                "rebalance_frequency_days", 30,
                "bit_resolution", 2,
                "max_generations", 20,
                "population_size", 40,
                "estimator_shots", 1000,
                "sampler_shots", 1000,
                "optimizer_type", "differential_evolution"
            ));
            
            String endpoint = pythonApiBaseUrl + "/api/v1/dynamic-portfolio/optimize";
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> httpEntity = new HttpEntity<>(request, headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(
                endpoint, HttpMethod.POST, httpEntity, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                logger.info("[PythonAPI] Enhanced dynamic optimization completed successfully");
                return (Map<String, Object>) response.getBody();
            } else {
                throw new RuntimeException("Python API returned unexpected response");
            }
            
        } catch (RestClientException e) {
            logger.error("[PythonAPI] Connection error: {}", e.getMessage());
            throw new RuntimeException("Could not connect to Python API service: " + e.getMessage());
        } catch (Exception e) {
            logger.error("[PythonAPI] Enhanced dynamic optimization failed", e);
            throw new RuntimeException("Enhanced dynamic optimization failed: " + e.getMessage());
        }
    }
    
    @SuppressWarnings("unchecked")
    public Map<String, Object> getDynamicJobStatus(String jobId) {
        try {
            String endpoint = pythonApiBaseUrl + "/api/v1/dynamic-portfolio/status/" + jobId;
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> httpEntity = new HttpEntity<>(headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(
                endpoint, HttpMethod.GET, httpEntity, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                return (Map<String, Object>) response.getBody();
            } else {
                throw new RuntimeException("Failed to get job status");
            }
            
        } catch (RestClientException e) {
            logger.error("[PythonAPI] Connection error getting job status: {}", e.getMessage());
            throw new RuntimeException("Could not connect to Python API service: " + e.getMessage());
        } catch (Exception e) {
            logger.error("[PythonAPI] Failed to get job status", e);
            throw new RuntimeException("Failed to get job status: " + e.getMessage());
        }
    }
    
    @SuppressWarnings("unchecked")
    public Map<String, Object> getDynamicJobResult(String jobId) {
        try {
            String endpoint = pythonApiBaseUrl + "/api/v1/dynamic-portfolio/result/" + jobId;
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<String> httpEntity = new HttpEntity<>(headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(
                endpoint, HttpMethod.GET, httpEntity, Map.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                return (Map<String, Object>) response.getBody();
            } else {
                throw new RuntimeException("Failed to get job result");
            }
            
        } catch (RestClientException e) {
            logger.error("[PythonAPI] Connection error getting job result: {}", e.getMessage());
            throw new RuntimeException("Could not connect to Python API service: " + e.getMessage());
        } catch (Exception e) {
            logger.error("[PythonAPI] Failed to get job result", e);
            throw new RuntimeException("Failed to get job result: " + e.getMessage());
        }
    }
    
    public boolean isHealthy() {
        try {
            String endpoint = pythonApiBaseUrl + "/health";
            ResponseEntity<String> response = restTemplate.getForEntity(endpoint, String.class);
            return response.getStatusCode() == HttpStatus.OK;
        } catch (Exception e) {
            logger.warn("[PythonAPI] Health check failed: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Convert stock data format to assets format expected by dynamic optimization API
     */
    private List<Map<String, Object>> convertStockDataToAssets(List<Map<String, Object>> stockData) {
        Map<String, String> uniqueSymbols = new HashMap<>();
        
        // Get unique symbols from stock data
        for (Map<String, Object> row : stockData) {
            String symbol = (String) row.get("symbol");
            if (symbol != null) {
                uniqueSymbols.put(symbol, symbol);
            }
        }
        
        List<Map<String, Object>> assets = new ArrayList<>();
        
        // Convert each unique symbol to asset format expected by dynamic optimization
        for (String symbol : uniqueSymbols.keySet()) {
            Map<String, Object> asset = new HashMap<>();
            asset.put("symbol", symbol);
            asset.put("name", symbol + " Stock"); // Optional name
            asset.put("max_allocation", 0.8); // Optional max allocation
            assets.add(asset);
        }
        
        logger.info("[PythonAPI] Converted {} unique symbols to {} assets for dynamic optimization", 
                   uniqueSymbols.size(), assets.size());
        return assets;
    }
}