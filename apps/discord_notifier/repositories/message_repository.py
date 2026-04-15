from apps.discord_notifier.models import DiscordPostedMessage


class DiscordMessageRepository:

    def get_by_ranking(self, ranking_id: str) -> DiscordPostedMessage | None:
        try:
            return DiscordPostedMessage.objects.get(ranking_id=ranking_id)
        except DiscordPostedMessage.DoesNotExist:
            return None

    def update_or_create(self, ranking_id: str, message_id: str) -> DiscordPostedMessage:
        obj, _ = DiscordPostedMessage.objects.update_or_create(
            ranking_id=ranking_id,
            defaults={'message_id': message_id},
        )
        return obj
