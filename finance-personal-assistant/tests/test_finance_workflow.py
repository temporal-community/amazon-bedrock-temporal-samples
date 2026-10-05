import asyncio
import shutil
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from temporalio import activity
from temporalio.common import VersioningBehavior
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker, WorkerDeploymentConfig, WorkerDeploymentVersion

from temporal.budget_agent_activity import budget_agent_activity
from temporal.financial_analysis_activity import financial_analysis_activity
from temporal.financial_assistant_workflow import FinancialAssistantWorkflow
from temporal.llm_activity import invoke_bedrock_model
from temporal.models import BedrockInvocationRequest, FinancialReport


@activity.defn(name="budget_agent_activity")
def fake_budget(prompt: str) -> FinancialReport:
    return FinancialReport(
        monthly_income=6000,
        budget_categories=[
            {"name": "Dining", "amount": 800, "percentage": 13.3}
        ],
        recommendations=["Build an emergency fund"],
        financial_health_score=7,
        recommended_investment_amount=300,
    )


@activity.defn(name="invoke_bedrock_model")
def fake_format(request: BedrockInvocationRequest) -> str:
    return "formatted analysis" if "analysis" in request.system_prompt else "formatted budget"


@activity.defn(name="financial_analysis_activity")
def fake_analysis(amount: float) -> str:
    return f"Analysis for {amount}"


class FinanceWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_versioned_worker_registers_finance_activities(self):
        temporal_cli = shutil.which("temporal")
        if temporal_cli is None:
            self.skipTest("Temporal CLI is required for the local test server")

        async with await WorkflowEnvironment.start_local(
            dev_server_existing_path=temporal_cli,
            data_converter=pydantic_data_converter,
        ) as env:
            with ThreadPoolExecutor(max_workers=4) as executor:
                async with Worker(
                    env.client,
                    task_queue=f"finance-versioned-test-{uuid.uuid4()}",
                    workflows=[FinancialAssistantWorkflow],
                    activities=[
                        budget_agent_activity,
                        invoke_bedrock_model,
                        financial_analysis_activity,
                    ],
                    activity_executor=executor,
                    deployment_config=WorkerDeploymentConfig(
                        version=WorkerDeploymentVersion(
                            deployment_name="finance-personal-assistant",
                            build_id="test-v1",
                        ),
                        use_worker_versioning=True,
                        default_versioning_behavior=VersioningBehavior.PINNED,
                    ),
                ):
                    await asyncio.sleep(0.1)

    async def test_report_query_and_signal_complete_with_fake_activities(self):
        temporal_cli = shutil.which("temporal")
        if temporal_cli is None:
            self.skipTest("Temporal CLI is required for the local test server")

        async with await WorkflowEnvironment.start_local(
            dev_server_existing_path=temporal_cli,
            data_converter=pydantic_data_converter,
        ) as env:
            task_queue = f"finance-test-{uuid.uuid4()}"
            with ThreadPoolExecutor(max_workers=3) as executor:
                async with Worker(
                    env.client,
                    task_queue=task_queue,
                    workflows=[FinancialAssistantWorkflow],
                    activities=[fake_budget, fake_format, fake_analysis],
                    activity_executor=executor,
                ):
                    handle = await env.client.start_workflow(
                        FinancialAssistantWorkflow.run,
                        "A budget prompt",
                        id=f"finance-test-{uuid.uuid4()}",
                        task_queue=task_queue,
                    )
                    for _ in range(100):
                        recommended = await handle.query(
                            FinancialAssistantWorkflow.get_recommended_investment_amount
                        )
                        if recommended is not None:
                            break
                        await asyncio.sleep(0.02)
                    self.assertEqual(recommended, 300)
                    await handle.signal(FinancialAssistantWorkflow.set_investment_amount, 100)
                    result = await asyncio.wait_for(handle.result(), timeout=10)
                    self.assertEqual(result, "formatted budget\n\nformatted analysis")


if __name__ == "__main__":
    unittest.main()
