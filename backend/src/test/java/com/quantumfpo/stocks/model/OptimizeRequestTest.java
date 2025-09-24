package com.quantumfpo.stocks.model;

import org.junit.jupiter.api.Test;
import java.util.Arrays;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class OptimizeRequestTest {

    @Test
    void testOptimizeRequestCreationAndDefaults() {
        OptimizeRequest request = new OptimizeRequest();
        
        // Test initial state and defaults
        assertNull(request.getStocks());
        assertEquals(0.0, request.getVarPercent(), 0.001);
        assertTrue(request.isQcSimulator()); // Default should be true
    }

    @Test
    void testOptimizeRequestSetters() {
        OptimizeRequest request = new OptimizeRequest();
        List<String> stocks = Arrays.asList("AAPL", "GOOGL", "MSFT");
        double varPercent = 5.0;
        boolean qcSimulator = false;
        
        request.setStocks(stocks);
        request.setVarPercent(varPercent);
        request.setQcSimulator(qcSimulator);
        
        assertEquals(stocks, request.getStocks());
        assertEquals(varPercent, request.getVarPercent(), 0.001);
        assertFalse(request.isQcSimulator());
    }

    @Test
    void testOptimizeRequestWithEmptyStocksList() {
        OptimizeRequest request = new OptimizeRequest();
        List<String> emptyStocks = Arrays.asList();
        
        request.setStocks(emptyStocks);
        
        assertEquals(emptyStocks, request.getStocks());
        assertTrue(request.getStocks().isEmpty());
    }

    @Test
    void testOptimizeRequestWithNullStocksList() {
        OptimizeRequest request = new OptimizeRequest();
        
        request.setStocks(null);
        
        assertNull(request.getStocks());
    }

    @Test
    void testOptimizeRequestWithZeroVarPercent() {
        OptimizeRequest request = new OptimizeRequest();
        
        request.setVarPercent(0.0);
        
        assertEquals(0.0, request.getVarPercent(), 0.001);
    }

    @Test
    void testOptimizeRequestWithNegativeVarPercent() {
        OptimizeRequest request = new OptimizeRequest();
        double negativeVar = -5.0;
        
        request.setVarPercent(negativeVar);
        
        assertEquals(negativeVar, request.getVarPercent(), 0.001);
    }

    @Test
    void testOptimizeRequestWithLargeVarPercent() {
        OptimizeRequest request = new OptimizeRequest();
        double largeVar = 100.0;
        
        request.setVarPercent(largeVar);
        
        assertEquals(largeVar, request.getVarPercent(), 0.001);
    }

    @Test
    void testOptimizeRequestWithDecimalVarPercent() {
        OptimizeRequest request = new OptimizeRequest();
        double decimalVar = 2.5;
        
        request.setVarPercent(decimalVar);
        
        assertEquals(decimalVar, request.getVarPercent(), 0.001);
    }

    @Test
    void testOptimizeRequestQcSimulatorToggle() {
        OptimizeRequest request = new OptimizeRequest();
        
        // Test default
        assertTrue(request.isQcSimulator());
        
        // Test setting to false
        request.setQcSimulator(false);
        assertFalse(request.isQcSimulator());
        
        // Test setting back to true
        request.setQcSimulator(true);
        assertTrue(request.isQcSimulator());
    }

    @Test
    void testOptimizeRequestWithSingleStock() {
        OptimizeRequest request = new OptimizeRequest();
        List<String> singleStock = Arrays.asList("BTC");
        
        request.setStocks(singleStock);
        
        assertEquals(singleStock, request.getStocks());
        assertEquals(1, request.getStocks().size());
        assertEquals("BTC", request.getStocks().get(0));
    }

    @Test
    void testOptimizeRequestWithManyStocks() {
        OptimizeRequest request = new OptimizeRequest();
        List<String> manyStocks = Arrays.asList("AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN", "NFLX");
        
        request.setStocks(manyStocks);
        
        assertEquals(manyStocks, request.getStocks());
        assertEquals(8, request.getStocks().size());
    }

    @Test
    void testOptimizeRequestCompleteScenario() {
        OptimizeRequest request = new OptimizeRequest();
        List<String> stocks = Arrays.asList("AAPL", "GOOGL");
        double varPercent = 3.5;
        boolean useSimulator = false;
        
        request.setStocks(stocks);
        request.setVarPercent(varPercent);
        request.setQcSimulator(useSimulator);
        
        // Verify all fields are set correctly
        assertEquals(stocks, request.getStocks());
        assertEquals(varPercent, request.getVarPercent(), 0.001);
        assertEquals(useSimulator, request.isQcSimulator());
        
        // Verify specific values
        assertEquals(2, request.getStocks().size());
        assertFalse(request.isQcSimulator());
        assertTrue(request.getVarPercent() > 3.0 && request.getVarPercent() < 4.0);
    }
}