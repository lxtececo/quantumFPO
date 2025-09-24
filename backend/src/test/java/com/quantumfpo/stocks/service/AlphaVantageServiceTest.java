package com.quantumfpo.stocks.service;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AlphaVantageServiceTest {
    @Test
    void testFetchStockHistory() {
        AlphaVantageService service = new AlphaVantageService();
        assertNotNull(service);
        // Add more detailed tests with mocks for API calls if needed
    }
}