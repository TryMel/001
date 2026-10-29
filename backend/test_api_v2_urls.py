import json

from django.test import SimpleTestCase
from django.urls import resolve


class RoutesApiV2Tests(SimpleTestCase):
    def test_api_v1_routes_remain_available_alongside_v2(self):
        route_v1 = resolve("/api/comptes/connexion/")
        route_v2 = resolve("/api/v2/comptes/connexion/")

        self.assertIs(route_v1.func.view_class, route_v2.func.view_class)

    def test_versioned_schema_identifies_api_v2(self):
        route = resolve("/api/v2/schema/")
        settings_schema = route.func.view_initkwargs["custom_settings"]

        self.assertEqual(settings_schema["TITLE"], "API Akasha v2")
        self.assertEqual(settings_schema["VERSION"], "2.0.0")
        self.assertIn("api/v2/", settings_schema["DESCRIPTION"])

    def test_versioned_schema_is_served_with_only_v2_paths(self):
        response = self.client.get(
            "/api/v2/schema/",
            HTTP_HOST="localhost",
            HTTP_ACCEPT="application/vnd.oai.openapi+json",
        )

        self.assertEqual(response.status_code, 200)
        schema = json.loads(response.content)
        self.assertEqual(schema["info"]["title"], "API Akasha v2")
        self.assertEqual(schema["info"]["version"], "2.0.0")
        self.assertTrue(schema["paths"])
        self.assertTrue(all(path.startswith("/api/v2/") for path in schema["paths"]))

    def test_organization_listing_and_detail_use_existing_member_scoped_viewset(self):
        route_list = resolve("/api/v2/organisations/")
        route_detail = resolve("/api/v2/organisations/1/")

        self.assertIs(route_list.func.cls, route_detail.func.cls)
        self.assertEqual(route_list.func.cls.__name__, "OrganisationVueSet")
