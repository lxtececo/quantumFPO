package com.quantumfpo.stocks.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.lang.reflect.Field;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Comprehensive test suite for PythonApiService.
 * Tests REST API communication with Python FastAPI service.
 */
@ExtendWith(MockitoExtension.class)
@SuppressWarnings({"unchecked", "rawtypes"})
class PythonApiServiceTest {

    @Mock
    private RestTemplate restTemplate;

    private PythonApiService pythonApiService;

    @BeforeEach
    void setUp() throws Exception {
        pythonApiService = new PythonApiService();
        
        // Use reflection to set the private RestTemplate field
        Field restTemplateField = PythonApiService.class.getDeclaredField("restTemplate");
        restTemplateField.setAccessible(true);
        restTemplateField.set(pythonApiService, restTemplate);
        
        // Set the base URL using reflection
        Field baseUrlField = PythonApiService.class.getDeclaredField("pythonApiBaseUrl");
        baseUrlField.setAccessible(true);
        baseUrlField.set(pythonApiService, "http://localhost:8002");
    }

    @Test
    void testOptimizeClassicalSuccess() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 5.0;

        // Prepare expected response
        Map<String, Object> expectedResponse = createExpectedOptimizationResponse();

        // Mock RestTemplate response
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(expectedResponse, HttpStatus.OK);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute method
        Map<String, Object> result = pythonApiService.optimizeClassical(stockData, varPercent);

        // Verify results
        assertNotNull(result);
        assertEquals(expectedResponse, result);
        
        // Verify RestTemplate was called with correct parameters
        verify(restTemplate).exchange(
            eq("http://localhost:8002/api/optimize/classical"),
            eq(HttpMethod.POST),
            argThat(entity -> {
                HttpHeaders headers = entity.getHeaders();
                Map<String, Object> body = (Map<String, Object>) entity.getBody();
                return headers != null && headers.getContentType() != null &&
                       headers.getContentType().equals(MediaType.APPLICATION_JSON) &&
                       body != null && body.containsKey("stock_data") &&
                       body.containsKey("var_percent") &&
                       body.get("var_percent").equals(0.05); // varPercent converted to decimal
            }),
            eq(Map.class)
        );
    }

    @Test
    void testOptimizeClassicalRestClientException() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 5.0;

        // Mock RestTemplate to throw exception
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenThrow(new RestClientException("Connection failed"));

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeClassical(stockData, varPercent);
        });

        assertTrue(exception.getMessage().contains("Could not connect to Python API service"));
    }

    @Test
    void testOptimizeClassicalNon200Response() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 5.0;

        // Mock RestTemplate response with error status
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(Collections.emptyMap(), HttpStatus.INTERNAL_SERVER_ERROR);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeClassical(stockData, varPercent);
        });

        assertEquals("Classical optimization failed: Python API returned unexpected response", exception.getMessage());
    }

    @Test
    void testOptimizeClassicalNullResponseBody() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 5.0;

        // Mock RestTemplate response with null body (which is a failure case)
        ResponseEntity<Map> responseEntity = ResponseEntity.ok(null);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeClassical(stockData, varPercent);
        });

        assertEquals("Classical optimization failed: Python API returned unexpected response", exception.getMessage());
    }

    @Test
    void testOptimizeHybridSuccess() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 0.05;
        boolean useSimulator = true;

        // Prepare expected response
        Map<String, Object> expectedResponse = createExpectedHybridResponse();

        // Mock RestTemplate response
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(expectedResponse, HttpStatus.OK);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute method
        Map<String, Object> result = pythonApiService.optimizeHybrid(stockData, varPercent, useSimulator);

        // Verify results
        assertNotNull(result);
        assertEquals(expectedResponse, result);
        
        // Verify RestTemplate was called with correct parameters
        verify(restTemplate).exchange(
            eq("http://localhost:8002/api/optimize/hybrid"),
            eq(HttpMethod.POST),
            argThat(entity -> {
                Map<String, Object> body = (Map<String, Object>) entity.getBody();
                return body != null && body.containsKey("stock_data") &&
                       body.containsKey("var_percent") &&
                       body.containsKey("qc_simulator") &&
                       body.get("qc_simulator").equals(useSimulator);
            }),
            eq(Map.class)
        );
    }

    @Test
    void testOptimizeHybridWithRealBackend() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 0.05;
        boolean useSimulator = false; // Use real quantum backend

        // Prepare expected response
        Map<String, Object> expectedResponse = createExpectedHybridResponse();

        // Mock RestTemplate response
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(expectedResponse, HttpStatus.OK);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute method
        Map<String, Object> result = pythonApiService.optimizeHybrid(stockData, varPercent, useSimulator);

        // Verify results
        assertNotNull(result);
        
        // Verify use_simulator was set to false
        verify(restTemplate).exchange(
            anyString(),
            eq(HttpMethod.POST),
            argThat(entity -> {
                Map<String, Object> body = (Map<String, Object>) entity.getBody();
                return body != null && body.get("qc_simulator").equals(false);
            }),
            eq(Map.class)
        );
    }

    @Test
    void testOptimizeHybridRestClientException() {
        // Prepare test data
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = 0.05;
        boolean useSimulator = true;

        // Mock RestTemplate to throw exception
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenThrow(new RestClientException("Connection timeout"));

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeHybrid(stockData, varPercent, useSimulator);
        });

        assertTrue(exception.getMessage().contains("Could not connect to Python API service"));
    }

    @Test
    void testIsHealthySuccess() {
        // Mock RestTemplate response
        ResponseEntity<String> responseEntity = new ResponseEntity<>("{\"status\":\"healthy\"}", HttpStatus.OK);
        when(restTemplate.getForEntity(
            anyString(),
            eq(String.class)
        )).thenReturn(responseEntity);

        // Execute method
        boolean isHealthy = pythonApiService.isHealthy();

        // Verify results
        assertTrue(isHealthy);
        
        // Verify RestTemplate was called with correct URL
        verify(restTemplate).getForEntity(
            "http://localhost:8002/health",
            String.class
        );
    }

    @Test
    void testIsHealthyPythonServiceDown() {
        // Mock RestTemplate to throw connection exception
        when(restTemplate.getForEntity(
            anyString(),
            eq(String.class)
        )).thenThrow(new RestClientException("Connection refused"));

        // Execute method
        boolean isHealthy = pythonApiService.isHealthy();

        // Verify results
        assertFalse(isHealthy);
    }

    @Test
    void testIsHealthyUnhealthyResponse() {
        // Mock RestTemplate response - the service only calls getForEntity, so this test is not valid
        // The actual service only checks for 200 status code, not response content
        // Mock RestTemplate response with non-200 status
        ResponseEntity<String> responseEntity = new ResponseEntity<>("{\"status\":\"unhealthy\"}", HttpStatus.SERVICE_UNAVAILABLE);
        when(restTemplate.getForEntity(
            anyString(),
            eq(String.class)
        )).thenReturn(responseEntity);

        // Execute method
        boolean isHealthy = pythonApiService.isHealthy();

        // Verify results
        assertFalse(isHealthy);
    }

    @Test
    void testIsHealthyNon200Status() {
        // Mock RestTemplate response with error status
        ResponseEntity<String> responseEntity = new ResponseEntity<>("", HttpStatus.SERVICE_UNAVAILABLE);
        when(restTemplate.getForEntity(
            anyString(),
            eq(String.class)
        )).thenReturn(responseEntity);

        // Execute method
        boolean isHealthy = pythonApiService.isHealthy();

        // Verify results
        assertFalse(isHealthy);
    }

    @Test
    void testOptimizeClassicalWithEmptyStockData() {
        // Prepare empty stock data
        List<Map<String, Object>> stockData = new ArrayList<>();
        double varPercent = 5.0;

        // Mock error response from Python API
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", "stock_data cannot be empty");
        
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeClassical(stockData, varPercent);
        });

        assertEquals("Classical optimization failed: Python API returned unexpected response", exception.getMessage());
    }

    @Test
    void testOptimizeClassicalWithInvalidVarPercent() {
        // Prepare test data with invalid VaR percent
        List<Map<String, Object>> stockData = createSampleStockData();
        double varPercent = -5.0; // Invalid negative value

        // Mock error response from Python API
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", "var_percent must be between 0 and 100");
        
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeClassical(stockData, varPercent);
        });

        assertEquals("Classical optimization failed: Python API returned unexpected response", exception.getMessage());
    }

    @Test
    void testOptimizeHybridWithInvalidStockData() {
        // Prepare invalid stock data (missing required fields)
        List<Map<String, Object>> stockData = Arrays.asList(
            Map.of("symbol", "AAPL") // Missing date and close
        );
        double varPercent = 0.05;
        boolean useSimulator = true;

        // Mock validation error response
        ResponseEntity<Map> responseEntity = new ResponseEntity<>(Collections.emptyMap(), HttpStatus.UNPROCESSABLE_ENTITY);
        when(restTemplate.exchange(
            anyString(),
            eq(HttpMethod.POST),
            any(HttpEntity.class),
            eq(Map.class)
        )).thenReturn(responseEntity);

        // Execute and verify exception
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            pythonApiService.optimizeHybrid(stockData, varPercent, useSimulator);
        });

        assertEquals("Hybrid optimization failed: Python API returned unexpected response", exception.getMessage());
    }

    // Helper methods

    private List<Map<String, Object>> createSampleStockData() {
        return Arrays.asList(
            Map.of(
                "symbol", "AAPL",
                "date", "2025-09-01",
                "close", 150.0
            ),
            Map.of(
                "symbol", "AAPL", 
                "date", "2025-09-02",
                "close", 152.0
            ),
            Map.of(
                "symbol", "GOOGL",
                "date", "2025-09-01", 
                "close", 2800.0
            ),
            Map.of(
                "symbol", "GOOGL",
                "date", "2025-09-02",
                "close", 2820.0
            )
        );
    }

    private Map<String, Object> createExpectedOptimizationResponse() {
        Map<String, Object> weights = new HashMap<>();
        weights.put("AAPL", 0.6);
        weights.put("GOOGL", 0.4);

        Map<String, Object> response = new HashMap<>();
        response.put("weights", weights);
        response.put("expected_annual_return", 0.12);
        response.put("annual_volatility", 0.15);
        response.put("sharpe_ratio", 0.8);
        response.put("value_at_risk", 5.0);

        return response;
    }

    private Map<String, Object> createExpectedHybridResponse() {
        Map<String, Object> classicalWeights = new HashMap<>();
        classicalWeights.put("AAPL", 0.7);
        classicalWeights.put("GOOGL", 0.3);

        Map<String, Object> quantumWeights = new HashMap<>();
        quantumWeights.put("AAPL", 0.6);
        quantumWeights.put("GOOGL", 0.4);

        Map<String, Object> hybridWeights = new HashMap<>();
        hybridWeights.put("AAPL", 0.65);
        hybridWeights.put("GOOGL", 0.35);

        Map<String, Object> performanceMetrics = new HashMap<>();
        performanceMetrics.put("classical_sharpe", 0.8);
        performanceMetrics.put("quantum_sharpe", 0.85);
        performanceMetrics.put("hybrid_sharpe", 0.82);

        Map<String, Object> response = new HashMap<>();
        response.put("classical_weights", classicalWeights);
        response.put("quantum_weights", quantumWeights);
        response.put("hybrid_weights", hybridWeights);
        response.put("performance_metrics", performanceMetrics);

        return response;
    }
}