import time
import logging
from trading_api import fetch_market_data, generate_signal, log_signal, execute_trade, update_dashboard

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SLEEP_INTERVAL = 60  # 1 min
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def initialize_trading():
    """Initialize trading system and validate connections."""
    logger.info("Initializing trading system...")
    try:
        # Validate API connectivity
        test_data = fetch_market_data()
        if test_data:
            logger.info("Trading system initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to initialize trading system: {e}")
        return False

def run_trading_with_retry():
    """Execute trading pipeline with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            run_trading()
            return True
        except Exception as e:
            logger.warning(f"Trading attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Trading failed after {MAX_RETRIES} attempts")
                return False

def run_trading():
    """Main trading pipeline execution."""
    try:
        # Fetch market data
        markets = fetch_market_data()
        if not markets:
            logger.warning("No market data available")
            return
        
        logger.info(f"Processing {len(markets)} markets")
        
        # Process each market
        for market in markets:
            try:
                # Generate trading signal
                signal = generate_signal(market)
                
                if signal and signal.confidence >= 0.8:
                    logger.info(f"High-confidence signal generated for {market}: confidence={signal.confidence}")
                    
                    # Log the signal
                    log_signal(signal)
                    
                    # Execute trade
                    trade_result = execute_trade(signal)
                    
                    # Update dashboard
                    update_dashboard(
                        trading_ROI=signal.estimated_ROI,
                        signal_executed=True,
                        trade_id=getattr(trade_result, 'id', None),
                        status='success'
                    )
                    logger.info(f"Trade executed successfully for {market}")
                else:
                    logger.debug(f"Signal confidence too low for {market}: {signal.confidence if signal else 'N/A'}")
                    
            except Exception as e:
                logger.error(f"Error processing market {market}: {e}")
                update_dashboard(status='error', error_message=str(e))
                continue
                
    except Exception as e:
        logger.error(f"Critical error in trading pipeline: {e}")
        raise

if __name__ == "__main__":
    # Initialize system
    if not initialize_trading():
        logger.critical("Failed to initialize trading system. Exiting.")
        exit(1)
    
    logger.info(f"Starting trading pipeline (interval: {SLEEP_INTERVAL}s)")
    
    # Main loop
    try:
        while True:
            run_trading_with_retry()
            time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Trading pipeline stopped by user")
    except Exception as e:
        logger.critical(f"Unexpected error in main loop: {e}")