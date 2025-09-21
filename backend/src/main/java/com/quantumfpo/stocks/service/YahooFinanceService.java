package com.quantumfpo.stocks.service;

import com.quantumfpo.stocks.model.StockData;
import org.springframework.stereotype.Service;
import yahoofinance.Stock;
import yahoofinance.YahooFinance;
import yahoofinance.histquotes.HistoricalQuote;
import yahoofinance.histquotes.Interval;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.*;

@Service
public class YahooFinanceService {
    public List<StockData> fetchStockHistory(String symbol, int days) throws Exception {
        Calendar from = Calendar.getInstance();
        from.add(Calendar.DAY_OF_YEAR, -days);
        Calendar to = Calendar.getInstance();
        Stock stock = YahooFinance.get(symbol);
        List<HistoricalQuote> history = stock.getHistory(from, to, Interval.DAILY);
        List<StockData> result = new ArrayList<>();
        for (HistoricalQuote hq : history) {
            if (hq.getClose() != null && hq.getDate() != null) {
                LocalDate date = hq.getDate().toInstant().atZone(ZoneId.systemDefault()).toLocalDate();
                result.add(new StockData(symbol, date, hq.getClose().doubleValue()));
            }
        }
        return result;
    }
}
