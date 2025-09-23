package com.quantumfpo.stocks.service;

import com.quantumfpo.stocks.model.StockData;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
// import org.springframework.http.client.ClientHttpRequestFactory; // removed unused import
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import java.io.IOException;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class AlphaVantageService {
    private static final Logger logger = LoggerFactory.getLogger(AlphaVantageService.class);
    @Value("${alphavantage.apikey}")
    private String apiKey;

    private final RestTemplate restTemplate;

    public AlphaVantageService() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        restTemplate = new RestTemplate(factory);
        // No User-Agent header added; mimics default browser request
    }

    public List<StockData> fetchStockHistory(String symbol, int days) throws IOException {
        // Simulator: If symbol starts with "SIM_", return mock data
        if (symbol.startsWith("SIM_")) {
            logger.info("Simulating Alpha Vantage response for symbol: {}", symbol);
            List<StockData> mockData = new ArrayList<>();
            LocalDate today = LocalDate.now();
            for (int i = 0; i < days; i++) {
                double close = 100 + (ThreadLocalRandom.current().nextDouble() - 0.5) * 20;
                mockData.add(new StockData(symbol, today.minusDays(i), close));
            }
            mockData.sort(Comparator.comparing(StockData::getDate));
            return mockData;
        }
        String url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=%s&apikey=%s".formatted(
                symbol, apiKey
        );
        logger.info("Requesting Alpha Vantage API: {}", url);
        ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
        logger.info("Alpha Vantage raw response: {}", response.getBody());
        ObjectMapper mapper = new ObjectMapper();
        JsonNode root = mapper.readTree(response.getBody());
        JsonNode timeSeries = root.path("Time Series (Daily)");
        List<StockData> result = new ArrayList<>();
        int count = 0;
        Iterator<String> dates = timeSeries.fieldNames();
        while (dates.hasNext() && count < days) {
            String dateStr = dates.next();
            JsonNode dayData = timeSeries.path(dateStr);
            if (dayData.has("4. close")) {
                double close = dayData.path("4. close").asDouble();
                result.add(new StockData(symbol, LocalDate.parse(dateStr), close));
                count++;
            }
        }
        result.sort(Comparator.comparing(StockData::getDate));
        return result;
    }
}
