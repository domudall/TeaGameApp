from django.http import HttpResponse
from django.template import loader
from rest_framework.views import APIView
from rest_framework.response import Response

from cards.cards import Cards
from datastore.models import Round, Player, DrinkRequirements
from cards.forms.player import PlayerForm


def play_game(request):
    cards = Cards()
    template = loader.get_template('cards/playgame.html')
    players = get_players(request.GET.get('players'))

    player_cards = cards.get_cards_for_players(players)
    loser = cards.get_loser(player_cards)[0]

    save_round(loser)

    return HttpResponse(template.render(
        {"player_cards": player_cards, "loser": loser},
        request, ))


def save_round(loser):
    round = Round()
    round.loser = loser
    round.save()


def get_players(players):
    if players:
        return players.split(",")
    return ["unknown"]


def register_players(request):
    template = loader.get_template('cards/registerplayers.html')

    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            save_drink_and_player(form)

            return HttpResponse(template.render(
                {"form": form, "name": form.cleaned_data['name']},
                request,))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PlayerForm()

    return HttpResponse(template.render(
        {"form": form},
        request,))


def save_player_to_session(request, player):
    """ Save a player name to the session

    The session is used within the request object,
    saving the player here means it can be accessed by other
    views.

    :param request: request
    :param player: String
    :return:
    """
    sessionlist = request.session['players']
    sessionlist.append(player)
    request.session['players'] = sessionlist


def save_drink_and_player(form):
    """ Cleans form data and saves to DB

    :param form: form
    :return:
    """
    name = form.cleaned_data['name']
    drink_type = form.cleaned_data['drink_type']
    milk = form.cleaned_data["milk"]
    sugar = form.cleaned_data['sugar']

    drink = DrinkRequirements()
    drink.drink_type = drink_type
    drink.milk = milk
    drink.sugar = sugar
    drink.save()

    player = Player()
    player.name = name
    player.drink_preference = drink
    player.save()


def player_list(request):
    template = loader.get_template('cards/playerlist.html')
    render_data = {
        "in_game": [],
        "players": [],
    }

    if request.method == "POST":
        # Adds player to session (To register for game)
        # TODO: Work out appropriate way to clear the session
        # Not sure if I should set an expiry, or clear after the
        # game is played.
        remove_player = request.POST["player_name"]
        save_player_to_session(request, remove_player)
        render_data["in_game"] = request.session['players']

    players = Player.objects.all()

    # Could probably refactor all below.
    # Adds all players to the list
    for player in players:
        render_data["players"].append(player.name)

    # Removes players already playing
    for playing in render_data["in_game"]:
        if playing in render_data["in_game"]:
            render_data["players"].remove(playing)

    return HttpResponse(
        template.render(
            render_data, request,))


class GetCards(APIView):

  def get(self, request, format=None):
    """
    Return a hardcoded response.
    """
    c = Cards()
    card, suit, card_idx, suit_idx = c.get_card()
    return Response({
        "card": card,
        "suit": suit,
        "card_idx": card_idx
    })