from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update(
        {
            "patrol": "profile",
            "patrol_name": "profile",
            "team": "profile",
            "team_name": "profile",
            "rank": "profile",
            "scout_rank": "profile",
            "instructor_rank": "profile",
            "function": "profile",
            "is_active": "profile",
            "is_superuser": "profile",
            "is_staff": "profile",
        }
    )

    def get_additional_claims(self, request):
        user = request.user
        patrol = user.patrol if user.patrol else None
        team = patrol.team if patrol and patrol.team else None

        return {
            # Standard claims
            "email": user.email,
            "email_verified": user.email_verified,
            "nickname": user.nickname,
            "name": user.full_name,
            "given_name": user.first_name,
            "family_name": user.last_name,
            "gender": user.gender_string,
            # Custom claims
            "patrol": patrol.id if patrol else None,
            "patrol_name": patrol.name if patrol else None,
            "team": team.id if team else None,
            "team_name": team.name if team else None,
            "rank": user.full_rank(),
            "scout_rank": user.scout_rank,
            "instructor_rank": user.instructor_rank,
            "function": user.function,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }

    def get_discovery_claims(self, request):
        return [
            "email",
            "email_verified",
            "nickname",
            "name",
            "given_name",
            "family_name",
            "gender",
            "patrol",
            "rank",
            "scout_rank",
            "instructor_rank",
            "function",
            "is_active",
            "is_superuser",
            "is_staff",
        ]
