from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.teams.models import District, Patrol, Team, TeamRequest
from apps.users.models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TeamRequestApiTests(APITestCase):
    def setUp(self):
        self.district = District.objects.create(name="Okręg testowy")

    def create_user(self, email, *, email_verified=False, is_superuser=False):
        user = User.objects.create(
            email=email,
            first_name="Jan",
            last_name="Testowy",
            email_verified=email_verified,
            is_staff=is_superuser,
            is_superuser=is_superuser,
        )
        user.set_password("test-password")
        user.save()
        return user

    def request_payload(self):
        return {
            "team_name": "1 Testowa Drużyna",
            "team_short_name": "1 TD",
            "district": str(self.district.id),
            "organization": 0,
            "patrols": ["Kadra", "Pierwszy"],
            "user_patrol": "Kadra",
            "function_level": 4,
        }

    def create_existing_request(self, user, status_value="submitted"):
        team = Team.objects.create(
            name="Istniejąca Drużyna",
            short_name="ID",
            district=self.district,
            organization=0,
        )
        patrol = Patrol.objects.create(name="Kadra", team=team)
        user.patrol = patrol
        user.save(update_fields=["patrol"])
        return TeamRequest.objects.create(
            created_by=user,
            team=team,
            function_level=4,
            status=status_value,
        )

    def test_verified_zhr_request_is_approved_without_admin_request_email(self):
        user = self.create_user("jan@zhr.pl", email_verified=True)
        self.client.force_authenticate(user)

        with patch("apps.teams.api.views.threading.Thread") as thread:
            response = self.client.post(
                "/api/team-requests/", self.request_payload(), format="json"
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "approved")
        self.assertEqual(response.data["approval_outcome"], "auto_approved")
        request_obj = TeamRequest.objects.get(pk=response.data["id"])
        request_obj.team.refresh_from_db()
        user.refresh_from_db()
        self.assertTrue(request_obj.team.is_verified)
        self.assertEqual(user.function, 4)
        thread.assert_not_called()

    def test_unverified_zhr_request_waits_for_email_verification(self):
        user = self.create_user("jan@zhr.pl")
        self.client.force_authenticate(user)

        with patch("apps.teams.api.views.threading.Thread") as thread:
            response = self.client.post(
                "/api/team-requests/", self.request_payload(), format="json"
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending_verification")
        self.assertEqual(response.data["approval_outcome"], "can_auto_approve")
        thread.assert_not_called()

    def test_email_verification_auto_approves_and_informs_admin(self):
        user = self.create_user("jan@zhr.pl")
        team_request = self.create_existing_request(user, "pending_verification")

        response = self.client.post(
            reverse("api_verify_email"),
            {"user_id": str(user.id), "token": str(user.email_verification_token)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team_request.refresh_from_db()
        team_request.team.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(team_request.status, "approved")
        self.assertTrue(team_request.team.is_verified)
        self.assertEqual(user.function, 4)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["eproba@zhr.pl"])
        self.assertIn("Nie wymaga ręcznej weryfikacji", mail.outbox[0].body)

    def test_explicit_approve_action_persists_and_emails_note(self):
        applicant = self.create_user("applicant@example.com", email_verified=True)
        admin = self.create_user("admin@example.com", is_superuser=True)
        team_request = self.create_existing_request(applicant)
        self.client.force_authenticate(admin)

        response = self.client.post(
            f"/api/team-requests/{team_request.id}/approve/",
            {
                "note": "Dane zostały sprawdzone.",
                "send_email": True,
                "send_note": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team_request.refresh_from_db()
        self.assertEqual(team_request.status, "approved")
        self.assertEqual(team_request.notes, "Dane zostały sprawdzone.")
        self.assertEqual(team_request.accepted_by, admin)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Notatka: Dane zostały sprawdzone.", mail.outbox[0].body)

    def test_generic_update_methods_are_not_available(self):
        applicant = self.create_user("applicant@example.com")
        admin = self.create_user("admin@example.com", is_superuser=True)
        team_request = self.create_existing_request(applicant)
        self.client.force_authenticate(admin)

        for method in (self.client.put, self.client.patch):
            response = method(
                f"/api/team-requests/{team_request.id}/",
                {"status": "approved"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_request_verification_requires_email_notification(self):
        applicant = self.create_user("applicant@example.com", email_verified=True)
        admin = self.create_user("admin@example.com", is_superuser=True)
        team_request = self.create_existing_request(applicant)
        self.client.force_authenticate(admin)

        response = self.client.post(
            f"/api/team-requests/{team_request.id}/request-verification/",
            {"send_email": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        team_request.refresh_from_db()
        self.assertEqual(team_request.status, "submitted")
        self.assertEqual(len(mail.outbox), 0)

    def test_user_can_fetch_their_latest_request_outcome(self):
        user = self.create_user("jan@zhr.pl")
        team_request = self.create_existing_request(user, "pending_verification")
        self.client.force_authenticate(user)

        response = self.client.get("/api/team-requests/mine/latest/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(team_request.id))
        self.assertEqual(response.data["approval_outcome"], "can_auto_approve")
