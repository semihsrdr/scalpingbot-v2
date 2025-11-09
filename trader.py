import config
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json

try:
    llm = ChatGroq(
        model=config.LLM_MODEL_NAME,
        groq_api_key=config.GROQ_API_KEY,
        temperature=0.7
    )
    print("Groq LLM connection successful.")
except Exception as e:
    print(f"Error initializing LLM: {e}")
    llm = None

SYSTEM_PROMPT = """
You are an expert scalping trader, executing trades on multiple assets on the Binance exchange.
Your task is to analyze the current market data and your portfolio status to make a trade decision for the next minute.

RULES:
1.  **Input:** You will receive data in JSON format with three parts: `portfolio_summary`, `market_data`, and `position_status`.
    *   `portfolio_summary` contains your overall balance and PnL.
    *   `market_data` contains the technical indicators for the specific asset.
    *   `position_status` tells you if you have an open position for that asset ('long', 'short', or 'flat').
2.  **Decisions:** Your possible commands are: 'long', 'short', 'hold', 'close'.
3.  **Leverage:** If you decide 'long' or 'short', you MUST specify a leverage between 10x and 50x. (e.g., "long 25x", "short 40x"). You can only open a new position if you are 'flat' for that asset.
4.  **Trade Size (Margin Allocation):**
    *   When opening a new position ('long' or 'short'), you MUST decide how much **margin** to allocate from your `available_balance_usd`.
    *   This is specified in the `trade_amount_usd` field. The total position size will be this margin multiplied by your chosen leverage.
    *   Based on your confidence in the trade, choose an amount to risk:
        *   Low confidence: ~5% of balance (e.g., $50 on a $1000 balance)
        *   Medium confidence: ~10% of balance (e.g., $100 on a $1000 balance)
        *   High confidence: ~20% of balance (e.g., $200 on a $1000 balance)
    *   For example, if the balance is $1000 and you are highly confident, you would set `trade_amount_usd` to 200. This will be your margin, and the position size will be $200 * leverage.
5.  **Logic:**
    *   **If Position is Open:** Your command should be 'hold' or 'close'. You cannot open a new position.
    *   **If No Position (flat):** Use market data (trend, RSI) to decide whether to 'long' or 'short'.
6.  **OUTPUT FORMAT:** Your response MUST be a JSON object with three keys: "reasoning", "command", and "trade_amount_usd".
    *   `reasoning`: A brief analysis explaining your thought process.
    *   `command`: The trading command string (e.g., "long 25x").
    *   `trade_amount_usd`: The amount in USD to use for the trade. This key is ONLY required for 'long' or 'short' commands. For 'hold' or 'close', it can be 0.
    *   EXAMPLE FOR OPENING A POSITION:
        {
          "reasoning": "The market is highly bullish and RSI is strong. I am confident in this long position and will allocate 20% of my balance.",
          "command": "long 25x",
          "trade_amount_usd": 200
        }
    *   EXAMPLE FOR HOLDING A POSITION:
        {
          "reasoning": "The bullish trend is continuing and my position is profitable. I will hold.",
          "command": "hold",
          "trade_amount_usd": 0
        }
    *   **CRITICAL:** Your entire output must be a single, valid JSON object. Do not add any text before or after it. Ensure all keys and string values are enclosed in double quotes.
"""

def get_trade_decision(market_summary: dict, position_status: tuple, portfolio_summary: dict) -> dict:
    """
    Takes market summary, position, and portfolio status, asks the LLM, and returns the trade decision dictionary.
    """
    default_decision = {"command": "hold", "trade_amount_usd": 0, "reasoning": "Default action."}
    if not llm:
        print("LLM not available. Defaulting to 'hold'.")
        return default_decision

    # Normalize position side for the LLM to be consistent with the prompt ('long'/'short')
    side, quantity = position_status
    if side == 'buy':
        side = 'long'
    elif side == 'sell':
        side = 'short'

    # Create a combined input for the LLM
    combined_input = {
        "portfolio_summary": portfolio_summary,
        "market_data": market_summary,
        "position_status": {
            "side": side,
            "quantity": quantity
        }
    }
    human_input = json.dumps(combined_input, indent=2)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_input)
    ]

    try:
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Parse the JSON output
        try:
            decision_json = json.loads(response_text)
            command = decision_json.get("command", "hold").lower()
            reasoning = decision_json.get("reasoning", "No reasoning provided.")
            trade_amount = decision_json.get("trade_amount_usd", 0)

            print(f"[AI Reasoning] {reasoning}")

            # Validate command and amount
            parts = command.split()
            action = parts[0]
            if action not in ['long', 'short', 'hold', 'close']:
                print(f"Invalid command action from LLM: '{action}'. Defaulting to 'hold'.")
                return default_decision

            if action in ['long', 'short']:
                if not isinstance(trade_amount, (int, float)) or trade_amount <= 0:
                    print(f"Invalid or missing 'trade_amount_usd' for new position. Got: {trade_amount}. Defaulting to 5% of balance.")
                    trade_amount = portfolio_summary.get('total_balance_usd', 1000) * 0.05
                
                # Cap the trade amount at 50% of balance for safety
                max_trade_size = portfolio_summary.get('total_balance_usd', 1000) * 0.5
                if trade_amount > max_trade_size:
                    print(f"Trade amount {trade_amount} exceeds safety cap. Adjusting to {max_trade_size}.")
                    trade_amount = max_trade_size

            return {
                "command": command,
                "trade_amount_usd": trade_amount,
                "reasoning": reasoning
            }

        except json.JSONDecodeError:
            print(f"Could not decode JSON from LLM response: '{response_text}'. Defaulting to 'hold'.")
            return default_decision

    except Exception as e:
        print(f"Error during LLM decision: {e}")
        return default_decision

# Bu dosyayı doğrudan çalıştırarak test edebilirsiniz
if __name__ == "__main__":
    test_market_data = {
        "symbol": "BTC/USDT",
        "current_price": 68500.50,
        "ema_20": 68450.0,
        "ema_50": 68300.0,
        "rsi_14": 62.0,
        "market_trend": "bullish"
    }
    test_position = ('flat', 0)
    test_portfolio = {
        "total_balance_usd": 1000.00,
        "unrealized_pnl_usd": 0
    }

    print("--- LLM Agent Testi (Yeni Pozisyon Açma) ---")
    print(f"Girdi: {json.dumps({'market_data': test_market_data, 'position': test_position, 'portfolio': test_portfolio}, indent=2)}")
    decision = get_trade_decision(test_market_data, test_position, test_portfolio)
    print(f"Çıktı (Karar): {decision}")

    print("\n--- LLM Agent Testi (Mevcut Pozisyonu Tutma) ---")
    test_position_hold = ('long', 0.01)
    test_portfolio_hold = {
        "total_balance_usd": 1050.75,
        "unrealized_pnl_usd": 50.25
    }
    print(f"Girdi: {json.dumps({'market_data': test_market_data, 'position': test_position_hold, 'portfolio': test_portfolio_hold}, indent=2)}")
    decision_hold = get_trade_decision(test_market_data, test_position_hold, test_portfolio_hold)
    print(f"Çıktı (Karar): {decision_hold}")