//+------------------------------------------------------------------+
//| OMEGA / JARVIS: MT5 read-only broker observation (DEMO INVESTOR)  |
//| No trade/order API, no optimization, no historical/holdout reads. |
//| NEVER proves commission or a strategy profit factor.             |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs
#property version "1.00"

void OnStart()
{
   // Fail closed for any real account, disconnected terminal, or master
   // credentials that allow trading. Run using INVESTOR password only.
   if(TerminalInfoInteger(TERMINAL_CONNECTED) == 0)
   {
      Print("OMEGA_STOP: NOT_CONNECTED");
      return;
   }
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
   {
      Print("OMEGA_STOP: DEMO_ACCOUNT_REQUIRED");
      return;
   }
   if(AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) != 0 ||
      TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) != 0)
   {
      Print("OMEGA_STOP: INVESTOR_READONLY_LOGIN_AND_AUTOTRADING_OFF_REQUIRED");
      return;
   }

   // Never overwrite an earlier observation; do not create a CSV at all
   // when this is not a named broker server.
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "")
   {
      Print("OMEGA_STOP: BROKER_SERVER_MISSING");
      return;
   }
   const string export_name = "OMEGA_Mt5ReadOnlyBrokerSpec_v1.csv";
   if(FileIsExist(export_name))
   {
      Print("OMEGA_STOP: EXPORT_ALREADY_EXISTS_NO_OVERWRITE");
      return;
   }
   const string names[] = {"EURUSD", "GBPUSD", "USDJPY", "XAUUSD"};
   int output = FileOpen(export_name,
                         FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(output == INVALID_HANDLE)
   {
      Print("OMEGA_STOP: CANNOT_OPEN_SANDBOX_EXPORT");
      return;
   }
   FileWrite(output, "observed_utc", "tick_server_time", "server", "symbol",
             "bid", "ask", "point", "tick_size", "tick_value",
             "contract_size", "lot_min", "lot_step", "lot_max",
             "spread_points", "spread_float", "stops_level",
             "swap_long", "swap_short", "execution_mode",
             "quote_status", "commission_status");
   int rows = 0;
   for(int i = 0; i < ArraySize(names); i++)
   {
      string symbol = names[i];
      if(!SymbolSelect(symbol, true))
      {
         Print("OMEGA_SKIP: SYMBOL_NOT_AVAILABLE ", symbol);
         continue;
      }
      MqlTick tick;
      bool received = SymbolInfoTick(symbol, tick);
      if(!received || tick.bid <= 0.0 || tick.ask < tick.bid)
      {
         Print("OMEGA_SKIP: VALID_BID_ASK_MISSING ", symbol);
         continue;
      }
      // A valid BID/ASK alone is insufficient: cached MT5 quotes can be old.
      // Tick time and TimeTradeServer use the BROKER SERVER time basis.
      // TimeTradeServer is CLIENT-ESTIMATED and not independent NTP proof.
      // TimeGMT is used ONLY for the separately labelled observation time.
      datetime now_server = TimeTradeServer();
      long quote_age_seconds = (long)now_server - (long)tick.time;
      if(now_server <= 0 || tick.time <= 0 ||
         quote_age_seconds > 120 || quote_age_seconds < -120)
      {
         Print("OMEGA_SKIP: STALE_OR_FUTURE_TICK_UNVERIFIED_CLOCK ", symbol);
         continue;
      }
      double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
      if(point <= 0.0 || tick_size <= 0.0)
      {
         Print("OMEGA_SKIP: POINT_OR_TICK_SIZE_INVALID ", symbol);
         continue;
      }
      FileWrite(output,
                TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
                TimeToString(tick.time, TIME_DATE | TIME_SECONDS),
                server, symbol,
                DoubleToString(tick.bid, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
                DoubleToString(tick.ask, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
                DoubleToString(point, 9),
                DoubleToString(tick_size, 9),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE), 9),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE), 5),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN), 5),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP), 5),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX), 5),
                (int)SymbolInfoInteger(symbol, SYMBOL_SPREAD),
                (int)SymbolInfoInteger(symbol, SYMBOL_SPREAD_FLOAT),
                (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SWAP_LONG), 6),
                DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SWAP_SHORT), 6),
                (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_EXEMODE),
                "CURRENT_TICK_ONLY_NOT_FILL",
                "UNVERIFIED_REQUIRES_ACCOUNT_FEE_SCHEDULE");
      rows++;
   }
   FileClose(output);
   if(rows == 0)
   {
      Print("OMEGA_STOP: NO_VALID_QUOTES_HEADER_ONLY_EXPORT_NOT_EVIDENCE");
      return;
   }
   Print("OMEGA_READONLY_EXPORT_COMPLETED_BUT_NOT_COST_VERIFIED: rows=", rows);
}
