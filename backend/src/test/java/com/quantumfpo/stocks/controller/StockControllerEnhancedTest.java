package com.quantumfpo.stocks.controller;

import com.quantumfpo.stocks.service.AlphaVantageService;
import com.quantumfpo.stocks.service.PythonApiService;
import com.quantumfpo.stocks.model.StockData;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.http.MediaType;

import java.time.LocalDate;
import java.util.*;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Comprehensive test suite for StockController with enhanced REST API integration testing.
 * Tests all endpoints including integration with PythonApiService.
 */
@SpringBootTest
class StockControllerIntegrationTest {

    @Autowired
    private WebApplicationContext webApplicationContext;
    
    private MockMvc mockMvc;

    @MockitoBean
    private AlphaVantageService alphaVantageService;

    @MockitoBean
    private PythonApiService pythonApiService;

    @BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build();
        Mockito.reset(alphaVantageService, pythonApiService);
    }

    // Stock Loading Tests

    @Test
    void testLoadStocksEndpointSuccess() throws Exception {
        // Mock service response
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 23), 2800.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 24), 2850.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(Arrays.asList(mockData.get(0), mockData.get(1)));
        when(alphaVantageService.fetchStockHistory("SIM_GOOGL", 30))
            .thenReturn(Arrays.asList(mockData.get(2), mockData.get(3)));

        String requestJson = "{\"stocks\":[\"SIM_AAPL\",\"SIM_GOOGL\"],\"period\":30}";

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$.length()").value(4))
                .andExpect(jsonPath("$[0].symbol").value("SIM_AAPL"))
                .andExpect(jsonPath("$[0].close").value(150.0))
                .andExpect(jsonPath("$[2].symbol").value("SIM_GOOGL"));
    }

    @Test
    void testLoadStocksEndpointWithEmptyStocks() throws Exception {
        String requestJson = "{\"stocks\":[],\"period\":30}";

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$.length()").value(0));
    }

    @Test
    void testLoadStocksEndpointWithServiceException() throws Exception {
        when(alphaVantageService.fetchStockHistory("SIM_ERROR", 30))
            .thenThrow(new RuntimeException("Alpha Vantage service error"));

        String requestJson = "{\"stocks\":[\"SIM_ERROR\"],\"period\":30}";

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isInternalServerError());
    }

    // Classical Optimization Tests with PythonApiService

    @Test
    void testOptimizeEndpointWithPythonApiServiceSuccess() throws Exception {
        // Mock stock data loading
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 23), 2800.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 24), 2850.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(Arrays.asList(mockData.get(0), mockData.get(1)));
        when(alphaVantageService.fetchStockHistory("SIM_GOOGL", 30))
            .thenReturn(Arrays.asList(mockData.get(2), mockData.get(3)));

        // Mock Python API health check
        when(pythonApiService.isHealthy()).thenReturn(true);

        // Mock Python API optimization response
        Map<String, Object> optimizationResult = new HashMap<>();
        Map<String, Double> weights = new HashMap<>();
        weights.put("SIM_AAPL", 0.6);
        weights.put("SIM_GOOGL", 0.4);
        optimizationResult.put("weights", weights);
        optimizationResult.put("expected_annual_return", 0.12);
        optimizationResult.put("annual_volatility", 0.15);
        optimizationResult.put("sharpe_ratio", 0.8);
        optimizationResult.put("value_at_risk", 5.0);

        when(pythonApiService.optimizeClassical(anyList(), eq(5.0)))
            .thenReturn(optimizationResult);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\",\"SIM_GOOGL\"],\"varPercent\":5.0}";

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.weights").exists())
                .andExpect(jsonPath("$.weights.SIM_AAPL").value(0.6))
                .andExpect(jsonPath("$.weights.SIM_GOOGL").value(0.4))
                .andExpect(jsonPath("$.expected_annual_return").value(0.12))
                .andExpect(jsonPath("$.sharpe_ratio").value(0.8));
    }

    @Test
    void testOptimizeEndpointPythonServiceUnhealthy() throws Exception {
        // Mock Python API health check failure
        when(pythonApiService.isHealthy()).thenReturn(false);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":5.0}";

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error").exists())
                .andExpect(jsonPath("$.error").value("Python optimization service is not available"));
    }

    @Test
    void testOptimizeEndpointPythonApiException() throws Exception {
        // Mock stock data loading
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(mockData);

        // Mock Python API health check success
        when(pythonApiService.isHealthy()).thenReturn(true);

        // Mock Python API optimization failure
        when(pythonApiService.optimizeClassical(anyList(), eq(5.0)))
            .thenThrow(new RuntimeException("Python API optimization failed"));

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":5.0}";

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").exists());
    }

    @Test
    void testOptimizeEndpointWithEmptyDatabase() throws Exception {
        // Mock Python API health check
        when(pythonApiService.isHealthy()).thenReturn(true);

        String requestJson = "{\"stocks\":[\"NONEXISTENT\"],\"varPercent\":5.0}";

        // No stocks loaded in database for NONEXISTENT symbol
        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").exists())
                .andExpect(jsonPath("$.error").value("No stock data available for optimization"));
    }

    // Hybrid Optimization Tests

    @Test
    void testHybridOptimizeEndpointSuccess() throws Exception {
        // Mock stock data loading
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 23), 2800.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 24), 2850.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(Arrays.asList(mockData.get(0), mockData.get(1)));
        when(alphaVantageService.fetchStockHistory("SIM_GOOGL", 30))
            .thenReturn(Arrays.asList(mockData.get(2), mockData.get(3)));

        // Mock Python API health check
        when(pythonApiService.isHealthy()).thenReturn(true);

        // Mock hybrid optimization response
        Map<String, Object> hybridResult = new HashMap<>();
        Map<String, Double> classicalWeights = Map.of("SIM_AAPL", 0.7, "SIM_GOOGL", 0.3);
        Map<String, Double> quantumWeights = Map.of("SIM_AAPL", 0.6, "SIM_GOOGL", 0.4);
        Map<String, Double> hybridWeights = Map.of("SIM_AAPL", 0.65, "SIM_GOOGL", 0.35);
        
        hybridResult.put("classical_weights", classicalWeights);
        hybridResult.put("quantum_weights", quantumWeights);
        hybridResult.put("hybrid_weights", hybridWeights);

        when(pythonApiService.optimizeHybrid(anyList(), eq(0.05), eq(true)))
            .thenReturn(hybridResult);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\",\"SIM_GOOGL\"],\"varPercent\":0.05,\"qcSimulator\":true}";

        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.classical_weights").exists())
                .andExpect(jsonPath("$.quantum_weights").exists())
                .andExpect(jsonPath("$.hybrid_weights").exists())
                .andExpect(jsonPath("$.hybrid_weights.SIM_AAPL").value(0.65));
    }

    @Test
    void testHybridOptimizeEndpointWithRealBackend() throws Exception {
        // Mock stock data loading
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(mockData);

        // Mock Python API health check
        when(pythonApiService.isHealthy()).thenReturn(true);

        // Mock hybrid optimization with real quantum backend
        Map<String, Object> hybridResult = new HashMap<>();
        hybridResult.put("classical_weights", Map.of("SIM_AAPL", 1.0));
        hybridResult.put("quantum_weights", Map.of("SIM_AAPL", 1.0));
        hybridResult.put("hybrid_weights", Map.of("SIM_AAPL", 1.0));

        when(pythonApiService.optimizeHybrid(anyList(), eq(0.05), eq(false)))
            .thenReturn(hybridResult);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":0.05,\"qcSimulator\":false}";

        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.quantum_weights").exists());
    }

    @Test
    void testHybridOptimizeEndpointPythonServiceDown() throws Exception {
        // Mock Python API health check failure
        when(pythonApiService.isHealthy()).thenReturn(false);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":0.05,\"qcSimulator\":true}";

        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error").value("Python optimization service is not available"));
    }

    @Test
    void testHybridOptimizeEndpointOptimizationFailure() throws Exception {
        // Mock stock data loading
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(mockData);

        // Mock Python API health check
        when(pythonApiService.isHealthy()).thenReturn(true);

        // Mock hybrid optimization failure
        when(pythonApiService.optimizeHybrid(anyList(), eq(0.05), eq(true)))
            .thenThrow(new RuntimeException("Hybrid optimization failed"));

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":0.05,\"qcSimulator\":true}";

        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").exists());
    }

    // Input Validation Tests

    @Test
    void testOptimizeEndpointInvalidVarPercent() throws Exception {
        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":-5.0}"; // Invalid negative

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").exists());
    }

    @Test
    void testOptimizeEndpointVarPercentTooHigh() throws Exception {
        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":150.0}"; // Invalid > 100

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testHybridOptimizeEndpointInvalidVarPercent() throws Exception {
        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":-0.05,\"qcSimulator\":true}"; // Invalid negative

        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testOptimizeEndpointMissingRequiredFields() throws Exception {
        String requestJson = "{\"stocks\":[\"SIM_AAPL\"]}"; // Missing varPercent

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testHybridOptimizeEndpointMissingRequiredFields() throws Exception {
        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":0.05}"; // Missing qcSimulator

        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testOptimizeEndpointEmptyStocksList() throws Exception {
        String requestJson = "{\"stocks\":[],\"varPercent\":5.0}";

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("No stocks specified for optimization"));
    }

    @Test
    void testLoadStocksEndpointInvalidPeriod() throws Exception {
        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"period\":-10}"; // Invalid negative period

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest());
    }

    // Performance and Edge Case Tests

    @Test
    void testOptimizeEndpointWithLargeStockList() throws Exception {
        // Create a large list of stocks
        List<String> stocks = new ArrayList<>();
        for (int i = 0; i < 50; i++) {
            stocks.add("SIM_STOCK" + i);
        }

        // Mock stock data for all stocks
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_STOCK0", LocalDate.of(2025, 9, 23), 100.0),
            new StockData("SIM_STOCK0", LocalDate.of(2025, 9, 24), 102.0)
        );

        for (String stock : stocks) {
            when(alphaVantageService.fetchStockHistory(stock, 30)).thenReturn(mockData);
        }

        // Mock Python API health check and optimization
        when(pythonApiService.isHealthy()).thenReturn(true);
        
        Map<String, Object> result = new HashMap<>();
        Map<String, Double> weights = new HashMap<>();
        for (String stock : stocks) {
            weights.put(stock, 1.0 / stocks.size()); // Equal weights
        }
        result.put("weights", weights);
        result.put("expected_annual_return", 0.10);
        result.put("annual_volatility", 0.20);
        result.put("sharpe_ratio", 0.5);
        result.put("value_at_risk", 5.0);

        when(pythonApiService.optimizeClassical(anyList(), eq(5.0))).thenReturn(result);

        String stocksJson = "\"" + String.join("\",\"", stocks) + "\"";
        String requestJson = "{\"stocks\":[" + stocksJson + "],\"varPercent\":5.0}";

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.weights").exists());
    }

    @Test
    void testOptimizeEndpointWithSingleStock() throws Exception {
        // Mock single stock data
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30)).thenReturn(mockData);
        when(pythonApiService.isHealthy()).thenReturn(true);

        Map<String, Object> result = new HashMap<>();
        result.put("weights", Map.of("SIM_AAPL", 1.0));
        result.put("expected_annual_return", 0.12);
        result.put("annual_volatility", 0.15);
        result.put("sharpe_ratio", 0.8);
        result.put("value_at_risk", 5.0);

        when(pythonApiService.optimizeClassical(anyList(), eq(5.0))).thenReturn(result);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":5.0}";

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.weights.SIM_AAPL").value(1.0));
    }
}