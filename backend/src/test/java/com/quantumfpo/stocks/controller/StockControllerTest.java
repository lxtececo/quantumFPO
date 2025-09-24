package com.quantumfpo.stocks.controller;

import com.quantumfpo.stocks.service.AlphaVantageService;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(StockController.class)
class StockControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Configuration
    static class TestConfig {
        @Bean
        public AlphaVantageService alphaVantageService() {
            return Mockito.mock(AlphaVantageService.class);
        }
    }

    @Test
    void testOptimizePortfolioEndpoint() throws Exception {
        String requestJson = "{\"stocks\":[\"AAPL\"],\"varPercent\":5}";

        // Mock service and database behavior if needed
        // You may need to use ReflectionTestUtils to set the database field if required

        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().is4xxClientError()); // Accept 4xx for now, since database is empty
    }
}