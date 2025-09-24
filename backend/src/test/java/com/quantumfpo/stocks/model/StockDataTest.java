package com.quantumfpo.stocks.model;

import org.junit.jupiter.api.Test;
import java.time.LocalDate;
import static org.junit.jupiter.api.Assertions.*;

class StockDataTest {

    @Test
    void testStockDataCreation() {
        String symbol = "AAPL";
        LocalDate date = LocalDate.of(2025, 9, 23);
        double close = 150.75;
        
        StockData stockData = new StockData(symbol, date, close);
        
        assertEquals(symbol, stockData.getSymbol());
        assertEquals(date, stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }

    @Test
    void testStockDataWithNullSymbol() {
        LocalDate date = LocalDate.of(2025, 9, 23);
        double close = 150.75;
        
        StockData stockData = new StockData(null, date, close);
        
        assertNull(stockData.getSymbol());
        assertEquals(date, stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }

    @Test
    void testStockDataWithNullDate() {
        String symbol = "AAPL";
        double close = 150.75;
        
        StockData stockData = new StockData(symbol, null, close);
        
        assertEquals(symbol, stockData.getSymbol());
        assertNull(stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }

    @Test
    void testStockDataWithZeroClose() {
        String symbol = "AAPL";
        LocalDate date = LocalDate.of(2025, 9, 23);
        double close = 0.0;
        
        StockData stockData = new StockData(symbol, date, close);
        
        assertEquals(symbol, stockData.getSymbol());
        assertEquals(date, stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }

    @Test
    void testStockDataWithNegativeClose() {
        String symbol = "AAPL";
        LocalDate date = LocalDate.of(2025, 9, 23);
        double close = -10.0;
        
        StockData stockData = new StockData(symbol, date, close);
        
        assertEquals(symbol, stockData.getSymbol());
        assertEquals(date, stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }

    @Test
    void testStockDataWithVeryLargeClose() {
        String symbol = "BERKSHIRE";
        LocalDate date = LocalDate.of(2025, 9, 23);
        double close = 500000.99;
        
        StockData stockData = new StockData(symbol, date, close);
        
        assertEquals(symbol, stockData.getSymbol());
        assertEquals(date, stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }

    @Test
    void testStockDataWithEmptySymbol() {
        String symbol = "";
        LocalDate date = LocalDate.of(2025, 9, 23);
        double close = 150.75;
        
        StockData stockData = new StockData(symbol, date, close);
        
        assertEquals(symbol, stockData.getSymbol());
        assertTrue(stockData.getSymbol().isEmpty());
        assertEquals(date, stockData.getDate());
        assertEquals(close, stockData.getClose(), 0.001);
    }
}