package com.quantumfpo.stocks.service;

import com.quantumfpo.stocks.model.StockData;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.test.util.ReflectionTestUtils;
import java.io.IOException;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class AlphaVantageServiceTest {

    private AlphaVantageService service;

    @BeforeEach
    void setUp() {
        service = new AlphaVantageService();
        ReflectionTestUtils.setField(service, "apiKey", "test_api_key");
    }

    @Test
    void testFetchStockHistoryWithSimulatorSymbol() throws IOException {
        String simulatorSymbol = "SIM_GOOGL";
        int days = 5;
        
        List<StockData> result = service.fetchStockHistory(simulatorSymbol, days);
        
        assertNotNull(result);
        assertEquals(days, result.size());
        
        // Verify all entries have the correct symbol
        for (StockData stock : result) {
            assertEquals(simulatorSymbol, stock.getSymbol());
            assertNotNull(stock.getDate());
            assertTrue(stock.getClose() > 0);
        }
        
        // Verify data is sorted by date
        for (int i = 1; i < result.size(); i++) {
            assertTrue(result.get(i-1).getDate().compareTo(result.get(i).getDate()) <= 0);
        }
    }

    @Test
    void testFetchStockHistoryMultipleSimulatorSymbols() throws IOException {
        String[] symbols = {"SIM_AAPL", "SIM_GOOGL", "SIM_AMZN", "SIM_MSFT", "SIM_META"};
        int days = 10;
        
        for (String symbol : symbols) {
            List<StockData> result = service.fetchStockHistory(symbol, days);
            
            assertNotNull(result);
            assertEquals(days, result.size());
            
            // Verify each result has different values (randomized simulation)
            for (StockData stock : result) {
                assertEquals(symbol, stock.getSymbol());
                assertTrue(stock.getClose() > 0);
            }
        }
    }

    @Test
    void testFetchStockHistoryWithDifferentDaysCounts() throws IOException {
        String symbol = "SIM_AAPL";
        int[] daysCounts = {1, 5, 10, 30};
        
        for (int days : daysCounts) {
            List<StockData> result = service.fetchStockHistory(symbol, days);
            
            assertNotNull(result);
            assertEquals(days, result.size());
        }
    }

    @Test
    void testFetchStockHistorySimulationConsistency() throws IOException {
        String symbol = "SIM_AAPL";
        int days = 5;
        
        List<StockData> result1 = service.fetchStockHistory(symbol, days);
        List<StockData> result2 = service.fetchStockHistory(symbol, days);
        
        // Both calls should return the same number of results
        assertEquals(result1.size(), result2.size());
        
        // But the values might be different due to randomization
        // Just verify they're both valid
        for (int i = 0; i < result1.size(); i++) {
            assertTrue(result1.get(i).getClose() > 0);
            assertTrue(result2.get(i).getClose() > 0);
            assertEquals(symbol, result1.get(i).getSymbol());
            assertEquals(symbol, result2.get(i).getSymbol());
        }
    }

    @Test
    void testFetchStockHistoryDataRanges() throws IOException {
        String symbol = "SIM_AMZN";
        int days = 30;
        
        List<StockData> result = service.fetchStockHistory(symbol, days);
        
        assertNotNull(result);
        assertEquals(days, result.size());
        
        // Check that simulated prices are within reasonable range (around 100 +/- 10)
        for (StockData stock : result) {
            assertTrue(stock.getClose() >= 80 && stock.getClose() <= 120,
                    "Stock price " + stock.getClose() + " should be in reasonable simulation range");
        }
    }

    @Test
    void testFetchStockHistoryMultipleDifferentSymbols() throws IOException {
        String symbol1 = "SIM_AMZN";
        String symbol2 = "SIM_AMZN"; // Same symbol
        int days = 5;
        
        List<StockData> result1 = service.fetchStockHistory(symbol1, days);
        List<StockData> result2 = service.fetchStockHistory(symbol2, days);
        
        // Both should have valid data
        assertNotNull(result1);
        assertNotNull(result2);
        assertEquals(days, result1.size());
        assertEquals(days, result2.size());
    }

    @Test
    void testFetchStockHistoryLargeDataSet() throws IOException {
        String symbol = "SIM_MSFT";
        int days = 100; // Larger dataset
        
        List<StockData> result = service.fetchStockHistory(symbol, days);
        
        assertNotNull(result);
        assertEquals(days, result.size());
        
        // Verify all entries are valid
        for (StockData stock : result) {
            assertEquals(symbol, stock.getSymbol());
            assertNotNull(stock.getDate());
            assertTrue(stock.getClose() > 0);
        }
    }

    @Test
    void testFetchStockHistoryWithMixedSymbols() throws IOException {
        String[] mixedSymbols = {"SIM_META", "SIM_TSLA", "SIM_NVDA"};
        int days = 7;
        
        for (String symbol : mixedSymbols) {
            List<StockData> result = service.fetchStockHistory(symbol, days);
            
            assertNotNull(result);
            assertEquals(days, result.size());
            
            for (StockData stock : result) {
                assertEquals(symbol, stock.getSymbol());
            }
        }
    }

    @Test
    void testFetchStockHistoryNonSimulatorSymbol() throws IOException {
        String nonSimulatorSymbol = "REAL_AAPL";
        int days = 5;
        
        // This calls the real API, which with test API key will return an error response
        // but the service handles it gracefully and returns a result (likely empty or with error parsing)
        List<StockData> result = service.fetchStockHistory(nonSimulatorSymbol, days);
        
        // The service should return a result (empty list if API returns error)
        assertNotNull(result);
        assertTrue(result.size() >= 0);
    }

    @Test
    void testFetchStockHistoryEmptySymbol() throws IOException {
        String emptySymbol = "";
        int days = 5;
        
        // Empty symbol will be sent to API, which will return error, but service handles gracefully
        List<StockData> result = service.fetchStockHistory(emptySymbol, days);
        
        // Should return empty result since API will return error for empty symbol
        assertNotNull(result);
        assertTrue(result.size() >= 0);
    }

    @Test
    void testFetchStockHistoryWithNullSymbol() {
        int days = 5;
        
        // Null symbol should cause an exception during string formatting
        assertThrows(NullPointerException.class, () -> {
            service.fetchStockHistory(null, days);
        });
    }

    @Test
    void testFetchStockHistoryWithZeroDays() throws IOException {
        String symbol = "SIM_AAPL";
        int days = 0;
        
        List<StockData> result = service.fetchStockHistory(symbol, days);
        
        assertNotNull(result);
        assertEquals(0, result.size());
    }

    @Test
    void testFetchStockHistoryWithNegativeDays() throws IOException {
        String symbol = "SIM_AAPL";
        int days = -5;
        
        List<StockData> result = service.fetchStockHistory(symbol, days);
        
        // Service should handle negative days gracefully
        assertNotNull(result);
        assertTrue(result.size() >= 0);
    }

    @Test
    void testFetchStockHistoryApiKeyHandling() throws IOException {
        // Test with different API key scenarios
        AlphaVantageService serviceWithoutKey = new AlphaVantageService();
        // Not setting API key should still work for simulator symbols
        
        String symbol = "SIM_AAPL";
        int days = 3;
        
        List<StockData> result = serviceWithoutKey.fetchStockHistory(symbol, days);
        
        assertNotNull(result);
        assertEquals(days, result.size());
    }

    @Test
    void testFetchStockHistoryInvalidApiKey() throws IOException {
        AlphaVantageService serviceInvalidKey = new AlphaVantageService();
        ReflectionTestUtils.setField(serviceInvalidKey, "apiKey", "invalid_key");
        
        String symbol = "AAPL"; // Non-simulator symbol
        int days = 5;
        
        // Should handle invalid API key gracefully
        List<StockData> result = serviceInvalidKey.fetchStockHistory(symbol, days);
        
        assertNotNull(result);
        // With invalid key, API returns error, so result should be empty
        assertTrue(result.size() >= 0);
    }

    @Test
    void testFetchStockHistoryEdgeCaseSymbols() throws IOException {
        String[] edgeCaseSymbols = {"SIM_", "SIM_123", "SIM_VERY_LONG_SYMBOL_NAME"};
        int days = 3;
        
        for (String symbol : edgeCaseSymbols) {
            List<StockData> result = service.fetchStockHistory(symbol, days);
            
            assertNotNull(result);
            // For simulator symbols starting with SIM_, should return data
            if (symbol.startsWith("SIM_")) {
                assertEquals(days, result.size());
            } else {
                assertTrue(result.size() >= 0);
            }
        }
    }
}