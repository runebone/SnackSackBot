import logging


def log_exceptions(logger: logging.Logger):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(f"ERROR - {str(e)}")
                if logger is not None:
                    logger.error(f"{str(e)}", exc_info=True)
            else:
                return result

        return wrapper

    return decorator


def async_log_exceptions(logger: logging.Logger):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                print(f"ERROR - {str(e)}")
                if logger is not None:
                    logger.error(f"{str(e)}", exc_info=True)
            else:
                return result

        return wrapper

    return decorator
