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
}