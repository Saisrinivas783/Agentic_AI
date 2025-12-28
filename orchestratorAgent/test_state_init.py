import logging
from schemas.state import OrchestratorState
from registry.loader import load_tools_from_yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_state_initialization():
    """Test if OrchestratorState initializes properly with registry"""
    
    try:
        # Step 1: Load registry
        logger.info("Loading registry...")
        registry = load_tools_from_yaml("registry/tools-config.yaml")
        logger.info(f"✅ Registry loaded successfully")
        logger.info(f"   Registry type: {type(registry)}")
        logger.info(f"   Registry keys: {list(registry.keys())}")
        
        # Step 2: Create state
        logger.info("\nCreating OrchestratorState...")
        state = OrchestratorState(
            query="Hello, can you help me with my insurance claim?",
            session_id="test-session-123",
            registry=registry
        )
        logger.info(f"✅ State initialized successfully")
        logger.info(f"   Query: {state.query}")
        logger.info(f"   Session ID: {state.session_id}")
        logger.info(f"   Registry tools count: {len(state.registry)}")
        
        # Step 3: Print registry tools
        logger.info("\nRegistry tools loaded:")
        for tool_name, tool_def in state.registry.items():
            logger.info(f"   - {tool_name}: {tool_def.description}")
        
        # Step 4: Print full state
        logger.info("\n========== FULL STATE ==========")
        logger.info(state.model_dump_json(indent=2))
        logger.info("================================")
            
        logger.info("\n✅ ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_state_initialization()