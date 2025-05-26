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
        return {
            # Standard claims
            "email": request.user.email,
            "email_verified": request.user.email_verified,
            "nickname": request.user.nickname,
            "name": request.user.full_name,
            "given_name": request.user.first_name,
            "family_name": request.user.last_name,
            "gender": request.user.gender_string,
            # Custom claims
            "patrol": request.user.patrol.id,
            "patrol_name": request.user.patrol.name,
            "team": request.user.patrol.team.id,
            "team_name": request.user.patrol.team.name,
            "rank": request.user.full_rank(),
            "scout_rank": request.user.scout_rank,
            "instructor_rank": request.user.instructor_rank,
            "function": request.user.function,
            "is_active": request.user.is_active,
            "is_superuser": request.user.is_superuser,
            "is_staff": request.user.is_staff,
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
