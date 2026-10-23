"""Exercise Security -> Developer -> Testing -> Product Owner without services."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main as app
from crew.workflow import ROLES, STEPS, build_tasks, workflow_steps


FEATURE = {
    "title": "Merchant QR payment status",
    "description": "Show a reliable QR payment status for a merchant.",
    "acceptance_criteria": ["The merchant sees a unique payment reference and current status."],
}


class WorkflowTests(unittest.TestCase):
    def test_workflow_has_requested_order(self):
        self.assertEqual(
            [role.KEY for role in ROLES],
            ["security", "developer", "testing", "product_owner"],
        )
        self.assertEqual([step[0] for step in STEPS], [role.KEY for role in ROLES])

    def test_each_role_builds_its_own_task(self):
        tasks = build_tasks(FEATURE)
        self.assertEqual(list(tasks), ["security", "developer", "testing", "product_owner"])
        for role in ROLES:
            self.assertIs(tasks[role.KEY].agent, role.agent)
            self.assertIn(FEATURE["title"], tasks[role.KEY].description)
            self.assertIn(FEATURE["description"], tasks[role.KEY].description)
            for criterion in FEATURE["acceptance_criteria"]:
                self.assertIn(criterion, tasks[role.KEY].description)
            self.assertTrue(Path(role.__file__).is_file())

    def test_each_agent_has_role_specific_instructions_and_output(self):
        tasks = build_tasks(FEATURE)
        required = {
            "security": ("preventiva", "mitigacion", "security_report.md"),
            "developer": ("Quarkus", "Angular", "infraestructura", "developer_spec.md"),
            "testing": ("NO EJECUTADO", "criterio", "testing_report.md"),
            "product_owner": ("docs/", "evidencia", "product_owner_review.md"),
        }
        for key, markers in required.items():
            with self.subTest(role=key):
                task_text = f"{tasks[key].description}\n{tasks[key].expected_output}".lower()
                for marker in markers:
                    self.assertIn(marker.lower(), task_text)
                self.assertNotIn("realiza la tarea de tu rol", task_text)

    def test_docs_context_selects_issue_story_and_documents_mock_limits(self):
        context = app.build_project_docs_context(FEATURE)
        self.assertIn("docs/epic/peru-wallet-mvp.sp.md", context)
        self.assertIn("docs/user-stories/3-merchant-qr-payment-status-visibility.sp.md", context)
        self.assertIn("docs/mockups/W3-Pago-QR-comercio.md", context)
        self.assertIn("Cobertura y límites", context)
        self.assertNotIn("docs/user-stories/1-user-onboarding-mvp-completion.sp.md", context)

    def test_pipeline_saves_all_roles_extracts_infra_and_resumes(self):
        roles = ROLES
        steps = workflow_steps()
        calls = []

        def run(agent, task):
            key = next(role.KEY for role in roles if role.agent is agent)
            calls.append((key, task.description))
            if key == "developer":
                return (
                    "```java\n// BalanceService.java\npackage pe.bcp.login.service;\npublic class BalanceService {}\n```\n"
                    "```typescript\n// balance.service.ts\nexport class BalanceService {}\n```\n"
                    "```yaml\n# compose.yaml\nservices: {}\n```"
                )
            if key == "testing":
                return "Coverage report. NO EJECUTADO.\n```java\n// BalanceTest.java\npackage pe.bcp.login;\npublic class BalanceTest {}\n```"
            if key == "product_owner":
                return "DECISION: LISTO PARA REVISION HUMANA. No model was called."
            return f"Approved output from {key}. No model was called."

        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            output = Path(tmp)
            stack.enter_context(patch.object(app, "OUTPUT_DIR", output))
            stack.enter_context(
                patch.object(app, "CHECKPOINT_FILE", output / ".checkpoint.json")
            )
            stack.enter_context(patch.object(app, "proj_tools", return_value=[]))
            stack.enter_context(
                patch.object(
                    app,
                    "list_projects",
                    return_value=[{"id": "P1", "title": "Team backlog"}],
                )
            )
            stack.enter_context(
                patch.object(
                    app,
                    "list_project_items",
                    return_value=[{"title": FEATURE["title"]}],
                )
            )
            stack.enter_context(
                patch.object(app, "get_feature_from_item", return_value=FEATURE)
            )
            stack.enter_context(patch.object(app, "run_step", side_effect=run))
            stack.enter_context(patch.object(app, "hitl_approve", return_value=("s", "")))
            stack.enter_context(patch("builtins.input", return_value="1"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            app.main()

            expected = ["security", "developer", "testing", "product_owner"]
            self.assertEqual([key for key, _ in calls], expected)
            for key, _, _, spec, _ in steps:
                self.assertTrue((output / "specs" / spec).is_file(), key)
            self.assertTrue(
                (
                    output
                    / "backend-quarkus/src/test/java/pe/bcp/login/BalanceTest.java"
                ).is_file()
            )
            self.assertTrue((output / "compose.yaml").is_file())
            developer_prompt = next(prompt for key, prompt in calls if key == "developer")
            self.assertIn("Approved output from security", developer_prompt)
            product_owner_prompt = calls[-1][1]
            self.assertIn("Coverage report", product_owner_prompt)
            self.assertIn("BalanceService.java", product_owner_prompt)
            checkpoint = json.loads((output / ".checkpoint.json").read_text())
            self.assertEqual(len(checkpoint["steps"]), len(roles))
            self.assertTrue(
                all(
                    step["status"] == "approved"
                    for step in checkpoint["steps"].values()
                )
            )

            app.main()
            self.assertEqual(
                len(calls), len(expected), "Approved steps must not call the model again"
            )
            before = (output / ".checkpoint.json").read_text()
            with patch.object(app, "run_step", side_effect=AssertionError("checkpoint must skip")):
                app.main()
            self.assertEqual((output / ".checkpoint.json").read_text(), before)

    def test_old_checkpoint_is_not_reused(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            output = Path(tmp)
            checkpoint_file = output / ".checkpoint.json"
            legacy = {"workflow_mode": "standard", "feature_title": FEATURE["title"], "steps": {"security": {"status": "approved", "output": "old"}}}
            checkpoint_file.write_text(json.dumps(legacy))
            stack.enter_context(patch.object(app, "OUTPUT_DIR", output))
            stack.enter_context(patch.object(app, "CHECKPOINT_FILE", checkpoint_file))
            stack.enter_context(patch.object(app, "proj_tools", return_value=[]))
            stack.enter_context(patch.object(app, "list_projects", return_value=[{"id": "P1", "title": "Team backlog"}]))
            stack.enter_context(patch.object(app, "list_project_items", return_value=[{"title": FEATURE["title"]}]))
            stack.enter_context(patch.object(app, "get_feature_from_item", return_value=FEATURE))
            stack.enter_context(patch("builtins.input", return_value="1"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            with self.assertRaises(SystemExit) as stopped:
                app.main()
            self.assertEqual(stopped.exception.code, 1)
            self.assertEqual(json.loads(checkpoint_file.read_text()), legacy)


if __name__ == "__main__":
    unittest.main()
