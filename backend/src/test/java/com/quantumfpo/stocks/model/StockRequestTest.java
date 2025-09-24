package com.quantumfpo.stocks.model;

import org.junit.jupiter.api.Test;
import java.util.Arrays;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class StockRequestTest {

    @Test
    void testStockRequestCreationAndGetters() {
        StockRequest request = new StockRequest();
        
        // Test initial state
        assertNull(request.getStocks());
        assertEquals(0, request.getPeriod());
        assertEquals(0, request.getStockAmount());
    }

    @Test
    void testStockRequestSetters() {
        StockRequest request = new StockRequest();
        List<String> stocks = Arrays.asList("AAPL", "GOOGL", "MSFT");
        int period = 30;
        int stockAmount = 5;
        
        request.setStocks(stocks);
        request.setPeriod(period);
        request.setStockAmount(stockAmount);
        
        assertEquals(stocks, request.getStocks());
        assertEquals(period, request.getPeriod());
        assertEquals(stockAmount, request.getStockAmount());
    }

    @Test
    void testStockRequestWithEmptyStocksList() {
        StockRequest request = new StockRequest();
        List<String> emptyStocks = Arrays.asList();
        
        request.setStocks(emptyStocks);
        
        assertEquals(emptyStocks, request.getStocks());
        assertTrue(request.getStocks().isEmpty());
    }

    @Test
    void testStockRequestWithNullStocksList() {
        StockRequest request = new StockRequest();
        
        request.setStocks(null);
        
        assertNull(request.getStocks());
    }

    @Test
    void testStockRequestWithNegativePeriod() {
        StockRequest request = new StockRequest();
        int negativePeriod = -10;
        
        request.setPeriod(negativePeriod);
        
        assertEquals(negativePeriod, request.getPeriod());
    }

    @Test
    void testStockRequestWithZeroPeriod() {
        StockRequest request = new StockRequest();
        
        request.setPeriod(0);
        
        assertEquals(0, request.getPeriod());
    }

    @Test
    void testStockRequestWithLargePeriod() {
        StockRequest request = new StockRequest();
        int largePeriod = 365 * 5; // 5 years
        
        request.setPeriod(largePeriod);
        
        assertEquals(largePeriod, request.getPeriod());
    }

    @Test
    void testStockRequestWithNegativeStockAmount() {
        StockRequest request = new StockRequest();
        int negativeAmount = -5;
        
        request.setStockAmount(negativeAmount);
        
        assertEquals(negativeAmount, request.getStockAmount());
    }

    @Test
    void testStockRequestWithSingleStock() {
        StockRequest request = new StockRequest();
        List<String> singleStock = Arrays.asList("TSLA");
        
        request.setStocks(singleStock);
        
        assertEquals(singleStock, request.getStocks());
        assertEquals(1, request.getStocks().size());
        assertEquals("TSLA", request.getStocks().get(0));
    }

    @Test
    void testStockRequestWithDuplicateStocks() {
        StockRequest request = new StockRequest();
        List<String> duplicateStocks = Arrays.asList("AAPL", "AAPL", "GOOGL");
        
        request.setStocks(duplicateStocks);
        
        assertEquals(duplicateStocks, request.getStocks());
        assertEquals(3, request.getStocks().size());
    }
}