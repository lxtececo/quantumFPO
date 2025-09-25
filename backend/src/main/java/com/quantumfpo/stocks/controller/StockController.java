package com.quantumfpo.stocks.controller;
import com.quantumfpo.stocks.model.OptimizeRequest;
import com.quantumfpo.stocks.model.StockRequest;
import com.quantumfpo.stocks.model.StockData;
import com.quantumfpo.stocks.service.AlphaVantageService;
import com.quantumfpo.stocks.service.PythonApiService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import java.util.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
@RequestMapping("/api/stocks")
@CrossOrigin(origins = "http://localhost:5173")
public class StockController {
    private static final Logger logger = LoggerFactory.getLogger(StockController.class);
    private static final String ERROR_KEY = "error";
    
    private final AlphaVantageService alphaVantageService;
    private final PythonApiService pythonApiService;
    private final Map<String, List<StockData>> database = new HashMap<>();
    private List<String> lastLoadedSymbols = new ArrayList<>();

    public StockController(AlphaVantageService alphaVantageService, PythonApiService pythonApiService) {
        this.alphaVantageService = alphaVantageService;
        this.pythonApiService = pythonApiService;
    }

    @PostMapping("/load")
    public ResponseEntity<List<StockData>> loadStocks(@RequestBody StockRequest request) {
        try {
            int period = request.getPeriod() > 0 ? request.getPeriod() : 30;
            List<StockData> allData = new ArrayList<>();
            lastLoadedSymbols = new ArrayList<>(request.getStocks());
            
            for (String symbol : request.getStocks()) {
                List<StockData> data = alphaVantageService.fetchStockHistory(symbol, period);
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
            if (e.getMessage() != null && e.getMessage().contains("Service error")) {
                logger.warn("Error loading stocks: {}", e.getMessage());
            } else {
                logger.error("Error loading stocks: {}", e.getMessage(), e);
            }
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.emptyList());
        }
    }

    @PostMapping("/optimize")
    public ResponseEntity<Map<String, Object>> optimizePortfolio(@RequestBody OptimizeRequest request) {
        try {
            // Check Python API health first
            if (!pythonApiService.isHealthy()) {
                logger.warn("[REST] Python API service is not available");
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put(ERROR_KEY, "Python optimization service is not available. Please ensure it's running.");
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(errorResponse);
            }
            
            // Prepare stock data
            List<Map<String, Object>> stockData = prepareStockDataForApi(request);
            
            if (stockData.isEmpty()) {
                logger.warn("[REST] No stock data found for optimization");
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put(ERROR_KEY, "No stock data available for optimization. Please load stocks first.");
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            // Call Python REST API for classical optimization
            logger.info("[REST] Starting classical portfolio optimization via REST API");
            Map<String, Object> result = pythonApiService.optimizeClassical(stockData, request.getVarPercent());
            
            logger.info("[REST] Classical optimization completed successfully via REST API");
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("[REST] Error during classical portfolio optimization", e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put(ERROR_KEY, "Portfolio optimization failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PostMapping("/hybrid-optimize")
    public ResponseEntity<Map<String, Object>> hybridOptimizePortfolio(@RequestBody OptimizeRequest request) {
        try {
            // Check Python API health first
            if (!pythonApiService.isHealthy()) {
                logger.warn("[REST] Python API service is not available for hybrid optimization");
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put(ERROR_KEY, "Python optimization service is not available. Please ensure it's running.");
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(errorResponse);
            }
            
            // Prepare stock data
            List<Map<String, Object>> stockData = prepareStockDataForApi(request);
            
            if (stockData.isEmpty()) {
                logger.warn("[REST] No stock data found for hybrid optimization");
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put(ERROR_KEY, "No stock data available for optimization. Please load stocks first.");
                return ResponseEntity.badRequest().body(errorResponse);
            }
            
            // Call Python REST API for hybrid optimization
            logger.info("[REST] Starting hybrid portfolio optimization via REST API (simulator: {})", request.isQcSimulator());
            Map<String, Object> result = pythonApiService.optimizeHybrid(
                stockData, 
                request.getVarPercent(), 
                request.isQcSimulator()
            );
            
            logger.info("[REST] Hybrid optimization completed successfully via REST API");
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("[REST] Error during hybrid portfolio optimization", e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put(ERROR_KEY, "Hybrid optimization failed: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
    
    @GetMapping("/python-api/health")
    public ResponseEntity<Map<String, Object>> checkPythonApiHealth() {
        Map<String, Object> response = new HashMap<>();
        boolean healthy = pythonApiService.isHealthy();
        
        response.put("python_api_healthy", healthy);
        response.put("timestamp", java.time.LocalDateTime.now().toString());
        
        if (healthy) {
            response.put("message", "Python API service is running");
            return ResponseEntity.ok(response);
        } else {
            response.put("message", "Python API service is not available");
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
        }
    }

    /**
     * Prepare stock data in the format expected by Python API
     */
    private List<Map<String, Object>> prepareStockDataForApi(OptimizeRequest request) {
        List<Map<String, Object>> stockData = new ArrayList<>();
        List<String> symbols = (request.getStocks() != null && !request.getStocks().isEmpty()) 
            ? request.getStocks() : lastLoadedSymbols;
        
        for (String symbol : symbols) {
            List<StockData> data = database.getOrDefault(symbol, Collections.emptyList());
            for (StockData sd : data) {
                Map<String, Object> row = new HashMap<>();
                row.put("symbol", sd.getSymbol());
                row.put("date", sd.getDate().toString());
                row.put("close", sd.getClose());
                stockData.add(row);
            }
        }
        
        logger.info("[REST] Prepared {} stock data points for API call", stockData.size());
        return stockData;
    }
}
