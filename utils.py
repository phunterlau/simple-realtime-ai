import json
from datetime import datetime

RUN_TIME_TABLE_LOG_JSON = "runtime_time_table.jsonl"

def log_runtime(function_or_name: str, duration: float):
    jsonl_file = RUN_TIME_TABLE_LOG_JSON
    time_record = {
        "timestamp": datetime.now().isoformat(),
        "function": function_or_name,
        "duration": f"{duration:.4f}",
    }
    with open(jsonl_file, "a") as file:
        json.dump(time_record, file)
        file.write("\n")

    print(f"⏰ {function_or_name}() took {duration:.4f} seconds")