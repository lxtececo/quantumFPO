package com.quantumfpo.stocks.controller;

import com.quantumfpo.stocks.service.AlphaVantageService;
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

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
class StockControllerTest {

    @Autowired
    private WebApplicationContext webApplicationContext;
    
    private MockMvc mockMvc;

    @MockBean
    private AlphaVantageService alphaVantageService;

    @BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build();
        Mockito.reset(alphaVantageService);
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

        // No stocks loaded in database, should return 200 with error in response body
        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.error").exists());
    }
}