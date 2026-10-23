"""Coverage regressions: undocumented source repositories and crowded middleware trees."""
import base64
import unittest
from unittest.mock import patch
from arktic_office.preparation.repository import collect, file_role
from arktic_office.coordination.team import plan_cells
from arktic_office.reporting.view import render_html, render_markdown
from arktic_office.reporting.security import CONTROLS


class SelectionTests(unittest.TestCase):
    def collect_fixture(self, readme=False):
        paths = ["composer.json", "composer.lock", "package.json", "server.php", "bootstrap/app.php",
                 "config/database.php", "config/auth.php", "config/session.php", "app/Http/routes.php",
                 "app/Http/Controllers/Controller.php", "app/Http/Controllers/Admin/AdminController.php",
                 "app/User.php", "database/migrations/create_users.php"]
        paths += [f"app/Http/Middleware/Auth{i}.php" for i in range(60)]
        paths += ["app/Providers/AuthServiceProvider.php", "app/Providers/RouteServiceProvider.php", "public/js/controllers/mainCtrl.js"]
        if readme:
            paths.append("readme.md")
        def fetch(endpoint):
            if endpoint == "/repos/acme/app":
                return {"default_branch": "main"}
            if "/branches/" in endpoint:
                return {"commit": {"sha": "a" * 40, "commit": {"tree": {"sha": "t"}}}}
            if "/git/trees/" in endpoint:
                return {"tree": [{"type": "blob", "mode": "100644", "path": p, "size": 22, "sha": str(i)} for i, p in enumerate(paths)]}
            return {"encoding": "base64", "content": base64.b64encode(b"<?php /* fixture */ ?>").decode()}
        with patch.dict("os.environ", {"AUDIT_MAX_FILES": "24", "AUDIT_MAX_TOTAL_BYTES": "120000"}):
            return collect("https://github.com/acme/app", fetch=fetch)

    def test_crowded_middleware_cannot_displace_core_files(self):
        snapshot = self.collect_fixture()
        paths = {x["path"] for x in snapshot["files"]}
        self.assertLessEqual(len(paths), 24)
        self.assertTrue({"composer.json", "composer.lock", "package.json", "config/database.php", "server.php", "app/Http/routes.php", "app/Http/Controllers/Admin/AdminController.php"} <= paths)
        plans = {x["id"]: {f["path"] for f in x["files"]} for x in plan_cells(snapshot)}
        self.assertTrue({"server.php", "config/database.php", "composer.json", "app/Http/routes.php"} <= plans["architecture"])
        self.assertIn("composer.json", plans["inventory"])
        self.assertTrue({"composer.json", "app/Http/routes.php", "app/Http/Controllers/Admin/AdminController.php"} <= plans["security"])
        self.assertTrue(all(plans.values()))
        for paths in plans.values():
            self.assertTrue({"composer.json", "package.json"} <= paths)

    def test_readme_is_only_complementary(self):
        plans = plan_cells(self.collect_fixture(readme=True))
        for cell in plans:
            paths = [f["path"] for f in cell["files"]]
            self.assertNotEqual(paths, ["readme.md"])
            self.assertNotEqual(paths[0], "readme.md")

    def test_inventory_reads_source_without_manifest_or_readme(self):
        snapshot = {"files": [{"path": "server.php", "text": "<?php run();"}, {"path": "app/Http/routes.php", "text": "Route::get('/');"}]}
        self.assertEqual(len(next(c for c in plan_cells(snapshot) if c["id"] == "inventory")["files"]), 2)

    def test_composer_is_not_docker_compose(self):
        self.assertEqual(file_role("composer.json"), "manifest")
        self.assertEqual(file_role("docker-compose.yml"), "deployment")
        self.assertEqual(file_role("app/Providers/RouteServiceProvider.php"), "config")

    def test_security_coverage_visible_even_with_zero_risks(self):
        snapshot = self.collect_fixture()
        controls = [{"id": key, "estado": "no_evaluado", "motivo": "Falta revisar la lógica de negocio.", "evidencia": []} for key in CONTROLS]
        data = {"schema_version": 3, "estado": "parcial", "confirmados": [], "indicios": [], "dudas": [], "controles": controls, "celulas": []}
        for value in (render_html(data, snapshot), render_markdown(data, snapshot)):
            self.assertIn("Evaluación pendiente en:", value)
            self.assertIn("No hay información validada suficiente", value)
            self.assertNotIn("Falta revisar la lógica de negocio.", value)


if __name__ == "__main__":
    unittest.main()
