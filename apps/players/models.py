from django.db import models


class Player(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True)
    username = models.CharField(max_length=32)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['username']
        verbose_name = 'player'
        verbose_name_plural = 'players'

    def __str__(self):
        return self.username


class PlayerStats(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='stats')
    play_time_ticks = models.BigIntegerField(default=0)
    pokemons_caught = models.IntegerField(default=0)
    pokedex_registered = models.IntegerField(default=0)
    cobbletcg_cards = models.IntegerField(default=0)
    battles_won = models.IntegerField(default=0)
    cobbledollars = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['player__username']
        verbose_name = 'player stats'
        verbose_name_plural = 'player stats'

    def __str__(self):
        return f'{self.player} stats'
