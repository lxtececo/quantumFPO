package com.quantumfpo.stocks.controller;

import com.quantumfpo.stocks.service.AlphaVantageService;
import com.quantumfpo.stocks.service.PythonApiService;
import com.quantumfpo.stocks.model.StockData;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.http.MediaType;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

import static org.mockito.Mockito.when;
import static org.mockito.ArgumentMatchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
class StockControllerTest {

    @Autowired
    private WebApplicationContext webApplicationContext;
    
    private MockMvc mockMvc;

    @MockBean
    private AlphaVantageService alphaVantageService;

    @MockBean
    private PythonApiService pythonApiService;

    @BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build();
        Mockito.reset(alphaVantageService, pythonApiService);
        
        // Mock Python service to be healthy by default to prevent HTTP calls
        when(pythonApiService.isHealthy()).thenReturn(true);
        
        // Mock optimize methods to return success results by default
        Map<String, Object> defaultResult = new HashMap<>();
        defaultResult.put("success", true);
        defaultResult.put("message", "Mock optimization completed successfully");
        when(pythonApiService.optimizeClassical(anyList(), anyDouble())).thenReturn(defaultResult);
        when(pythonApiService.optimizeHybrid(anyList(), anyDouble(), anyBoolean())).thenReturn(defaultResult);
    }

    @Test
    void testLoadStocksEndpoint() throws Exception {
        // Mock service response
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(mockData);

        String requestJson = "{\"stocks\":[\"SIM_AAPL\"],\"period\":30}";

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].symbol").value("SIM_AAPL"))
                .andExpect(jsonPath("$[0].close").value(150.0))
                .andExpect(jsonPath("$[1].close").value(152.0));
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
            .thenThrow(new RuntimeException("Service error"));

        String requestJson = "{\"stocks\":[\"SIM_ERROR\"],\"period\":30}";

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isInternalServerError());
    }

    @Test
    void testOptimizePortfolioEndpointWithEmptyDatabase() throws Exception {
        String requestJson = "{\"stocks\":[\"AAPL\"],\"varPercent\":5}";

        // No stocks loaded in database and no mocks setup, should return 400 for no data
        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").exists())
                .andExpect(jsonPath("$.error").value("No stock data available for optimization"));
    }
    
    @Test
    void testHybridOptimizePortfolioEndpoint() throws Exception {
        // Test the hybrid optimization endpoint
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(mockData);

        // With proper mocking, this should return 200 OK (successful optimization)
        mockMvc.perform(post("/api/stocks/hybrid-optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"stocks\":[\"SIM_AAPL\"],\"varPercent\":0.05,\"qcSimulator\":true}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }
    
    @Test
    void testPrepareStockDataMethod() throws Exception {
        // Test to cover the prepareStockData method
        List<StockData> mockData = Arrays.asList(
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 23), 150.0),
            new StockData("SIM_AAPL", LocalDate.of(2025, 9, 24), 152.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 23), 2800.0),
            new StockData("SIM_GOOGL", LocalDate.of(2025, 9, 24), 2850.0)
        );
        
        when(alphaVantageService.fetchStockHistory("SIM_AAPL", 30))
            .thenReturn(mockData);
        when(alphaVantageService.fetchStockHistory("SIM_GOOGL", 30))
            .thenReturn(mockData);

        // This will exercise the prepareStockData method
        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"stocks\":[\"SIM_AAPL\",\"SIM_GOOGL\"],\"varPercent\":0.05,\"qcSimulator\":false}"))
                .andExpect(status().isOk());
    }
    
    @Test
    void testFetchStockDataEndpointWithErrorScenario() throws Exception {
        // Test error handling in fetchStockData (load endpoint)
        when(alphaVantageService.fetchStockHistory("INVALID_STOCK", 30))
            .thenThrow(new RuntimeException("Service error"));

        mockMvc.perform(post("/api/stocks/load")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"stocks\":[\"INVALID_STOCK\"],\"period\":30,\"stockAmount\":1}"))
                .andExpect(status().isInternalServerError());
    }
}