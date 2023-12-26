from typing import Generator


def intervals_gen(
    interval: int = 10,
    retry_interval_min: int = 1,
    retry_interval_max: int = 32,
) -> Generator[int, bool, None]:
    success = True
    retry_interval = retry_interval_min

    while True:
        if success:
            success = yield interval
            retry_interval = retry_interval_min
        else:
            success = yield retry_interval
            retry_interval = min(retry_interval * 2, retry_interval_max)
