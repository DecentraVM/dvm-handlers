from .runners import get_runner
from .runners.base import BaseRunner
import logging
import json
import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s   %(name)s  [%(levelname)s]    %(message)s",
    handlers=[logging.StreamHandler()]
)


def runner_handler(payload):
    input_data = payload
    if not input_data:
        raise ValueError("No json input received in payload")

    code = input_data.get("code", "")
    language = input_data.get("language", "python")
    dependencies = input_data.get("dependencies")
    inputs = input_data.get("input", {})
    env_vars = input_data.get("env", {})
    execution_timeout = input_data.get(
        "execution_timeout",
        BaseRunner.EXECUTION_TIMEOUT
    )

    logger.info(f"Execution timeout: {execution_timeout}")

    try:
        runner = get_runner(language)
        result = runner.execute(
            code=code,
            dependencies=dependencies,
            inputs=inputs,
            env_vars=env_vars,
            execution_timeout=execution_timeout
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
        }

    except ValueError as e:
        raise ValueError(f"ValueError: {str(e)}")
    except Exception as e:
        raise Exception(f"Error running code: {str(e)}")
