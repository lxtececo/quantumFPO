package com.quantumfpo.stocks.controller;
import com.quantumfpo.stocks.model.OptimizeRequest;
import com.quantumfpo.stocks.model.StockRequest;
import com.quantumfpo.stocks.model.StockData;
import com.quantumfpo.stocks.service.AlphaVantageService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;

import java.util.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
@RequestMapping("/api/stocks")
@CrossOrigin(origins = "http://localhost:5173")
public class StockController {
    @PostMapping("/optimize")
    public ResponseEntity<?> optimizePortfolio(@RequestBody OptimizeRequest request) {
        try {
            // Gather all stock data from the database
            List<Map<String, Object>> stockData = new ArrayList<>();
            for (String symbol : request.getStocks()) {
                List<StockData> data = database.getOrDefault(symbol, Collections.emptyList());
                for (StockData sd : data) {
                    Map<String, Object> row = new HashMap<>();
                    row.put("symbol", sd.getSymbol());
                    row.put("date", sd.getDate().toString());
                    row.put("open", sd.getOpen());
                    row.put("high", sd.getHigh());
                    row.put("low", sd.getLow());
                    row.put("close", sd.getClose());
                    stockData.add(row);
                }
            }
            // Prepare JSON input for Python
            Map<String, Object> input = new HashMap<>();
            input.put("stock_data", stockData);
            input.put("var_percent", request.getVarPercent());
            String jsonInput = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(input);

            // Call Python script
            ProcessBuilder pb = new ProcessBuilder(
                "C:/Users/alexa/quantumFPO/.venv/Scripts/python.exe",
                "c:/Users/alexa/quantumFPO/backend/src/main/python/portfolio_opt.py"
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();
            try (java.io.OutputStream os = process.getOutputStream()) {
                os.write(jsonInput.getBytes());
                os.flush();
            }
            java.io.InputStream is = process.getInputStream();
            String resultJson = new String(is.readAllBytes());
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                logger.error("Python optimizer failed: {}", resultJson);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap("message", "Python optimizer error"));
            }
            // Return Python result
            return ResponseEntity.ok(new com.fasterxml.jackson.databind.ObjectMapper().readValue(resultJson, Map.class));
        } catch (Exception e) {
            logger.error("Error optimizing portfolio: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap("message", e.getMessage()));
        }
    }
    private static final Logger logger = LoggerFactory.getLogger(StockController.class);
    private final AlphaVantageService alphaVantageService;
    private final Map<String, List<StockData>> database = new HashMap<>();

    @Autowired
    public StockController(AlphaVantageService alphaVantageService) {
        this.alphaVantageService = alphaVantageService;
    }

    @PostMapping("/load")
    public ResponseEntity<?> loadStocks(@RequestBody StockRequest request) {
        try {
            List<StockData> allData = new ArrayList<>();
            for (String symbol : request.getStocks()) {
                List<StockData> data = alphaVantageService.fetchStockHistory(symbol, request.getPeriod());
                logger.info("Fetched data for {}: {} records", symbol, data.size());
                if (!data.isEmpty()) {
                    logger.info("Sample record for {}: {}", symbol, data.get(0));
                }
                database.put(symbol, data);
                allData.addAll(data);
            }
            logger.info("Returning total {} records to frontend", allData.size());
            return ResponseEntity.ok(allData);
        } catch (Exception e) {
            logger.error("Error loading stocks: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap("message", e.getMessage()));
        }
    }
}
