package com.quantumfpo.stocks.controller;

import com.quantumfpo.stocks.model.OptimizeRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.http.MediaType;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(StockController.class)
public class StockControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @Test
    public void testOptimizePortfolioEndpoint() throws Exception {
        String requestJson = "{\"stocks\":[\"AAPL\"],\"varPercent\":5}";
        mockMvc.perform(post("/api/stocks/optimize")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isOk());
    }
}
