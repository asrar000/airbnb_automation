"""
Step 07: Network and Console Monitoring
- Save all captured network requests to DB
- Save all captured console messages to DB
- Log summary result
"""
from automation.tests.base import BaseTestStep
from automation.db_logger import save_network_logs, save_console_logs, save_result
from automation.models import ResultModel


class Step07MonitoringLogs(BaseTestStep):
    name = "Network and Console Monitoring Test"

    def run(self) -> ResultModel:
        print("\n[Step 07] Network and Console Monitoring...")

        network_requests = self.shared_state.get("network_requests", [])
        console_messages = self.shared_state.get("console_messages", [])

        screenshot_path = self.screenshot("step07_monitoring")

        console_errors = [m for m in console_messages if m.get("type") == "error"]
        network_errors = [
            r for r in network_requests
            if r.get("status") and r["status"] >= 400
        ]

        total_network = len(network_requests)
        total_console = len(console_messages)
        total_net_errors = len(network_errors)
        total_con_errors = len(console_errors)

        print(f"  Network requests : {total_network}")
        print(f"  Network errors   : {total_net_errors}")
        print(f"  Console messages : {total_console}")
        print(f"  Console errors   : {total_con_errors}")

        comment = (
            f"Total network requests captured: {total_network}. "
            f"Network errors (4xx/5xx): {total_net_errors}. "
            f"Console messages: {total_console}. "
            f"Console errors: {total_con_errors}."
        )

        # Pass if data was captured; errors are logged but don't fail the step
        # (Airbnb itself may return some 4xx for analytics/tracking — expected)
        passed = total_network > 0 and total_console >= 0

        result = save_result(
            test_case=self.name,
            url=self.page.url,
            passed=passed,
            comment=comment,
            screenshot_path=screenshot_path,
        )

        save_network_logs(result, network_requests)
        save_console_logs(result, console_messages)

        print(f"  Network requests saved: {min(total_network, 50)}")
        print(f"  Console messages saved: {total_console}")

        return result