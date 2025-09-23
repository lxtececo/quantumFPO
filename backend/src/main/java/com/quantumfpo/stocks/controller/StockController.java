package com.quantumfpo.stocks.controller;
import com.quantumfpo.stocks.model.OptimizeRequest;
import com.quantumfpo.stocks.model.StockRequest;
import com.quantumfpo.stocks.model.StockData;
import com.quantumfpo.stocks.service.AlphaVantageService;
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
    private List<String> lastLoadedSymbols = new ArrayList<>();
    private static final String MESSAGE_KEY = "message";
    @PostMapping("/optimize")
    public ResponseEntity<Map<String, Object>> optimizePortfolio(@RequestBody OptimizeRequest request) {
        try {
            // Gather all stock data from the database
            List<Map<String, Object>> stockData = new ArrayList<>();
            List<String> symbols = (request.getStocks() != null && !request.getStocks().isEmpty()) ? request.getStocks() : lastLoadedSymbols;
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
            // Prepare JSON input for Python
            Map<String, Object> input = new HashMap<>();
            input.put("stock_data", stockData);
            input.put("var_percent", request.getVarPercent());
            String jsonInput = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(input);

            // Write input to temp file
            java.io.File inputFile = java.io.File.createTempFile("classic_input", ".json");
            java.nio.file.Files.write(inputFile.toPath(), jsonInput.getBytes());
            java.io.File outputFile = java.io.File.createTempFile("classic_output", ".json");

            // Call Python script with input/output file paths
            ProcessBuilder pb = new ProcessBuilder(
                "C:/Users/alexa/quantumFPO/.venv/Scripts/python.exe",
                "c:/Users/alexa/quantumFPO/backend/src/main/python/classic_portfolio_opt.py",
                inputFile.getAbsolutePath(),
                outputFile.getAbsolutePath()
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();
            StringBuilder stdoutBuilder = new StringBuilder();
            try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    logger.info("[Classic] Python event: {}", line);
                    stdoutBuilder.append(line).append("\n");
                }
            }
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, "Python optimizer error"));
            }
            // Extract JSON result from stdout
            String resultJson = extractJsonFromOutput(stdoutBuilder.toString());
            if (resultJson == null) {
                // Fallback: try reading from output file
                resultJson = new String(java.nio.file.Files.readAllBytes(outputFile.toPath()));
                logger.info("[Classic] Python output file fallback: {}", resultJson);
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> resultMap = new com.fasterxml.jackson.databind.ObjectMapper().readValue(resultJson, Map.class);
            return ResponseEntity.ok(resultMap);
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, "Thread was interrupted: " + ie.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, e.getMessage()));
        }
    }
    private static final Logger logger = LoggerFactory.getLogger(StockController.class);
    private final AlphaVantageService alphaVantageService;
    private final Map<String, List<StockData>> database = new HashMap<>();

    public StockController(AlphaVantageService alphaVantageService) {
        this.alphaVantageService = alphaVantageService;
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
            logger.error("Error loading stocks: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.emptyList());
        }
    }
    @PostMapping("/hybrid-optimize")
    public ResponseEntity<Map<String, Object>> hybridOptimizePortfolio(@RequestBody OptimizeRequest request) {
        try {
            List<Map<String, Object>> stockData = prepareStockData(request);
            Map<String, Object> input = new HashMap<>();
            input.put("stock_data", stockData);
            input.put("var_percent", request.getVarPercent());
            String jsonInput = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(input);

            logger.info("[Hybrid] Input to Python: {}", jsonInput);
            java.io.File tempFile = java.io.File.createTempFile("hybrid_input", ".json");
            writeJsonToFile(jsonInput, tempFile);
            logger.info("[Hybrid] Input JSON written to: {}", tempFile.getAbsolutePath());
            String qcSimulatorArg = request.isQcSimulator() ? "simulator" : "real";
            ProcessBuilder pb = new ProcessBuilder(
                "C:/Users/alexa/quantumFPO/.venv/Scripts/python.exe",
                "c:/Users/alexa/quantumFPO/backend/src/main/python/hybrid_portfolio_opt.py",
                tempFile.getAbsolutePath(),
                qcSimulatorArg
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();
            StringBuilder stdoutBuilder = new StringBuilder();
            try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    logger.info("[Hybrid] Python event: {}", line);
                    stdoutBuilder.append(line).append("\n");
                }
            }
            int exitCode = process.waitFor();
            logger.info("[Hybrid] Python process exit code: {}", exitCode);
            deleteTempFile(tempFile);
            String resultJson = extractJsonFromOutput(stdoutBuilder.toString());
            logger.info("[Hybrid] Extracted JSON result: {}", resultJson);
            if (resultJson == null) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, "Hybrid Python optimizer error: No valid JSON output"));
            }
            if (exitCode != 0) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, "Hybrid Python optimizer error"));
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> result = new com.fasterxml.jackson.databind.ObjectMapper().readValue(resultJson, Map.class);
            return ResponseEntity.ok(result);
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            logger.error("Hybrid optimization thread was interrupted: {}", ie.getMessage(), ie);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, "Thread was interrupted: " + ie.getMessage()));
        } catch (Exception e) {
            logger.error("Error in hybrid optimization: {}", e.getMessage(), e);
            if (e instanceof java.io.IOException) {
                logger.error("[Hybrid] IOException details:", e);
            }
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Collections.singletonMap(MESSAGE_KEY, e.getMessage()));
        }
    }

    private List<Map<String, Object>> prepareStockData(OptimizeRequest request) {
        List<Map<String, Object>> stockData = new ArrayList<>();
        List<String> symbols = (request.getStocks() != null && !request.getStocks().isEmpty()) ? request.getStocks() : lastLoadedSymbols;
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
        return stockData;
    }

    private void writeJsonToFile(String jsonInput, java.io.File tempFile) throws java.io.IOException {
        try (java.io.FileWriter fw = new java.io.FileWriter(tempFile)) {
            fw.write(jsonInput);
        }
    }

    private void deleteTempFile(java.io.File tempFile) {
        try {
            java.nio.file.Files.delete(tempFile.toPath());
            logger.info("[Hybrid] Temp file deleted successfully: {}", tempFile.getAbsolutePath());
        } catch (java.io.IOException delEx) {
            logger.warn("[Hybrid] Failed to delete temp file: {}", tempFile.getAbsolutePath(), delEx);
        }
    }

    private String extractJsonFromOutput(String rawOutput) {
        for (String line : rawOutput.split("\n")) {
            String trimmed = line.trim();
            if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
                return trimmed;
            }
        }
        return null;
    }
}
