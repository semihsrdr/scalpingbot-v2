import schedule
import time
import market
import trader
import config
import json
from datetime import datetime
import trade_logger

# ÖNCE trade modülünü import et
import trade

# Initialize portfolio ONCE at startup
portfolio = None
if config.SIMULATION_MODE:
    from simulation import SimulatedPortfolio
    portfolio = SimulatedPortfolio()
    # Şimdi portfolio'yu trade modülüne set et
    trade.set_portfolio(portfolio)
    print(f"[INIT] Portfolio initialized and shared with trade module.")

def check_tp_sl():
    """Checks open positions and closes them if TP/SL levels are hit."""
    if not config.SIMULATION_MODE:
        print("TP/SL check is currently only supported in simulation mode.")
        return

    open_positions = portfolio.get_all_open_positions()
    if not open_positions:
        return

    print("\n[MGM] Checking open positions for TP/SL...")
    for symbol, position in list(open_positions.items()):
        try:
            margin = position.get('margin', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            
            if margin == 0: 
                continue

            # More accurate PnL % calculation based on margin used
            pnl_pct = (unrealized_pnl / margin) * 100
            
            print(f"[{symbol}] PnL: {pnl_pct:.2f}% (Entry: {position['entry_price']}, Current: {position['current_price']}, PnL: ${unrealized_pnl:.2f})")

            # Check TP/SL
            if pnl_pct >= config.TAKE_PROFIT_PCT:
                reason = f"TAKE PROFIT triggered at {pnl_pct:.2f}%"
                print(f"✅ [{symbol}] {reason}")
                trade.parse_and_execute({"command": "close", "reasoning": reason}, symbol)
            elif pnl_pct <= -config.STOP_LOSS_PCT:
                reason = f"STOP LOSS triggered at {pnl_pct:.2f}%"
                print(f"❌ [{symbol}] {reason}")
                trade.parse_and_execute({"command": "close", "reasoning": reason}, symbol)

        except Exception as e:
            print(f"[{symbol}] Error during TP/SL check: {e}")


# --- State Management ---


cycle_count = 0


current_api_key_index = 0


# --- End State Management ---





def main_job():


    """


    Main job flow: Update PnL -> Check TP/SL -> For each symbol: Get Data -> Get Decision -> Execute


    """


    global cycle_count, current_api_key_index





    print(f"\n{'='*60}")


    print(f"--- Cycle Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Cycle #{cycle_count}) ---")


    print(f"--- Using API Key Index: {current_api_key_index} ---")


    print(f"{'='*60}")


    


    # 1. Update PnL for all open positions FIRST


    if config.SIMULATION_MODE and portfolio:


        print("\n[STEP 1] Updating open positions from market...")


        portfolio.update_open_positions()


        


        # Debug: Show what's in memory after update


        print(f"[DEBUG] Positions in memory: {list(portfolio.positions.keys())}")


        print(f"[DEBUG] Balance in memory: ${portfolio.balance:.2f}")





    # 2. Check for TP/SL on existing positions with the updated data


    if config.SIMULATION_MODE and portfolio:


        print("\n[STEP 2] Checking TP/SL triggers...")


        check_tp_sl()





    # 3. Get a fresh portfolio summary to be used by the AI


    portfolio_summary = {}


    if config.SIMULATION_MODE and portfolio:


        print("\n[STEP 3] Getting portfolio summary...")


        portfolio_summary = portfolio.get_portfolio_summary()


        print("[PF] Portfolio Summary:", json.dumps(portfolio_summary, indent=2))





    # 4. For each symbol, run the main trading logic


    print("\n[STEP 4] Processing trading symbols...")


    for symbol in config.TRADING_SYMBOLS:


        try:


            print(f"\n-> Processing {symbol}...")


            


            # a. Get market data and current position status


            market_summary = market.get_market_summary(symbol=symbol)


            if not market_summary:


                print(f"[{symbol}] Could not get market summary, skipping.")


                continue


            


            position_status = trade.get_current_position(symbol=symbol)


            


            # b. Get trade decision from LLM using the currently active API key


            active_api_key = config.GROQ_API_KEYS[current_api_key_index]


            print(f"[{symbol}] Data: {json.dumps(market_summary)}")


            print(f"[{symbol}] Current Position: {position_status[0]}")


            decision = trader.get_trade_decision(


                market_summary=market_summary, 


                position_status=position_status, 


                portfolio_summary=portfolio_summary,


                groq_api_key=active_api_key


            )





            # c. Execute the decision


            trade.parse_and_execute(decision, symbol)


            


        except Exception as e:


            print(f"[{symbol}] An unexpected error occurred in the main loop: {e}")


            import traceback


            traceback.print_exc()


    


    # 5. Increment cycle count and rotate API key if necessary


    cycle_count += 1


    if cycle_count % 60 == 0:


        previous_key_index = current_api_key_index


        current_api_key_index = (current_api_key_index + 1) % len(config.GROQ_API_KEYS)


        print(f"\n{'!'*20}")


        print(f"ROTATING API KEY: Switched from index {previous_key_index} to {current_api_key_index}.")


        print(f"{'!'*20}\n")





    print(f"\n{'='*60}")


    print(f"--- Cycle End: Next run in 1 minute ---")


    print(f"{'='*60}\n")


print("--- LLM Scalping Bot Initialized ---")
print(f"Trading Assets: {', '.join(config.TRADING_SYMBOLS)}")
print(f"LLM Model: {config.LLM_MODEL_NAME}")
print(f"Strategy: TP: {config.TAKE_PROFIT_PCT}% / SL: {config.STOP_LOSS_PCT}%")
print(f"Simulation Mode: {'Active' if config.SIMULATION_MODE else 'Inactive'}")
print(f"Run Interval: Every 1 minute")
print("------------------------------------")

print("\n[WORKER] Starting trading bot worker...")

# Schedule the main job to run every 1 minute
schedule.every(1).minutes.do(main_job)

# Run the job once immediately to start
main_job()

# Main loop for the scheduler
print("\n[SCHEDULER] Worker is now running. Press Ctrl+C to stop.\n")
while True:
    schedule.run_pending()
    time.sleep(1)